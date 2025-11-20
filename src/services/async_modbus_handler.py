from typing import Optional
import logging

from services.modbus_common import ModbusException
from services.modbus_query import ModbusQuery
from services.async_modbus_connection import AsyncModbusConnection


class AsyncModbusHandler:
    """
    Fully async Modbus handler using ModbusConnection (async version).
    """

    def __init__(self, connection: AsyncModbusConnection,
                 logger:logging.Logger = None,
                 test_address: int = 1):
        if not isinstance(connection, AsyncModbusConnection):
            raise TypeError("AsyncModbusHandler requires a AsyncModbusConnection instance.")
        self.connection = connection

        self.logger: Optional[logging.Logger] = logger
        self.test_address = test_address

    # -------- helper --------

    async def _get_client(self):
        if not self.connection.is_connected:
            await self.connection.connect()
        return self.connection.client

    async def check_connection(self) -> bool:
        """
        Public connection test that does NOT trigger reconnect logic.
        Returns True only if:

        - TCP connection is open
        - Modbus server responds to a minimal request

        Does NOT use _get_client()
        Does NOT reconnect
        """

        # 1) internal connection state check
        if not self.connection.is_connected:
            return False

        client = self.connection.client
        if client is None:
            return False

        try:
            rr = await client.read_coils(self.test_address)
            return True
        
        except Exception:
            return False

    # --------------------------------------------------------------------------
    # ASYNC READS
    # --------------------------------------------------------------------------

    async def read_input(self, query: ModbusQuery):
        client = await self._get_client()

        try:
            result = await client.read_input_registers(
                address=query.register,
                count=query.length,
            )

            if result.isError():
                if self.logger:
                    self.logger.error(f"Error reading input register at {query.register}")
                raise ModbusException(
                    f"Error reading input register at {query.register}"
                )

            return query.parse_value_from_registers(result.registers)

        except Exception as e:
            raise ModbusException(
                f"Failed to read input register {query.register}: {e}"
            ) from e

    async def read_holding(self, query: ModbusQuery):
        client = await self._get_client()

        try:
            result = await client.read_holding_registers(
                address=query.register,
                count=query.length,
            )

            if result.isError():
                if self.logger:
                    self.logger.error(f"Error reading holding register at {query.register}")
                raise ModbusException(
                    f"Error reading holding register at {query.register}"
                )

            return query.parse_value_from_registers(result.registers)

        except Exception as e:
            raise ModbusException(
                f"Failed to read holding register {query.register}: {e}"
            ) from e

    async def read_coil(self, query: ModbusQuery) -> bool:
        client = await self._get_client()

        try:
            result = await client.read_coils(query.register, count=1)

            if result.isError():
                if self.logger:
                    self.logger.error(f"Error reading coil at {query.register}")
                raise ModbusException(
                    f"Error reading coil at {query.register}"
                )

            return bool(result.bits[0])

        except Exception as e:
            raise ModbusException(
                f"Failed to read coil {query.register}: {e}"
            ) from e

    # --------------------------------------------------------------------------
    # ASYNC WRITES
    # --------------------------------------------------------------------------

    async def write_register(self, query: ModbusQuery, value: int):
        client = await self._get_client()

        try:
            result = await client.write_register(
                address=query.register,
                value=value,
            )

            if result.isError():
                if self.logger:
                    self.logger.error(f"Error writing register at {query.register}")
                raise ModbusException(
                    f"Error writing register at {query.register}"
                )

        except Exception as e:
            raise ModbusException(
                f"Failed to write register {query.register}: {e}"
            ) from e

    async def write_registers(self, query: ModbusQuery, values: list[int]):
        client = await self._get_client()

        try:
            result = await client.write_registers(
                address=query.register,
                values=values,
            )

            if result.isError():
                if self.logger:
                    self.logger.error(f"Error writing registers at {query.register}")
                raise ModbusException(
                    f"Error writing registers at {query.register}"
                )

        except Exception as e:
            raise ModbusException(
                f"Failed to write registers {query.register}: {e}"
            ) from e

    async def write_coil(self, query: ModbusQuery, value: bool):
        client = await self._get_client()

        try:
            result = await client.write_coil(
                address=query.register,
                value=bool(value),
            )

            if result.isError():
                if self.logger:
                    self.logger.error(f"Error writing coil at {query.register}")
                raise ModbusException(
                    f"Error writing coil at {query.register}"
                )

        except Exception as e:
            raise ModbusException(
                f"Failed to write coil {query.register}: {e}"
            ) from e