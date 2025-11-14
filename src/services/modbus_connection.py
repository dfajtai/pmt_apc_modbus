from typing import Optional
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException
from model.config_model import AppConfig


class ModbusConnection:
    """Opens and manages a Modbus TCP connection based on AppConfig."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.client: Optional[ModbusTcpClient] = None

    def connect(self) -> bool:
        """Establish Modbus TCP connection."""
        if self.client and self.client.connected:
            return True

        self.client = ModbusTcpClient(str(self.config.ip), port=self.config.port, timeout=3.0)
        if not self.client.connect():
            raise ConnectionException(f"Failed to connect to {self.config.ip}:{self.config.port}")
        return True

    def close(self):
        """Close the connection if open."""
        if self.client:
            self.client.close()
            self.client = None

    @property
    def is_connected(self) -> bool:
        return bool(self.client and self.client.connected)