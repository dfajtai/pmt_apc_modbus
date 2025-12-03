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

        # self._lock = asyncio.Lock()
        # Store the loop and defer queue creation to start()
        self._loop = loop
        self._queue: Optional[asyncio.Queue[Optional[QueueItem]]] = None
        self._worker_task: Optional[asyncio.Task] = None

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    async def start(self) -> None:
        """
        Start the worker task and establish the Modbus connection.

        This method **must** be called before submitting any Modbus requests.
        """
        current_loop = asyncio.get_running_loop()
        self.logger.debug(f"[start] Current event loop: {id(current_loop)}")
        
        # If worker task exists and is from a different loop, stop it
        if self._worker_task is not None and not self._worker_task.done():
            # Check if we need to recreate the worker for the new loop
            try:
                task_loop = self._worker_task.get_loop()
                if task_loop != current_loop:
                    self.logger.info(f"[start] Worker task is from different event loop, recreating...")
                    # Cancel the old worker
                    self._worker_task.cancel()
                    await asyncio.sleep(0)  # Allow cancellation to propagate
                    self._queue = None  # Force queue recreation
                else:
                    self.logger.debug("Worker task already running in current loop")
                    return
            except Exception as e:
                self.logger.debug(f"[start] Could not get task loop: {e}, recreating...")
                self._queue = None
                self._worker_task = None

        self.logger.debug(f"[start] Initializing AsyncModbusHandler in event loop {id(current_loop)}")
        
        # Initialize the queue in the current event loop if not already done
        if self._queue is None:
            self.logger.debug(f"[start] Creating new queue in current event loop")
            self._queue = asyncio.Queue()
            self.logger.debug(f"[start] Created queue id={id(self._queue)}")
        else:
            self.logger.debug(f"[start] Queue already exists")

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
            If the worker is not running or queue is not initialized.
        """

        if self._worker_task is None:
            raise RuntimeError(
                "Worker is not running. Call start() before submitting jobs."
            )

        if self._queue is None:
            raise RuntimeError(
                "Queue is not initialized. Call start() before submitting jobs."
            )

        self.logger.debug(f"[_submit_job] Submitting job: {coro_func.__name__}")

        # Always create Future on the currently running loop to avoid
        # attaching a Future created on one loop to a Task running on
        # another loop (which raises RuntimeError).
        try:
            future = asyncio.get_running_loop().create_future()
            self.logger.debug(f"[_submit_job] Created future using current running loop")
        except Exception as e:
            self.logger.error(f"[_submit_job] ERROR creating future: {e}")
            raise

        self.logger.debug(f"[_submit_job] About to put job in queue: {coro_func.__name__} (queue id={id(self._queue)})")
        try:
            await self._queue.put((coro_func, args, future))
            self.logger.debug(f"[_submit_job] Job successfully put in queue: {coro_func.__name__}")
            try:
                qsize = self._queue.qsize()
            except Exception:
                qsize = None
            self.logger.debug(f"[_submit_job] Queue size after put: {qsize}")
            try:
                tasks = list(asyncio.all_tasks())
                self.logger.debug(f"[_submit_job] all_tasks count={len(tasks)}")
                self.logger.debug(f"[_submit_job] worker_task id={id(self._worker_task)} present={any(id(t)==id(self._worker_task) for t in tasks)}")
            except Exception:
                pass
        except Exception as e:
            self.logger.error(f"[_submit_job] ERROR putting job in queue: {e}")
            self.logger.exception(e)
            raise
        self.logger.debug(f"[_submit_job] Job queued, now waiting for future: {coro_func.__name__}")
        result = await future
        self.logger.debug(f"[_submit_job] Future resolved for: {coro_func.__name__}, result: {result}")
        return result

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
            self.logger.debug("MODBUS Worker waiting job...")
            try:
                # Use a longer timeout to avoid missing jobs
                    item = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                    try:
                        item_repr = f"{type(item)}"
                        if isinstance(item, tuple) and len(item) >= 1:
                            func = item[0]
                            item_repr = getattr(func, "__name__", repr(func))
                    except Exception:
                        item_repr = str(type(item))
                    self.logger.debug(f"[worker] got item from queue id={id(self._queue)} -> {item_repr}")
            except asyncio.TimeoutError:
                # nincs új job, csak folytatjuk a loop-ot
                self.logger.debug("MODBUS Worker queue timeout, continuing...")
                continue

            if item is None:
                self._queue.task_done()
                break

            coro_func, args, future = item

            try:
                # Timeout és hiba kezelése minden job-ra
                self.logger.debug(f"MODBUS Worker processing job: {coro_func.__name__}")

                result = await asyncio.wait_for(coro_func(*args), timeout=5.0)
                if not future.done():
                    future.set_result(result)
                self.logger.debug(f"MODBUS Worker processed job: {coro_func.__name__}")
            except asyncio.TimeoutError:
                self.logger.warning(f"MODBUS Worker job timeout: {coro_func.__name__}")
                if not future.done():
                    future.set_exception(asyncio.TimeoutError())
            except Exception as exc:
                self.logger.error(f"MODBUS Worker job exception: {coro_func.__name__} -> {exc}")
                if not future.done():
                    future.set_exception(exc)
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
                result = await client.read_input_registers(self.test_address, count=1)
                return not result.isError()
            except Exception:
                return False
            
        # async with self._lock:
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
        # async with self._lock:
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
        # async with self._lock:
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
        # async with self._lock:
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
    ) -> bool:
        """
        Write a single Modbus register.

        Parameters
        ----------
        value : int
            The integer value to store in the register.
        """
        # async with self._lock:
        return await self._submit_job(
            self._write_register_impl, query, value
        )

    async def _write_register_impl(
        self,
        query: ModbusQuery,
        value: int
    ) -> bool:
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
            return False
        return True

    async def write_registers(
        self,
        query: ModbusQuery,
        values: List[int]
    ) -> bool:
        """
        Write multiple registers in one Modbus command.
        """
        # async with self._lock:
        return await self._submit_job(
            self._write_registers_impl, query, values
        )

    async def _write_registers_impl(
        self,
        query: ModbusQuery,
        values: List[int]
    ) -> bool:
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
            return False
        return True

    async def write_coil(
        self,
        query: ModbusQuery,
        value: bool
    ) -> bool:
        """
        Write a single coil.

        Parameters
        ----------
        value : bool
            True or False to set the coil.
        """
        # async with self._lock:
        return await self._submit_job(
            self._write_coil_impl, query, value
        )

    async def _write_coil_impl(
        self,
        query: ModbusQuery,
        value: bool
    ) -> bool:
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
            return False
        return True