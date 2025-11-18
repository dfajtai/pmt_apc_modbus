from dataclasses import dataclass
from pymodbus.client.base import ModbusBaseClient


modbus_dtypes = {
    "uint16" : ModbusBaseClient.DATATYPE.UINT16,
    "uint32" : ModbusBaseClient.DATATYPE.UINT32,

    "int16" : ModbusBaseClient.DATATYPE.INT16,
    "int32" : ModbusBaseClient.DATATYPE.INT32,
    
    "float32": ModbusBaseClient.DATATYPE.FLOAT32,

    "str" : ModbusBaseClient.DATATYPE.STRING
}

@dataclass
class ModbusQuery:
    channel_name: str
    register: int                  # Regiszter címe
    length: int = 1                # Regiszterek száma
    dtype: str = "uint16"
    writeable: bool = False
    zero_indexed: bool = True
    word_little_endian: bool = False
    calibration_b: float = 0.0
    calibration_k: float = 1.0
    has_calibration: float | None = None

    def __post_init__(self):
        self.has_calibration = (self.calibration_b != 0) or (self.calibration_k != 1)
        self.word_order = "big" if not self.word_little_endian else "little"

        assert self.dtype in modbus_dtypes.keys()
        self.modbus_dtype = modbus_dtypes.get(self.dtype)

    def parse_value_from_registers(self, registers):      
        result = ModbusBaseClient.convert_from_registers(registers=registers,data_type=self.modbus_dtype, word_order=self.word_order)

        return self.convert_value(result)

    def convert_value(self, value):
        if self.has_calibration:
            return (self.calibration_k * value) + self.calibration_b
        return value