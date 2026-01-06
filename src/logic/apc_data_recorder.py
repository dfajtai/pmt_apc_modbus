from typing import Union, Optional, Dict, Callable, Deque, List
from collections import deque
from dataclasses import dataclass, field
import logging
import asyncio
import threading
import time
import datetime

from transitions import Machine

from ..services.logging_callback import CallbackLoggingHandler

from .config_handler import AppConfig, AppConfigHandler

from ..services.async_modbus_handler import AsyncModbusConnection, AsyncModbusHandler, ModbusException
from ..services.async_db_handler import AsyncDBHandler

from .apc_sample import APCSample
from .apc_instrument import PmtApcInstrument

class ApcDataRecorderException(Exception):
    pass

@dataclass
class ApcRecordSession():
    session_id:int
    flow:float
    deque_len: int

    session_start:Optional[int] = None # monotonic timestamp
    session_end:Optional[int] = None # monotonic timestamp

    live_data: Dict[str, Deque[int]] = field(default_factory=dict)
    accumulator: Dict[str, int] = field(default_factory=dict)

    num_of_samples:int = 0
    time_elapsed: int = 0

    def __post_init__(self):
        for channel in PmtApcInstrument.CHANNELS:
            self.live_data[channel.channel_name] = deque(maxlen=self.deque_len)
            self.accumulator[channel.channel_name] = 0
    
    @staticmethod
    def form_db(sample_list:List[APCSample]):
        raise NotImplementedError()
        pass

    def add_sample(self, sample:APCSample):
        if not sample.is_valid:
            return False

        if self.session_start is None: # implicitly starts 
            self.session_start = time.monotonic()

        for channel in PmtApcInstrument.CHANNELS:
            self.live_data[channel.channel_name].append(sample[channel.channel_name])
            self.accumulator[channel.channel_name]+=sample[channel.channel_name]
        
        self.time_elapsed = int(time.monotonic() - self.session_start)
        self.num_of_samples +=1

        return True
    
    def end_session(self):
        self.session_end = time.monotonic()

    # -------------------------
    # Helper functions
    # -------------------------
    @property
    def total_volume(self)->Union[float,None]:
        raise NotImplementedError()

    # -------------------------
    # Statistics functions
    # -------------------------

    def on_flight_staistics(self):

        # sliding window average...

        pass

    def session_statistics(self):

        pass
    


