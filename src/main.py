import time
import asyncio
import sys

from logic.config_handler import AppConfig, AppConfigHandler

from services.modbus_handler import ModbusConnection, ModbusHandler
from services.async_modbus_handler import AsyncModbusConnection, AsyncModbusHandler
from services.async_db_handler import AsyncDBHandler

from logic.apc_sample import APCSample
from logic.apc_instrument import PmtApcInstrument



def sync_test():
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


async def async_init(config:AppConfig):
    connection = AsyncModbusConnection(config=config)
    handler = AsyncModbusHandler(connection=connection)
    await handler._get_client()
    return connection, handler

async def async_test(sample_rate_hz: float = 1.0):
    config_handler = AppConfigHandler("../config.json")
    config = config_handler.initialize_defaults()

    connection, handler  = await async_init(config)
    

    db_handler = AsyncDBHandler(sample_model= APCSample, config = config)
    await db_handler.connect(create_session=True)

    sessions = await db_handler.get_all_sessions()
    for s in sessions:
        print(str(s))

    samples = await db_handler.get_all_samples()
    for s in samples:
        print(str(s))
    await db_handler.close()
    sys.exit()

    instrument = PmtApcInstrument(relay = handler)
    i = 0

    await instrument.async_start_sampling()
    await db_handler.start_session()
    
    interval = 1.0 / sample_rate_hz
    start_time = time.monotonic()
    next_time = time.monotonic()
    
    while(True):
        start_monotonic = time.monotonic()
        print(start_monotonic-start_time)

        print(await instrument.async_read_sampling_status())
        print(await instrument.async_read_flow())
        data = await instrument.async_read_channels()

        await db_handler.add_sample(APCSample.from_dict(data))

        # 3) --- Driftmentes várakozás ---
        next_time += interval
        sleep_time = next_time - time.monotonic()
        if sleep_time > 0:
            await asyncio.sleep(sleep_time)
        else:
            # ha Modbus + DB lassabb volt → skip sleep, logoljuk
            print(f"WARNING: sampling drift ({sleep_time:.3f}s behind schedule)")
        i+=1
        if i>=30:
            break
        
    await instrument.async_stop_sampling()
    await db_handler.end_session()

    last_session_id = await db_handler.get_last_session_id()
    samples = await db_handler.get_samples_for_session(session_id=last_session_id)
    print(await db_handler.get_session())

    for s in samples:
        print(str(s))

    await db_handler.close()
    await connection.close()

if __name__ == "__main__": 
    is_async = True

    if not is_async:
        sync_test()
    else:
        asyncio.run(async_test())