import datetime

from typing import List, Optional
from typing import Type, Generic, TypeVar, Callable, Tuple, Coroutine, Any

import threading
import asyncio

from sqlalchemy import select, inspect
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine, AsyncSession, AsyncConnection
from sqlalchemy.pool import StaticPool, NullPool

import logging

from model.init import AppConfig
from model.database_model import Base
from model.sample_model import BaseSample
from model.session_model import SamplingSession


T = TypeVar('T', bound=BaseSample)

QueueItem = Tuple[
    Callable[..., Coroutine[Any, Any, Any]],
    Tuple[Any, ...],
    asyncio.Future
]


class AsyncDBHandler(Generic[T]):

    def __init__(self, sample_model: Type[T], config: AppConfig, logger: Optional[logging.Logger] = None,
                 loop: Optional[asyncio.AbstractEventLoop] = None):
        self._sample_model = sample_model

        self._config = config

        self._logger: Optional[logging.Logger] = logger or logging.getLogger(__name__)

        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
        self._is_db_connected: bool = False       
                
        self._lock = asyncio.Lock()
        self._queue: asyncio.Queue[Optional[QueueItem]] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None

        self._sampling_session_id = None
        self._sampling_session_running = False
        self._samples_written = 0

        # --- THREAD-SAFE EVENT LOOP ---
        self._loop = loop

    @property
    def session_id(self):
        return self._sampling_session_id
    
    @property
    def session_running(self):
        return self._sampling_session_running
    
    @property
    def samples_written(self):
        return self._samples_written

    # QUEUED QUERY HANDLING

    async def _submit_job(
        self,
        coro_func: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any
    ) -> Any:
        if self._worker_task is None:
            raise RuntimeError(
                "Worker is not running. Call start() before submitting jobs."
            )
        try:
            if self._loop is not None:
                future = self._loop.create_future()
            else:
                future = asyncio.get_running_loop().create_future()
        except Exception as e:
            if self._logger:
                self._logger.exception("Error creating Future in DB handler")
                raise e


        await self._queue.put((coro_func, args, future))
        return await future

    async def _worker_loop(self)->bool:
        self._logger.debug("DB Worker task started.")

        while True:
            item = await self._queue.get()

            if item is None:
                self._queue.task_done()
                break

            coro_func, args, future = item
            try:
                result = await coro_func(*args)
                if not future.done():
                    future.set_result(result)
            except Exception as exc:
                if not future.done():
                    future.set_exception(exc)
                self._logger.error(f"Error in DB worker: {exc}")
            finally:
                self._queue.task_done()

        self._logger.debug("DB Worker task finished.")

        return True

    # CONNECTION

    async def connect(self):
        database_url = f"sqlite+aiosqlite:///{self._config.db_path.resolve()}"
        self._engine = create_async_engine(
            database_url,
            echo=True,
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self._session_factory = async_sessionmaker(
            self._engine,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

        self._is_db_connected = True


    # DATABASE INITIALIZATION

    async def _db_get_tables(self, connection: AsyncConnection ):
        def sync_inspect(c):
            inspector = inspect(c)
            return inspector.get_table_names()
        tables = await connection.run_sync(sync_inspect)
        return tables

    async def _db_create_schema(self, connection: AsyncConnection ):
        await connection.run_sync(Base.metadata.create_all)


    async def initialize_db(self):
        """Instant task, without queue"""
        if not self._is_db_connected:
            if self._logger:
                self._logger.warning("DB initialization called wothout DB connection.")
            return False
        
        async with self._lock:
            async with self._session_factory() as session:
                assert isinstance(session,AsyncSession)

                conn = await session.connection()

                existing_tables = await self._db_get_tables(connection=conn)
                if not existing_tables:
                    await self._db_create_schema(connection=conn)
                    self._logger.info("Database schema created.")
                else:
                    self._logger.info("Database schema exists; skipped creation.")
                

    # CONTROL

    async def start(self):
        """Connect to DB -> Initialize DB -> START worker task"""
        await self.connect()
        await self.initialize_db()
        self._worker_task = asyncio.create_task(self._worker_loop())


    async def stop(self):
        """Send None task to worker -> AWAITS worker task to finish -> Disconnects DB"""
        if self._logger:
            self._logger.info("Stopping AsyncDBHandler...")

        await self._queue.put(None)

        await self._queue.join()
    
        if self._worker_task:
            await self._worker_task
            self._worker_task = None

        if self._engine:
            await self._engine.dispose()
        self._is_db_connected = False

        self._logger.info("AsyncDBHandler stopped.")


    # SESSION HANDLING
    async def create_sampling_session(self)->int:
        async def _create_sampling_session_impl()->int:
            async with self._lock:
                async with self._session_factory() as session:
                    assert isinstance(session,AsyncSession)

                    new_session = SamplingSession(start=None, end=None)
                    session.add(new_session)
                    await session.flush()
                    await session.refresh(new_session)

                    await session.commit()

                    return new_session.id

        return await self._submit_job(_create_sampling_session_impl)


    async def start_sampling_session(self, session_id: Optional[int]= None, start_time: Optional[datetime.datetime] = None)->bool:
        if session_id is None:
            session_id = self.session_id

        async def _start_sampling_session_impl(session_id:int, start_time:Optional[datetime.datetime])->bool:
            async with self._lock:
                async with self._session_factory() as session:
                    assert isinstance(session,AsyncSession)

                    db_session = await session.get(SamplingSession, session_id)
                    if not db_session:
                        raise ValueError(f"Session ID {session_id} not found")
                    db_session.start = start_time or datetime.datetime.now(datetime.timezone.utc)

                    await session.commit()

            return True
        res = await self._submit_job(_start_sampling_session_impl, session_id, start_time)

        self._sampling_session_running = True

        return res


    async def end_sampling_session(self, session_id: Optional[int]= None, end_time: Optional[datetime.datetime] = None)->bool:
        if session_id is None:
            session_id = self.session_id

        async def _end_sampling_session_impl(session_id:int, end_time:Optional[datetime.datetime])->bool:
            async with self._lock:
                async with self._session_factory() as session:
                    assert isinstance(session,AsyncSession)

                    db_session = await session.get(SamplingSession, session_id)
                    if not db_session:
                        raise ValueError(f"Session ID {session_id} not found")
                    db_session.end = end_time or datetime.datetime.now(datetime.timezone.utc)
                    db_session.number_of_samples = self.samples_written

                    await session.commit()

            return True

        success = await self._submit_job(_end_sampling_session_impl,session_id,end_time)
        self._sampling_session_running = False
        return success
    

    async def get_last_session_id(self)->int:
        async def _get_last_session_id_impl():
            async with self._lock:
                async with self._session_factory() as session:
                    assert isinstance(session,AsyncSession)
                    result = await session.execute(
                        select(SamplingSession.id).order_by(SamplingSession.id.desc()).limit(1)
                    )
                    return result.scalar_one_or_none()
                
        return await self._submit_job(_get_last_session_id_impl)
    

    async def get_all_session(self)->List[SamplingSession]:
        async def _get_all_session_impl()->List[SamplingSession]:
            async with self._lock:
                async with self._session_factory() as session:
                    assert isinstance(session,AsyncSession)
                    result = await session.execute(select(SamplingSession).order_by(SamplingSession.id))
                    return result.scalars().all()
                
        return await self._submit_job(_get_all_session_impl)


    async def get_session_by_id(self, session_id)->Optional[SamplingSession]:
        if session_id is None:
            session_id = self.session_id
            
        async def _get_session_by_id_impl(session_id:int)->Optional[SamplingSession]:
            async with self._lock:
                async with self._session_factory() as session:
                    assert isinstance(session,AsyncSession)
                    return await session.get(SamplingSession, session_id)

        return await self._submit_job(_get_session_by_id_impl, session_id)


    # SAMPLE HANDLING
    async def add_sample(self, sample:T, session_id:int)->bool:
        if not sample.is_valid:
            self._logger.info(f"Invalid sample @{datetime.datetime.now(datetime.timezone.utc)}")
            return False

        if session_id is None:
            session_id = self.session_id

        if session_id is not None:
            sample.session_id = session_id

        async def _add_sample_impl(sample:T)->bool:
            async with self._lock:
                async with self._session_factory() as session:
                    assert isinstance(session,AsyncSession)
                    session.add(sample)
                    await session.commit()
                    return True
            return False
        
        success = await self._submit_job(_add_sample_impl,sample)
        if success:
            self._samples_written+=1

        return success

    async def get_all_samples(self)->List[T]:
        async def _get_all_samples_impl()->List[T]:
            async with self._lock:
                async with self._session_factory() as session:
                    assert isinstance(session,AsyncSession)
                    result = await session.execute(select(self._sample_model))
                    return result.scalars().all()
                
        return await self._submit_job(_get_all_samples_impl)

    async def get_samples_by_timestamp_range(
            self,
            start_ts: int, 
            end_ts: int
        )->List[T]:
        
        async def _get_samples_by_timestamp_range_impl(start_ts, end_ts)->List[T]:
            async with self._lock:
                async with self._session_factory() as session:
                    assert isinstance(session,AsyncSession)

                    stmt = select(self._sample_model).where(
                        self._sample_model.instrument_unix_timestamp >= start_ts,
                        self._sample_model.instrument_unix_timestamp <= end_ts,
                    )
                    result = await session.execute(stmt)
                    return result.scalars().all()

        return await self._submit_job(_get_samples_by_timestamp_range_impl, start_ts, end_ts)


    async def get_samples_for_session(self,session_id)->List[T]:
        if session_id is None:
            session_id = self.session_id

        async def _get_samples_for_session_impl()->List[T]:
            async with self._lock:
                async with self._session_factory() as session:
                    assert isinstance(session,AsyncSession)
                    stmt = select(self._sample_model).where(self._sample_model.session_id == session_id)
                    result = await session.execute(stmt)
                    return result.scalars().all()

        return await self._submit_job(_get_samples_for_session_impl, session_id)
