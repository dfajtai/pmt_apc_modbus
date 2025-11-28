from typing import Optional
import logging
import asyncio
from services.modbus_common import ModbusException
from services.modbus_query import ModbusQuery
from services.async_modbus_connection import AsyncModbusConnection


class AsyncModbusHandler:
    """
    Fully async Modbus handler using ModbusConnection (async version) with
    single worker queue to serialize all requests to avoid race conditions.
    """

    def __init__(self, connection: AsyncModbusConnection,
                 logger: Optional[logging.Logger] = None,
                 test_address: int = 1):

        if not isinstance(connection, AsyncModbusConnection):
            raise TypeError("AsyncModbusHandler requires a AsyncModbusConnection instance.")

        self.connection = connection
        self.logger = logger
        self.test_address = test_address

        self._queue = asyncio.Queue()
        self._worker_task = None

    # -------------------------------------------------------
    # Worker indítása mindig az aktuális event loopon
    # -------------------------------------------------------
    def _ensure_worker(self):
        if self._worker_task and not self._worker_task.done():
            return

        loop = asyncio.get_running_loop()
        self._worker_task = loop.create_task(self._worker())

        if self.logger:
            self.logger.debug("Worker task started")

    # -------------------------------------------------------
    # Worker loop
    # -------------------------------------------------------
    async def _worker(self):
        while True:
            item = await self._queue.get()
            try:
                query, coro_func, future = item
                result = await coro_func(query)
                if not future.done():
                    future.set_result(result)

            except Exception as e:
                if not future.done():
                    future.set_exception(e)

            finally:
                self._queue.task_done()

    # -------------------------------------------------------
    # Enqueue standardized request
    # -------------------------------------------------------
    async def enqueue_request(self, query, coro_func):
        self._ensure_worker()

        future = asyncio.get_running_loop().create_future()

        self.logger.debug("MODBUS query qued.")

        await self._queue.put((query, coro_func, future))

        self.logger.debug("MODBUS query done.")

        return await future

    # -------- helper --------

    async def _get_client(self):
        if not self.connection.is_connected:
            await self.connection.connect()
        return self.connection.client

    async def check_connection(self) -> bool:

        async def _check_impl(_):
            if not self.connection.is_connected:
                return False

            client = await self._get_client()
            if client is None:
                return False

            try:
                await client.read_coils(self.test_address, count=1)
                return True
            except Exception as e:
                if self.logger:
                    self.logger.error(e)
                return False

        return await self.enqueue_request(None, _check_impl)

    # --------------------------------------------------------------------------
    # ASYNC READS
    # --------------------------------------------------------------------------
    async def read_input(self, query: ModbusQuery):
        return await self.enqueue_request(query, self._read_input_impl)

    async def _read_input_impl(self, query: ModbusQuery):
        client = await self._get_client()
        try:
            result = await client.read_input_registers(
                address=query.register,
                count=query.length,
            )
            if result.isError():
                raise ModbusException(f"Error reading input register at {query.register}")
            return query.parse_value_from_registers(result.registers)
        except Exception as e:
            raise ModbusException(f"Failed to read input register {query.register}: {e}") from e

    async def read_holding(self, query: ModbusQuery):
        return await self.enqueue_request(query, self._read_holding_impl)

    async def _read_holding_impl(self, query: ModbusQuery):
        client = await self._get_client()
        try:
            result = await client.read_holding_registers(
                address=query.register,
                count=query.length,
            )
            if result.isError():
                raise ModbusException(f"Error reading holding register at {query.register}")
            return query.parse_value_from_registers(result.registers)
        except Exception as e:
            raise ModbusException(f"Failed to read holding register {query.register}: {e}") from e

    async def read_coil(self, query: ModbusQuery) -> bool:
        return await self.enqueue_request(query, self._read_coil_impl)

    async def _read_coil_impl(self, query: ModbusQuery):
        client = await self._get_client()
        try:
            result = await client.read_coils(query.register, count=1)
            if result.isError():
                raise ModbusException(f"Error reading coil at {query.register}")
            return bool(result.bits[0])
        except Exception as e:
            raise ModbusException(f"Failed to read coil {query.register}: {e}") from e

    # --------------------------------------------------------------------------
    # ASYNC WRITES
    # --------------------------------------------------------------------------
    async def write_register(self, query: ModbusQuery, value: int):
        return await self.enqueue_request(
            (query, value),
            self._write_register_impl
        )

    async def _write_register_impl(self, args):
        query, value = args
        client = await self._get_client()
        try:
            result = await client.write_register(address=query.register, value=value)
            if result.isError():
                raise ModbusException(f"Error writing register at {query.register}")
        except Exception as e:
            raise ModbusException(f"Failed to write register {query.register}: {e}") from e

    async def write_registers(self, query: ModbusQuery, values: list[int]):
        return await self.enqueue_request(
            (query, values),
            self._write_registers_impl
        )

    async def _write_registers_impl(self, args):
        query, values = args
        client = await self._get_client()
        try:
            result = await client.write_registers(address=query.register, values=values)
            if result.isError():
                raise ModbusException(f"Error writing registers at {query.register}")
        except Exception as e:
            raise ModbusException(f"Failed to write registers {query.register}: {e}") from e

    async def write_coil(self, query: ModbusQuery, value: bool):
        return await self.enqueue_request(
            (query, value),
            self._write_coil_impl
        )

    async def _write_coil_impl(self, args):
        query, value = args
        client = await self._get_client()
        try:
            result = await client.write_coil(address=query.register, value=bool(value))
            if result.isError():
                raise ModbusException(f"Error writing coil at {query.register}")
        except Exception as e:
            raise ModbusException(f"Failed to write coil {query.register}: {e}") from e