class ApcDataRecorder():
    """
    Async recorder controlling:
      - Async Modbus connection/handler
      - Instrument (PmtApcInstrument)
      - Async DB (AsyncDBHandler)
    Features:
      - initialize() to prepare resources
      - async start_recording()
      - async stop_recording()
      - start_in_thread()/stop_thread() to run in background thread (GUI-friendly)
      - watchdog monitoring
      - drift-free sampling loop (monotonic time)
      - structured logging + callback logging handler
    """

    def __init__(self, file_logger: bool = True):
        # event loop / thread related
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        self._thread: Optional[threading.Thread] = None
        self._thread_started = threading.Event()

        # stop events (thread-safe and async)
        self._stop_event = threading.Event()        # used for thread-based stop signalling
        self._async_stop: Optional[asyncio.Event] = None  # created per-loop
        self._sampling_started = False

        # logger
        self.logger = logging.getLogger("ApcDataRecorder")
        self.logger.setLevel(logging.DEBUG)

        # callbacks (e.g. GUI)
        self.callback_handler = CallbackLoggingHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.callback_handler.setFormatter(formatter)
        self.logger.addHandler(self.callback_handler)

        if file_logger:
            file_handler = logging.FileHandler("apcdatarecorder.log")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            #TODO DEBUG
            console_handler = logging.StreamHandler() 
            self.logger.addHandler(console_handler)

        # GUI state change callback
        self.state_change_callback: Optional[Callable[[str], None]] = None

    def set_state_change_callback(self, callback: Callable[[str], None]):
        self.state_change_callback = callback

        # config / components
        self.config_handler: Optional[AppConfigHandler] = None
        self.config: Optional[AppConfig] = None

        self.modbus_connection: Optional[AsyncModbusConnection] = None
        self.modbus_handler: Optional[AsyncModbusHandler] = None

        self.db_handler: Optional[AsyncDBHandler] = None

        self.instrument: Optional[PmtApcInstrument] = None

        # state flags
        self.config_initialized = False
        self.modbus_initialized = False
        self.db_initialized = False
        self.instrument_initialized = False

        # runtime tasks
        self._sampling_task: Optional[asyncio.Task] = None
        self._watchdog_task: Optional[asyncio.Task] = None

        # recording metadata
        self.record_session: ApcRecordSession = None
        
        # FSM for state management
        self.machine = Machine(
            model=self,
            states=['uninitialized', 'initialized', 'recording', 'stopped', 'error'],
            initial='uninitialized',
            transitions=[
                dict(trigger='fsm_initialize', source='uninitialized', dest='initialized', after='on_initialize'),
                dict(trigger='fsm_start_recording', source='initialized', dest='recording', after='on_start_recording'),
                dict(trigger='fsm_stop_recording', source='recording', dest='stopped', after='on_stop_recording'),
                dict(trigger='fsm_error', source='*', dest='error', after='on_error'),
                dict(trigger='fsm_reset', source='error', dest='uninitialized', after='on_reset'),
            ],
            auto_transitions=False
        )

        self.logger.info("ApcDataRecorder created")
    

    # -------------------------
    # Initialization helpers
    # -------------------------

    def _initialize_config(self) -> bool:
        if not self.config_initialized:
            try:
                self.config_handler = AppConfigHandler("../config.json", logger=self.logger)
                self.config = self.config_handler.load_from_json()
            except Exception as e:
                self.logger.error("Error during loading/initializing config.")
                self.logger.exception(e)
                return False
        self.config_initialized = True
        return True

    async def _initialize_modbus(self) -> bool:
        if not self.modbus_initialized:
            try:
                self.modbus_connection = AsyncModbusConnection(config=self.config, logger=self.logger)
                await self.modbus_connection.connect()
            except Exception as e:
                self.logger.error("Error during initializing MODBUS Connection.")
                self.logger.error(f"Exception: {e}")
                return False

            try:
                self.modbus_handler = AsyncModbusHandler(connection=self.modbus_connection, logger=self.logger, test_address= 30164)
                # public check that DOES NOT reconnect

                await self.modbus_handler.start()
                await asyncio.sleep(0.3)
                ok = await self.modbus_handler.check_connection()
                if not ok:
                    raise ModbusException("Initial modbus health-check failed")
            except Exception as e:
                self.logger.error("Error during initializing MODBUS Handler.")
                self.logger.error(f"Exception: {e}")
                return False

            

        self.modbus_initialized = True
        return True

    async def _initialize_db(self) -> bool:
        if not self.db_initialized:
            try:
                self.db_handler = AsyncDBHandler(sample_model=APCSample, config=self.config, logger=self.logger)
                await self.db_handler.start()
                # await self.db_handler.connect()
                # await self.db_handler.initialize_db()

            except Exception as e:
                self.logger.error("Error during connecting to the database.")
                self.logger.error(f"Exception: {e}")
                return False
        self.db_initialized = True
        return True

    def _initialize_instrument(self) -> bool:
        if not self.instrument_initialized:
            if self.modbus_handler is None:
                self.logger.error("Cannot initialize instrument: modbus handler missing")
                return False
            try:
                self.instrument = PmtApcInstrument(relay=self.modbus_handler, logger= self.logger)
            except Exception as e:
                self.logger.error("Error during initializing instrument.")
                self.logger.error(f"Exception: {e}")
                return False
        self.instrument_initialized = True
        return True

    async def initialize(self) -> bool:
        """
        Initialize all components. Must be called before start_recording.
        """
        if not self._initialize_config():
            return False

        if not await self._initialize_modbus():
            return False
                
        if not await self._initialize_db():
            return False

        if not self._initialize_instrument():
            return False

        self.logger.info("ApcDataRecorder initialized successfully.")
        self.fsm_initialize()
        return True

    @property
    def is_initialized(self) -> bool:
        return all([
            self.config_initialized,
            self.modbus_initialized,
            self.db_initialized,
            self.instrument_initialized
        ])

    @property
    def thread_obj(self):
        return self._thread

    # -------------------------
    # Logging callbacks
    # -------------------------

    def add_log_callback(self, callback: Callable[[str], None]):
        self.callback_handler.add_callback(callback)

    def remove_log_callback(self, callback: Callable[[str], None]):
        self.callback_handler.remove_callback(callback)


    # -------------------------
    # Health check (async)
    # -------------------------

    async def health_check(self) -> bool:
        """
        Full health check that does NOT perform reconnect.
        Returns True if modbus, instrument and db look healthy.
        """
        if not self.is_initialized:
            self.logger.debug("Health check: recorder not initialized.")
            return False

        try:
            if self.modbus_handler is None:
                self.logger.error("Health check: modbus handler missing")
                return False

            ok = await self.modbus_handler.check_connection()
            if not ok:
                self.logger.error("MODBUS Connection lost.")
                return False

            # instrument status (assume instrument has async_read_device_status and DeviceStatus enum)
            if self.instrument is None:
                self.logger.error("Health check: instrument missing")
                return False

            status = await self.instrument.async_read_device_status()
            if status != self.instrument.DeviceStatus.NORMAL:
                self.logger.critical("Instrument status is abnormal!")
                return False
            
            current_sampling_status = await self.instrument.async_read_sampling_status()
            if current_sampling_status != self.instrument.sampling_status:
                self.logger.critical("Instrument SAMPLING STATUS is falsely registrated.")
                return False

            # db connection check
            if self.db_handler is None:
                self.logger.error("Health check: db handler missing")
                return False

            ok = await self.db_handler.check_connection()
            if not ok:
                self.logger.error("Database Connection lost.")
                return False

            return True

        except Exception as e:
            self.logger.error("Error during health checkup.")
            self.logger.exception(e)
            return False
    
    # -------------------------
    # Sampling loop + watchdog
    # -------------------------

    async def _sampling_loop(self):
        if not self.is_initialized:
            self.logger.error("Cannot start sampling: recorder not initialized.")
            return False

        interval = self.config.sampling_step / 1000.0  # ms → sec
        self._async_stop = asyncio.Event()
        self._sampling_started = False

        # prepare sampling: try to start instrument and create new DB session
        try:
            start_trials = 0
            start_success = False
            while True:
                try:
                    self.logger.debug(f"Attempting to start sampling (trial {start_trials})")
                    start_success = await self.instrument.async_start_sampling()
                    self.logger.debug(f"async_start_sampling() returned: {start_success}")
                    if start_success:
                        self.logger.info("Sampling started successfully on instrument")
                        break
                    if start_trials > 4:
                        self.logger.error(f"Max start trials ({start_trials}) exceeded")
                        break
                    start_trials += 1
                    await asyncio.sleep(1.0)
                except Exception as e:
                    # swallow, try again
                    self.logger.debug(f"Exception during start attempt {start_trials}: {e}")
                    start_trials += 1
                    await asyncio.sleep(0.2)

            if not start_success:
                self.logger.error("Unable to start sampling")
                self._async_stop.set()
                return False

            # ensure last session closed (optional – if you want to force-close previous)
            try:
                await self.db_handler.end_sampling_session()
            except Exception:
                # ignore if there was no previous session; just log
                self.logger.debug("No previous DB session to end or error ending it (ignored).")

            # create new session and local record session
            current_session_id = await self.db_handler.create_sampling_session()
            # IMPORTANT: make sure DB handler knows current session id or use explicit ids later
            # e.g. await self.db_handler.set_current_session_id(current_session_id)
            flow = await self.instrument.async_read_flow()
            self.record_session = ApcRecordSession(
                session_id=current_session_id,
                flow=(flow / 1000.0) if flow is not None else 0.0,
                deque_len=self.config.live_window_len
            )

        except Exception as e:
            self.logger.error("Failed to initialize sampling session")
            self.logger.exception(e)
            return False

        # prepare timing
        next_time = time.monotonic()
        sample = None
        start_time = None

        # WAIT FOR REAL VALID SAMPLE -> mark session as started only when first good sample arrives
        wait_attempts = 0
        max_wait_attempts = 100  # timeout: ~10 seconds at 1 sample/sec
        
        while not self._async_stop.is_set():
            try:
                next_time += interval
                wait_attempts += 1

                status = await self.instrument.async_read_sampling_status()
                self.logger.debug(f"[Wait Sample] Status: {status}, Attempt: {wait_attempts}")
                
                if status == self.instrument.SamplingStatus.SAMPLING:
                    data = await self.instrument.async_read_channels()
                    self.logger.debug(f"[Wait Sample] Channel data: {data}")
                    
                    sample = APCSample.from_dict(data)

                    is_valid = sample.is_valid

                    self.logger.debug(f"[Wait Sample] Sample valid: {is_valid}")
                    if is_valid:
                        # explicitly pass the session id returned earlier.
                        # don't rely on db_handler internal session_id unless you set it.
                        await self.db_handler.start_sampling_session(session_id=self.record_session.session_id,
                                                                    start_time=datetime.datetime.now(datetime.timezone.utc))
                        start_time = time.monotonic()
                        self._sampling_started = True
                        self.logger.info(f"Sampling session started (ID={self.record_session.session_id})")
                        break
                else:
                    self.logger.debug(f"[Wait Sample] Not in SAMPLING state, current: {status}")

                # timeout check
                if wait_attempts > max_wait_attempts:
                    self.logger.error(f"Timeout waiting for first valid sample after {max_wait_attempts} attempts")
                    return False

                delay = next_time - time.monotonic()
                if delay > 0:
                    await asyncio.sleep(delay)
            except asyncio.CancelledError:
                self.logger.info("Sampling task cancelled externally - before actual sampling started...")
                return False
            except Exception as e:
                self.logger.error(f"Error while awaiting first valid sample (attempt {wait_attempts})")
                self.logger.exception(e)
                return False

        # double-check we have a valid sample
        if not isinstance(sample, APCSample):
            self.logger.warning("No APCSample obtained at session start - aborting sampling.")
            # try to cleanup
            try:
                await self.instrument.async_stop_sampling()
                await self.db_handler.end_sampling_session(session_id=self.record_session.session_id)
            except Exception:
                pass
            return False

        is_valid = sample.is_valid
        if not is_valid:
            self.logger.warning("First sample considered invalid after check - aborting.")
            try:
                await self.instrument.async_stop_sampling()
                await self.db_handler.end_sampling_session(session_id=self.record_session.session_id)
            except Exception:
                pass
            return False

        # --- actual sampling loop ---
        # note: we already consumed the first valid sample into `sample`
        # add it to record and DB
        try:
            # Add first sample
            self.record_session.add_sample(sample)  # record local sliding-window
            await self.db_handler.add_sample(sample, session_id=self.record_session.session_id)

            # continue periodic sampling
            while not self._async_stop.is_set():
                next_time += interval
                try:
                    data = await self.instrument.async_read_channels()
                    sample = APCSample.from_dict(data)

                    # add to in-memory session
                    try:
                        self.record_session.add_sample(sample)
                    except Exception:
                        self.logger.debug("record_session.add_sample() failed for a sample (ignored).")

                    # persist to DB
                    try:
                        await self.db_handler.add_sample(sample, session_id=self.record_session.session_id)
                    except Exception as e:
                        self.logger.error("Failed to persist sample to DB")
                        self.logger.exception(e)

                    # drift-free sleep
                    delay = next_time - time.monotonic()
                    if delay > 0:
                        await asyncio.sleep(delay)
                    else:
                        self.logger.warning(f"Sampling drift ({-delay:.3f}s behind schedule)")

                    # time limit for session
                    if self._sampling_started and (time.monotonic() - start_time >= self.config.sampling_time):
                        break

                except asyncio.CancelledError:
                    self.logger.info("Sampling task cancelled externally.")
                    break
                except Exception as e:
                    self.logger.error("Error during sampling loop iteration")
                    self.logger.exception(e)
                    # brief backoff before continuing
                    await asyncio.sleep(min(interval, 0.5))

        finally:
            # Stop instrument + DB session; don't stop worker threads here — close_connections handles that
            try:
                await self.instrument.async_stop_sampling()
            except Exception as e:
                self.logger.error("Failed to stop instrument sampling")
                self.logger.exception(e)

            try:
                await self.db_handler.end_sampling_session(session_id=self.record_session.session_id,
                                                        end_time=datetime.datetime.now(datetime.timezone.utc))
                self.record_session.end_session()
            except Exception as e:
                self.logger.error("Failed to end DB session")
                self.logger.exception(e)

            self.logger.info(f"Sampling session ended (ID={self.record_session.session_id})")
            self._sampling_started = False

        return True


    async def _watchdog_loop(self):
        """
        Periodically checks instrument and sampling health.
        If abnormal condition detected, stops the sampling.
        """
        if not self.is_initialized:
            self.logger.warning("Watchdog cannot start: recorder not initialized.")
            return

        await asyncio.sleep(5.0) # initial delay

        self.logger.info("Watchdog task started.")
        interval = 5.0  # check every 10.0 second
        next_time = time.monotonic() + interval
        try:
            while True:
                # exit if no sampling task
                if self._sampling_task is None or self._sampling_task.done():
                    await asyncio.sleep(interval)
                    continue

                # check instrument health
                try:
                    health_ok = await self.health_check()
                    if not health_ok:
                        self.logger.critical("Watchdog detected unhealthy system, stopping sampling!")
                        await self.manual_stop_sampling()
                        break
                except Exception as e:
                    self.logger.error("Watchdog error during health check")
                    self.logger.exception(e)

                # if sampling started, also check sampling status
                if self._sampling_started:
                    try:
                        status = await self.instrument.async_read_sampling_status()
                        if status != self.instrument.SamplingStatus.SAMPLING:
                            self.logger.critical("Watchdog detected sampling stopped unexpectedly, stopping task!")
                            await self.manual_stop_sampling()
                            break
                    except Exception as e:
                        self.logger.error("Watchdog error reading sampling status")
                        self.logger.exception(e)
                delay= next_time - time.monotonic()
                if delay>0:
                    await asyncio.sleep(interval)
                next_time +=interval

        except asyncio.CancelledError:
            self.logger.info("Watchdog task cancelled.")
        except Exception as e:
            self.logger.error("Unexpected error in watchdog task")
            self.logger.exception(e)
        finally:
            self.logger.info("Watchdog task finished.")

    # -------------------------
    # Public start / stop API (async)
    # -------------------------

    def is_running(self) -> bool:
        """
        Returns True if sampling is active.
        """
        return (self._sampling_task is not None and not self._sampling_task.done())

    async def start_recording(self):
        """
        Start sampling in the current asyncio loop.
        """
        if not self.is_initialized:
            raise ApcDataRecorderException("Recorder not initialized. Call initialize() first.")

        if self.is_running():
            raise ApcDataRecorderException("Recorder already running.")

        # clear stop indicators
        self._stop_event.clear()
        self._async_stop = asyncio.Event()

        # spawn tasks
        self._sampling_task = asyncio.create_task(self._sampling_loop())
        self._watchdog_task = asyncio.create_task(self._watchdog_loop())

        self.logger.info("Recording started.")
        self.fsm_start_recording()
        return True

    async def stop_recording(self, timeout: float = 10.0):
        """
        Stop sampling gracefully.
        """
        if not self.is_running():
            self.logger.info("Recorder not running.")
            return True

        # signal stop
        self._stop_event.set()
        if self._async_stop is not None and not self._async_stop.is_set():
            self._async_stop.set()

        # wait for sampling task to finish
        try:
            if self._sampling_task:
                await asyncio.wait_for(self._sampling_task, timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.error("Timeout waiting for sampling task to finish. Cancelling task.")
            if self._sampling_task:
                self._sampling_task.cancel()
                try:
                    await self._sampling_task
                except Exception:
                    pass

        # cancel watchdog
        try:
            if self._watchdog_task:
                self._watchdog_task.cancel()
                await asyncio.sleep(0)  # allow cancellation propagation
        except Exception:
            pass

        self.logger.info("Recording stopped.")
        self.fsm_stop_recording()
        return True

    # -------------------------
    # Thread-based convenience API (for GUI usage)
    # -------------------------

    def _thread_main(self):
        """
        Entry point for the background thread: creates an asyncio loop and runs start/stop there.
        Fully async-safe: uses await asyncio.sleep() instead of blocking time.sleep().
        """
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._thread_started.set()

        async def _main_async():
            try:
                # Initialize all components
                await self.initialize()
                # Start recording
                await self.start_recording()

                # Keep running until stop_event is set
                while not self._stop_event.is_set():
                    await asyncio.sleep(1.0)

                # Stop tasks gracefully
                await self.stop_recording()
                await self.close_connections()

            except Exception as e:
                self.logger.error("Background thread encountered an exception.")
                self.logger.exception(e)
            finally:
                # Cancel any remaining tasks
                pending = [t for t in asyncio.all_tasks(loop=self._loop) if not t.done()]
                for t in pending:
                    t.cancel()
                # Allow cancellations to propagate
                # await asyncio.sleep(0)
                self.logger.info("Background thread exiting.")

        # Run the async main
        try:
            self._loop.run_until_complete(_main_async())
            self._loop.close()
        except asyncio.CancelledError:
            self.logger.info("Background thread cancelled.")
        except Exception as e:
            self.logger.error("Background thread encountered an exception.")
            self.logger.exception(e)
        finally:
            # Cancel any remaining tasks
            pending = [t for t in asyncio.all_tasks(loop=self._loop) if not t.done()]
            for t in pending:
                t.cancel()
            self.logger.info("Background thread exited.")


    def init_thread(self)->threading.Thread:
        if self._thread and self._thread.is_alive():
            return self.thread_obj
        
        self._thread_started.clear()

        self._thread = threading.Thread(target=self._thread_main, args=(), daemon=True)
        return self.thread_obj



    def start_in_thread(self, thread:Optional[threading.Thread] = None, wait_for_start: bool = True):
        """
        Start the recorder in a background daemon thread. Useful for GUI apps.
        """

        if self._thread and self._thread.is_alive():
            raise ApcDataRecorderException("Recorder thread already running")

        # ensure config is loaded and components are available on the thread
        # thread will call initialize() itself
        self._stop_event.clear()
        
        self.init_thread()

        self._thread.start()

        if wait_for_start:
            # wait a short time for thread to set up loop
            started = self._thread_started.wait(timeout=5.0)
            if not started:
                raise ApcDataRecorderException("Background thread failed to start")

        self.logger.info("Recorder background thread started.")
        return True
    

    def stop_thread(self, wait_for_join: float = 5.0):
        """
        Stop the background thread run. Signals stop_event and waits for thread to join.
        """
        if not (self._thread and self._thread.is_alive()):
            self.logger.info("Recorder thread not running.")
            return True

        self._stop_event.set()
        self._thread.join(timeout=wait_for_join)
        if self._thread.is_alive():
            self.logger.warning("Recorder thread did not stop within timeout.")
        else:
            self.logger.info("Recorder thread stopped.")
        return True

    # -------------------------
    # Manual stop
    # -------------------------
    async def manual_stop_sampling(self):
        """
        External signal to stop the current sampling loop gracefully.
        """
        if self._async_stop is not None:
            self.logger.info("Manual stop signal received.")
            self._async_stop.set()
            # wait for sampling task to finish
            if self._sampling_task is not None:
                self._sampling_task.cancel()
                await self._sampling_task

            self.logger.info("Sampling stopped manually.")
        else:
            self.logger.warning("Manual stop requested, but no sampling task is running.")

    # GRACEFUL CLOSING
    async def close_connections(self):
        try:
            if self.modbus_connection:
                await self.modbus_connection.close()
                self.modbus_initialized = False
                self.logger.info("MODBUS connection closed.")

            if self.modbus_handler:
                await self.modbus_handler.stop()
                self.modbus_initialized = False
                self.logger.info("MODBUS HANDLER worker closed.")

        except Exception as e:
            self.logger.error("Error during stopping MODBUS handler.")
            self.logger.error(str(e))
            return False

        try:
            if self.db_handler:
                await self.db_handler.stop()
                self.db_initialized = False
                self.logger.info("Database connection closed.")
        except Exception as e:
            self.logger.error("Error during closing database connection.")
            self.logger.error(str(e))
            return False
        
        self.instrument_initialized = False


        return True

    # -------------------------
    # FSM callbacks
    # -------------------------

    def on_initialize(self):
        self.logger.info(f"FSM: transitioned to {self.state}")

    def on_start_recording(self):
        self.logger.info(f"FSM: transitioned to {self.state}")

    def on_stop_recording(self):
        self.logger.info(f"FSM: transitioned to {self.state}")

    def on_error(self):
        self.logger.error(f"FSM: transitioned to {self.state}")

    def on_reset(self):
        self.logger.info(f"FSM: transitioned to {self.state}")

    # -------------------------