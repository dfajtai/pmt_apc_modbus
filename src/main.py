import time

from logic.config_handler import AppConfigHandler
from logic.apc_instrument import PmtApcInstrument
from services.modbus_handler import ModbusConnection, ModbusHandler

if __name__ == "__main__": 
    config_handler = AppConfigHandler("../config.json")
    config = config_handler.initialize_defaults()

    connection = ModbusConnection(config=config)
    handler = ModbusHandler(connection=connection)

    instrument = PmtApcInstrument(relay = handler)
    i = 0
    instrument.start_sampling()
    while(True):
        print(instrument.read_sampling_status())
        print(instrument.read_flow())
        time.sleep(1)
        i+=1
        if i>=5:
            break
    
    instrument.stop_sampling()
    instrument.read_sampling_status()