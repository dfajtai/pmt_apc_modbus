from enum import Enum

from typing import Optional
import logging

from dataclasses import dataclass
import asyncio

from ..model.config_model import AppConfig
from ..services.modbus_query import ModbusQuery


from ..services.async_modbus_connection import AsyncModbusConnection
from ..services.async_modbus_handler import AsyncModbusHandler



class PmtApcInstrument:

    CHANNELS = [
        ModbusQuery("pc1",30312,2,dtype="uint32"), # particle channel 1 (0.3um count @ given second ??)
        ModbusQuery("pc2",30314,2,dtype="uint32"), # particle channel 3 (5.0um count @ given second ??)
        ModbusQuery("pc3",30316,2,dtype="uint32"), # particle channel 2 (0.5um count @ given second ??)
    ]


    class SamplingStatus(Enum):
        NOT_SAMPLING = 0
        SAMPLING = 1
        SELF_CHECK = 2

    class DeviceStatus(Enum):
        NORMAL = 0
        ABNORMAL = 1
        
    def __init__(self, relay: AsyncModbusHandler, logger: Optional[logging.Logger] = None):
        if not isinstance(relay,AsyncModbusHandler):
            raise ValueError
        self.relay = relay
    
        self.sampling_status = self.SamplingStatus.NOT_SAMPLING
        self.device_status = self.DeviceStatus.NORMAL

        self.flow_rate = None
        self.logger: Optional[logging.Logger] = logger


    async def async_read_sampling_status(self)-> "PmtApcInstrument.SamplingStatus":
        status_query = ModbusQuery("read_sampling_status",30164,1)
        response = await self.relay.read_input(status_query)
        
        return PmtApcInstrument.SamplingStatus(response)
    

    async def async_read_device_status(self):
        status_query = ModbusQuery("read_sampling_status",30214,1)
        response = await self.relay.read_input(status_query)

        return PmtApcInstrument.DeviceStatus(response)

    async def async_read_flow(self):
        # SET flow not worked in modbus applications.
        flow_query =  ModbusQuery("read_flow",30022,2,dtype="uint32")
        response = await self.relay.read_input(flow_query)

        return response

    # control

    async def async_start_sampling(self)-> bool:
        if self.logger:
            self.logger.debug("Starting sampling over MODBUS ....")
            self.logger.debug(f"relay type: {type(self.relay)}, relay is None: {self.relay is None}")

        control_query = ModbusQuery("control_sampling",2,1,writeable=True)
        
        if self.logger:
            self.logger.debug(f"About to call write_coil with query: {control_query}")
        
        try:
            res = await self.relay.write_coil(control_query,1)
            if self.logger:
                self.logger.debug(f"write_coil returned: {res}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Exception in write_coil: {e}")
                self.logger.exception(e)
            return False

        if self.logger:
            self.logger.debug("Sampling status over MODBUS modified")

        if res:
            self.sampling_status = self.SamplingStatus.SAMPLING
            return True
        
        self.sampling_status = self.SamplingStatus.NOT_SAMPLING
        return False
    

    async def async_stop_sampling(self) -> bool:
        control_query = ModbusQuery("control_sampling",2,1,writeable=True)
        res = await self.relay.write_coil(control_query,False)
        if res:
            self.sampling_status = self.SamplingStatus.NOT_SAMPLING
            return True
        return False

    # read data

    async def async_read_channels(self, name_list = None):
        channels_to_read = [ModbusQuery("timestamp",30310,2,dtype="uint32")]
        if isinstance(name_list,list):
            channels_to_read += [c for c in PmtApcInstrument.CHANNELS if c.channel_name in name_list]
        else:
            channels_to_read += PmtApcInstrument.CHANNELS[:]
        
        channel_names =[c.channel_name for c in channels_to_read]

        values = await asyncio.gather(*[asyncio.create_task(self.relay.read_input(c)) for c in channels_to_read])
     
        result = dict(zip(channel_names,values))
        return result