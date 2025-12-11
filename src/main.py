import time
import asyncio
import sys

from logic.config_handler import AppConfig, AppConfigHandler

from services.async_modbus_handler import AsyncModbusConnection, AsyncModbusHandler
from services.async_db_handler import AsyncDBHandler

from logic.apc_sample import APCSample
from logic.apc_instrument import PmtApcInstrument

from logic.apc_data_recorder import ApcDataRecorder




# -----------------------------
# ASYNC INIT HELPERS
# -----------------------------
async def async_init(config: AppConfig):
    connection = AsyncModbusConnection(config=config)
    handler = AsyncModbusHandler(connection=connection)

    # ensures client connects
    await handler._get_client()
    return connection, handler


# -----------------------------
# ASYNC TEST
# -----------------------------
async def async_test(sample_rate_hz: float = 1.0, print_last=False):
    config = AppConfigHandler("../config.json").initialize_defaults()

    connection, handler = await async_init(config)
    db_handler = AsyncDBHandler(sample_model=APCSample, config=config)

    await db_handler.connect(create_session=False)

    # optional: print last DB content
    if print_last:
        sessions = await db_handler.get_all_sessions()
        for s in sessions:
            print(s)

        last = await db_handler.get_last_session_id()
        samples = await db_handler.get_samples_for_session(last)
        for row in samples:
            print(row)

        await db_handler.close()
        await connection.close()
        return

    instrument = PmtApcInstrument(relay=handler)

    await instrument.async_start_sampling()
    await db_handler.create_session()
    await db_handler.start_session()

    interval = 1.0 / sample_rate_hz
    next_time = time.monotonic()

    for i in range(30):
        print("T:", time.monotonic())

        status = await instrument.async_read_sampling_status()
        flow = await instrument.async_read_flow()
        channels = await instrument.async_read_channels()

        print("Status:", status)
        print("Flow:", flow)

        await db_handler.add_sample(APCSample.from_dict(channels))

        # drift-less wait
        next_time += interval
        sleep_time = next_time - time.monotonic()

        if sleep_time > 0:
            await asyncio.sleep(sleep_time)
        else:
            print(f"WARNING: sampling drift ({sleep_time:.3f}s behind)")

    await instrument.async_stop_sampling()
    await db_handler.end_session()

    last = await db_handler.get_last_session_id()
    samples = await db_handler.get_samples_for_session(last)

    print("Session:", await db_handler.get_session())

    for s in samples:
        print(s)

    await db_handler.close()
    await connection.close()


def simple_tests():
    asyncio.run(async_test())


# -----------------------------
# RECORDER TEST
# -----------------------------
async def initialize_recorder():
    recorder = ApcDataRecorder()
    await recorder.initialize()
    return recorder


def thread_test():
    # Create recorder but do NOT initialize it in the main thread.
    # Initializing in the thread ensures async primitives (queues, tasks)
    # are created on the thread's event loop and not bound to the main loop.
    recorder = ApcDataRecorder()
    recorder.start_in_thread()
    
    time.sleep(30)
    recorder.manual_stop_sampling()
    recorder.stop_thread()

    # Wait for the recorder thread to exit
    # recorder.thread_obj.join()


# -----------------------------
# MAIN ENTRY
# -----------------------------
if __name__ == "__main__":
    # simple_tests()
    thread_test()
