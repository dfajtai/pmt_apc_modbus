from enum import Enum

from dataclasses import dataclass


from model.config_model import AppConfig
from services.modbus_connection import ModbusConnection
from services.modbus_handler import ModbusHandler, ModbusQuery




class PmtApcInstrument:
    
    CHANNELS = [
        ModbusQuery("timestamp",30310,2), # seconds
        ModbusQuery("pc1",30312,2), # particle channel 1 (0.3um count @ given second ??)
        ModbusQuery("pc3",30316,2), # particle channel 2 (0.5um count @ given second ??)
        ModbusQuery("pc2",30314,2), # particle channel 3 (5.0um count @ given second ??)
    ]


    class SamplingStatus(Enum):
        NOT_SAMPLING = 0
        SAMPLING = 1
        SELF_CHECK = 2

    class DeviceStatus(Enum):
        NORMAL = 0
        ABNORMAL = 1
        
    def __init__(self, relay: ModbusHandler):
        if not isinstance(relay,ModbusHandler):
            raise ValueError
        self.relay = relay

    
        self.sampling_status = None
        self.device_status = None
        self.flow_rate = None
    
    # read status

    def read_sampling_status(self) -> "PmtApcInstrument.SamplingStatus":
        status_query = ModbusQuery("read_sampling_status",30164,1)
        response = self.relay.read_input(status_query)
        return PmtApcInstrument.SamplingStatus(response)

    def read_device_status(self):
        status_query = ModbusQuery("read_sampling_status",30214,1)
        response = self.relay.read_coil(status_query)
        return PmtApcInstrument.DeviceStatus(response)

    def read_flow(self):
        # SET flow not worked in modbus applications.
        flow_query =  ModbusQuery("read_flow",30022,2,dtype="uint32")
        response = self.relay.read_input(flow_query)
        return response

    # control

    def start_sampling(self):
        control_query = ModbusQuery("control_sampling",2,1,writeable=True)
        self.relay.write_coil(control_query,True)

    def stop_sampling(self):
        control_query = ModbusQuery("control_sampling",2,1,writeable=True)
        self.relay.write_coil(control_query,False)

    # data read

    def read_channels(self, name_list = None):
        pass
        # TODO implement...

