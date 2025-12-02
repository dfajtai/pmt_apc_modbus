from typing import Optional, Any, Callable, Coroutine, Tuple, List
import asyncio
import logging

from services.modbus_common import ModbusException
from services.modbus_query import ModbusQuery
from services.async_modbus_connection import AsyncModbusConnection


QueueItem = Tuple[
    Callable[..., Coroutine[Any, Any, Any]],
    Tuple[Any, ...],
    asyncio.Future
]


class AsyncModbusHandler:
    """
    Asynchronous Modbus handler with serialized request execution.

    This class provides a robust pattern for executing Modbus operations
    in an asynchronous environment. Because Modbus clients are generally
    *not thread-safe*, all operations are funneled through a single worker
    task that processes requests sequentially.

    Features:
    ---------
    - Ensures all Modbus reads/writes are serialized.
    - Prevents race conditions within the Modbus TCP client.
    - Provides async API methods for reading/writing coils and registers.
    - Auto-reconnect support via `_get_client()`.
    - Graceful startup/shutdown handling.

    Typical Usage:
    --------------
    >>> handler = AsyncModbusHandler(conn, logger)
    >>> await handler.start()
    >>> value = await handler.read_holding(query)
    >>> await handler.stop()
    """

    def __init__(
        self,
        connection: AsyncModbusConnection,
        logger: Optional[logging.Logger] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        test_address: int = 1
    ) -> None:
        """
        Initialize the Modbus handler.

        Parameters
        ----------
        connection:
            An initialized AsyncModbusConnection instance.
        logger:
            Optional logger instance. If none is provided, a default logger
            for this module will be used.
        test_address:
            Coil/register address used for connection health checks.
        """
        if not isinstance(connection, AsyncModbusConnection):
            raise TypeError(
                "AsyncModbusHandler requires an AsyncModbusConnection instance."
            )

        self.connection = connection
        self.logger = logger or logging.getLogger(__name__)
        self.test_address = test_address

        self._lock = asyncio.Lock()
        self._queue: asyncio.Queue[Optional[QueueItem]] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None

        # --- THREAD-SAFE EVENT LOOP ---
        self._loop = loop

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    async def start(self) -> None:
        """
        Start the worker task and establish the Modbus connection.

        This method **must** be called before submitting any Modbus requests.
        """
        if self._worker_task is not None:
            return

        await self.connection.connect()
        self._worker_task = asyncio.create_task(self._worker())
        self.logger.info("AsyncModbusHandler started.")

    async def stop(self) -> None:
        """
        Gracefully stop the worker and close the Modbus connection.

        Ensures that:
        - all tasks currently in the queue are processed
        - the worker receives a shutdown signal
        - the Modbus connection is properly closed
        """
        self.logger.info("Stopping AsyncModbusHandler...")

        if self._worker_task is None:
            return

        # Send sentinel for shutdown
        await self._queue.put(None)

        # Wait until current jobs complete
        await self._queue.join()

        # Wait for the worker to exit
        if self._worker_task:
            await self._worker_task
            self._worker_task = None
            
        # Close the underlying connection
        await self.connection.close()
        self.logger.info("AsyncModbusHandler stopped.")

    # ------------------------------------------------------------------ #
    # Task submission
    # ------------------------------------------------------------------ #
    async def _submit_job(
        self,
        coro_func: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any
    ) -> Any:
        """
        Submit a coroutine to be executed by the worker.

        Parameters
        ----------
        coro_func:
            Coroutine function to execute (not awaited here).
        args:
            Arguments passed to the coroutine.

        Returns
        -------
        Any
            Result of the coroutine once executed by the worker.

        Raises
        ------
        RuntimeError
            If the worker is not running.
        """
        if self._worker_task is None:
            raise RuntimeError(
                "Worker is not running. Call start() before submitting jobs."
            )

        # future: asyncio.Future = asyncio.Future()

        if self._loop is not None:
            future = self._loop.create_future()
        else:
            future = asyncio.get_running_loop().create_future()

        await self._queue.put((coro_func, args, future))
        return await future

    # ------------------------------------------------------------------ #
    # Worker thread
    # ------------------------------------------------------------------ #
    async def _worker(self) -> None:
        """
        Internal worker loop that processes queued Modbus requests.

        This method:
        - Retrieves jobs (function, args, future) from the queue
        - Executes the function with the given arguments
        - Stores the result or exception in the provided Future
        - Handles shutdown upon receiving a None sentinel
        """
        self.logger.debug("MODBUS Worker task started.")

        while True:
            item = await self._queue.get()

            if item is None:
                self._queue.task_done()
                break

            coro_func, args, future = item

            try:
                result = await coro_func(*args)
                if not future.done():
                    future.set_result(result)
            except Exception as exc:
                if not future.done():
                    future.set_exception(exc)
                self.logger.error(f"Error in Modbus worker: {exc}")
            finally:
                self._queue.task_done()

        self.logger.debug("MODBUS Worker task finished.")

    # ------------------------------------------------------------------ #
    # Helper
    # ------------------------------------------------------------------ #
    async def _get_client(self):
        """
        Safely return the underlying Modbus client, reconnecting if required.

        Returns
        -------
        Any
            The active Modbus client instance, or None if reconnection failed.
        """
        async with self._lock:
            if not self.connection.is_connected:
                try:
                    await self.connection.connect()
                    self.logger.debug("Reconnected to Modbus server.")
                except Exception as exc:
                    self.logger.error(
                        f"Failed to reconnect Modbus client: {exc}"
                    )
            return self.connection.client

    # ------------------------------------------------------------------ #
    # Connection check
    # ------------------------------------------------------------------ #
    async def check_connection(self) -> bool:
        """
        Perform a lightweight connection health check.

        Returns
        -------
        bool
            True if the test coil can be read without error, else False.
        """
        async def _check_impl():
            client = await self._get_client()
            if client is None:
                return False
            try:
                result = await client.read_coils(self.test_address, count=1)
                return not result.isError()
            except Exception:
                return False

        return await self._submit_job(_check_impl)

    # ------------------------------------------------------------------ #
    # READ OPERATIONS
    # ------------------------------------------------------------------ #
    async def read_input(self, query: ModbusQuery) -> Any:
        """
        Read Modbus input registers.

        Parameters
        ----------
        query : ModbusQuery
            Contains register address, length, parsing rules, etc.

        Returns
        -------
        Any
            Parsed value from the returned register block.
        """
        return await self._submit_job(self._read_input_impl, query)

    async def _read_input_impl(self, query: ModbusQuery) -> Any:
        """
        Worker implementation for reading input registers.

        Raises
        ------
        ModbusException
            If client unavailable or read operation fails.
        """
        client = await self._get_client()
        if client is None:
            raise ModbusException(
                f"Failed to get client for read_input {query.register}"
            )

        result = await client.read_input_registers(
            address=query.register,
            count=query.length
        )
        if result.isError():
            raise ModbusException(
                f"Error reading input registers at {query.register}: {result}"
            )

        return query.parse_value_from_registers(result.registers)

    async def read_holding(self, query: ModbusQuery) -> Any:
        """
        Read Modbus holding registers.
        """
        return await self._submit_job(self._read_holding_impl, query)

    async def _read_holding_impl(self, query: ModbusQuery) -> Any:
        """
        Worker implementation for reading holding registers.
        """
        client = await self._get_client()
        if client is None:
            raise ModbusException(
                f"Failed to get client for read_holding {query.register}"
            )

        result = await client.read_holding_registers(
            address=query.register,
            count=query.length
        )
        if result.isError():
            raise ModbusException(
                f"Error reading holding registers at {query.register}: {result}"
            )

        return query.parse_value_from_registers(result.registers)

    async def read_coil(self, query: ModbusQuery) -> bool:
        """
        Read a single coil (boolean).

        Returns
        -------
        bool
            The coil state (True/False).
        """
        return await self._submit_job(self._read_coil_impl, query)

    async def _read_coil_impl(self, query: ModbusQuery) -> bool:
        """
        Worker implementation for reading a coil.
        """
        client = await self._get_client()
        if client is None:
            raise ModbusException(
                f"Failed to get client for read_coil {query.register}"
            )

        result = await client.read_coils(query.register, count=1)
        if result.isError():
            raise ModbusException(
                f"Error reading coil at {query.register}: {result}"
            )

        if not result.bits:
            raise ModbusException(
                f"No coil bits returned at {query.register}"
            )

        return bool(result.bits[0])

    # ------------------------------------------------------------------ #
    # WRITE OPERATIONS
    # ------------------------------------------------------------------ #
    async def write_register(
        self,
        query: ModbusQuery,
        value: int
    ) -> None:
        """
        Write a single Modbus register.

        Parameters
        ----------
        value : int
            The integer value to store in the register.
        """
        return await self._submit_job(
            self._write_register_impl, query, value
        )

    async def _write_register_impl(
        self,
        query: ModbusQuery,
        value: int
    ) -> None:
        """Worker implementation for writing a register."""
        client = await self._get_client()
        if client is None:
            raise ModbusException(
                f"Failed to get client for write_register {query.register}"
            )

        result = await client.write_register(
            address=query.register,
            value=value
        )
        if result.isError():
            raise ModbusException(
                f"Error writing register at {query.register}: {result}"
            )

    async def write_registers(
        self,
        query: ModbusQuery,
        values: List[int]
    ) -> None:
        """
        Write multiple registers in one Modbus command.
        """
        return await self._submit_job(
            self._write_registers_impl, query, values
        )

    async def _write_registers_impl(
        self,
        query: ModbusQuery,
        values: List[int]
    ) -> None:
        """Worker implementation for writing multiple registers."""
        client = await self._get_client()
        if client is None:
            raise ModbusException(
                f"Failed to get client for write_registers {query.register}"
            )

        result = await client.write_registers(
            address=query.register,
            values=values
        )
        if result.isError():
            raise ModbusException(
                f"Error writing registers at {query.register}: {result}"
            )

    async def write_coil(
        self,
        query: ModbusQuery,
        value: bool
    ) -> None:
        """
        Write a single coil.

        Parameters
        ----------
        value : bool
            True or False to set the coil.
        """
        return await self._submit_job(
            self._write_coil_impl, query, value
        )

    async def _write_coil_impl(
        self,
        query: ModbusQuery,
        value: bool
    ) -> None:
        """Worker implementation for writing a coil."""
        client = await self._get_client()
        if client is None:
            raise ModbusException(
                f"Failed to get client for write_coil {query.register}"
            )

        result = await client.write_coil(
            address=query.register,
            value=bool(value)
        )
        if result.isError():
            raise ModbusException(
                f"Error writing coil at {query.register}: {result}"
            )
