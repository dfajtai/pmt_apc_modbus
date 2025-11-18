
from services.modbus_connection import ModbusConnection
from services.modbus_query import ModbusQuery
from services.modbus_common import ModbusException


class ModbusHandler:
    """
    Magas szintű Modbus adat hozzáférési réteg ModbusConnection felett.
    Input/output regiszterek és coil-ok olvasása/írása, immár ModbusQuery objektummal.
    """

    def __init__(self, connection):
        if not isinstance(connection, ModbusConnection):
            raise TypeError("ModbusHandler requires a ModbusConnection instance.")
        self.connection = connection

    def read_input(self, query: ModbusQuery,):
        client = self._get_client()
        try:
            result = client.read_input_registers(address=query.register, count=query.length)
            if result.isError():
                raise ModbusException(f"Error reading input register at {query.register}")
            value = query.parse_value_from_registers(result.registers,)
            return value
        except Exception as e:
            raise ModbusException(f"Failed to read input register {query.register}: {e}") from e

    def read_holding(self, query: ModbusQuery):
        client = self._get_client()
        try:
            result = client.read_holding_registers(address=query.register, count=query.length)
            if result.isError():
                raise ModbusException(f"Error reading holding register at {query.register}")
            value = query.parse_value_from_registers(result.registers)
            return value
        except Exception as e:
            raise ModbusException(f"Failed to read holding register {query.register}: {e}") from e

    def write_register(self, query: ModbusQuery, value: int):
        client = self._get_client()
        try:
            result = client.write_register(address=query.register, value=value)
            if result.isError():
                raise ModbusException(f"Error writing register at {query.register}")
        except Exception as e:
            raise ModbusException(f"Failed to write register {query.register}: {e}") from e

    def write_registers(self, query: ModbusQuery, values: list[int]):
        client = self._get_client()
        try:
            result = client.write_registers(address=query.register, values=values)
            if result.isError():
                raise ModbusException(f"Error writing registers at {query.register}")
        except Exception as e:
            raise ModbusException(f"Failed to write registers {query.register}: {e}") from e

    def read_coil(self, query: ModbusQuery) -> bool:
        client = self._get_client()
        try:
            result = client.read_coils(query.register, count=1)
            if result.isError():
                raise ModbusException(f"Error reading coil at {query.register}")
            return bool(result.bits[0])
        except Exception as e:
            raise ModbusException(f"Failed to read coil {query.register}: {e}") from e

    def write_coil(self, query: ModbusQuery, value: bool):
        client = self._get_client()
        try:
            result = client.write_coil(address=query.register, value=bool(value))
            if result.isError():
                raise ModbusException(f"Error writing coil at {query.register}")
        except Exception as e:
            raise ModbusException(f"Failed to write coil {query.register}: {e}") from e

    def _get_client(self):
        if not self.connection.is_connected:
            self.connection.connect()
        return self.connection.client