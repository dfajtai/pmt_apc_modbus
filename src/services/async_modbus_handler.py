from services.modbus_common import ModbusException
from services.modbus_query import ModbusQuery
from services.async_modbus_connection import AsyncModbusConnection


class AsyncModbusHandler:
    """
    Fully async Modbus handler using ModbusConnection (async version).
    """

    def __init__(self, connection: AsyncModbusConnection):
        if not isinstance(connection, AsyncModbusConnection):
            raise TypeError("AsyncModbusHandler requires a AsyncModbusConnection instance.")
        self.connection = connection

    # -------- helper --------

    async def _get_client(self):
        if not self.connection.is_connected:
            await self.connection.connect()
        return self.connection.client

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
                raise ModbusException(
                    f"Error writing coil at {query.register}"
                )

        except Exception as e:
            raise ModbusException(
                f"Failed to write coil {query.register}: {e}"
            ) from e