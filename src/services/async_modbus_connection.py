from typing import Optional
import asyncio
import logging
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ConnectionException
from model.config_model import AppConfig


class AsyncModbusConnection:
    """
    Lightweight async Modbus TCP connection handler.
    Handles:
    - async connect()
    - automatic reconnect
    - safe state tracking
    - graceful close()
    """

    def __init__(self, config: AppConfig, logger: Optional[logging.Logger] = None):
        self.config = config
        self.client: Optional[AsyncModbusTcpClient] = None

        self.logger: Optional[logging.Logger] = logger

        # internal lock to block paralel calls
        self._connect_lock = asyncio.Lock()

        # flag for closing
        self._closing = False

    # --------------------------------------------------------------
    # PROPERTY
    # --------------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        """
        Safe connection state check.
        """
        return (
            self.client is not None
            and self.client.connected
            and not self._closing
        )

    # --------------------------------------------------------------
    # CONNECT
    # --------------------------------------------------------------

    async def connect(self, retry: int = 3, delay: float = 1.0) -> bool:
        """
        Async connect with retry logic.

        retry:   max reconnect attempts
        delay:   seconds between attempts
        """

        async with self._connect_lock:
            if self.is_connected:  # already connected
                return True

            # if there is a client already, lets close it
            if self.client:
                try:
                    await self.client.close()
                except Exception:
                    pass

            # create a nev client
            self.client = AsyncModbusTcpClient(
                str(self.config.ip),
                port=self.config.port,
                timeout=self.config.timeout,
            )

            # retry loop
            for attempt in range(1, retry + 1):
                try:
                    ok = await self.client.connect()
                    if ok:
                        if self.logger:
                            self.logger.info("MODBUS connection successfull.")
                        return True
                    else:
                        raise ConnectionException("Connect returned False")

                except Exception as e:
                    if attempt == retry:
                        raise ConnectionException(
                            f"Failed to connect to {self.config.ip}:{self.config.port} "
                            f"after {retry} attempts. Last error: {e}"
                        ) from e

                    await asyncio.sleep(delay)

        return False  # should not be reached

    # --------------------------------------------------------------
    # RECONNECT (when the handler notices dropped connection)
    # --------------------------------------------------------------

    async def ensure_connected(self):
        """
        Ensures the connection is alive.
        If disconnected → reconnect automatically.
        """
        if not self.is_connected:
            await self.connect()

    # --------------------------------------------------------------
    # CLOSE
    # --------------------------------------------------------------

    async def close(self):
        """Gracefully close the Modbus TCP connection."""
        self._closing = True

        if self.client:
            try:
                await self.client.close()
            except Exception:
                pass
            finally:
                self.client = None

        self._closing = False
