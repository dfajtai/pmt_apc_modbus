import datetime

from typing import List, Optional
from typing import Type, Generic, TypeVar, Callable

import threading
import asyncio

from sqlalchemy import select, inspect
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine, AsyncSession
from sqlalchemy.pool import StaticPool, NullPool

import logging

from model.init import AppConfig
from model.database_model import Base
from model.sample_model import BaseSample
from model.session_model import SessionTable


T = TypeVar('T', bound=BaseSample)


class AsyncDBWorker:
    """Queue-based DB worker for sequential async DB operations."""
    def __init__(self, session_factory: async_sessionmaker, logger: Optional[logging.Logger] = None):
        self._session_factory = session_factory
        self._queue = asyncio.Queue()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._logger = logger or logging.getLogger(__name__)

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._worker_loop())
        if self._logger:
            self._logger.info("AsyncDBWorker started.")

    async def stop(self):
        self._running = False
        await self._queue.put(None)  # Stop jel
        if self._task:
            await self._task
        if self._logger:
            self._logger.info("AsyncDBWorker stopped.")

    async def submit(self, coro: Callable[[AsyncSession], any]):
        """Submit a coroutine that takes AsyncSession and returns a result."""
        fut = asyncio.get_running_loop().create_future()
        await self._queue.put((coro, fut))
        return await fut

    async def _worker_loop(self):
        while True:
            item = await self._queue.get()
            if item is None:
                break
            coro, fut = item
            try:
                async with self._session_factory() as session:
                    result = await coro(session)
                    await session.commit()
                    if not fut.done():
                        fut.set_result(result)
            except Exception as e:
                if not fut.done():
                    fut.set_exception(e)
                if self._logger:
                    self._logger.error(f"AsyncDBWorker error: {e}")


class AsyncDBHandler(Generic[T]):

    def __init__(self, sample_model: Type[T], config: AppConfig, logger: Optional[logging.Logger] = None):
        self._sample_model = sample_model
        self._config = config
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
        self._logger: Optional[logging.Logger] = logger or logging.getLogger(__name__)

        self._worker: Optional[AsyncDBWorker] = None

        self.session_id = None
        self.session_running = False
        self.samples_written = 0

    async def connect(self, create_session=False):
        database_url = f"sqlite+aiosqlite:///{self._config.db_path.resolve()}"
        self._engine = create_async_engine(
            database_url,
            echo=True,
            future=True,
            connect_args={"check_same_thread": False},
            poolclass=NullPool,
        )
        self._session_factory = async_sessionmaker(
            self._engine,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

        # Worker indítása
        self._worker = AsyncDBWorker(self._session_factory, self._logger)
        await self._worker.start()

        # DB séma inicializálása
        await self._init_db()

        if create_session:
            await self.create_session()
        if self._logger:
            self._logger.info("Database connected.")

    async def _init_db(self):
        async def get_tables(session: AsyncSession):
            conn = await session.connection()
            def sync_inspect(c):
                inspector = inspect(c)
                return inspector.get_table_names()
            tables = await conn.run_sync(sync_inspect)
            return tables

        async def create_schema(session: AsyncSession):
            conn = await session.connection()
            await conn.run_sync(Base.metadata.create_all)

        existing_tables = await self._worker.submit(get_tables)
        if not existing_tables:
            await self._worker.submit(create_schema)
            self._logger.info("Database schema created.")
        else:
            self._logger.info("Database schema exists; skipped creation.")

    async def close(self):
        if self._worker:
            await self._worker.stop()
            self._worker = None
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    # ------------------------------
    # SESSION CONTROL
    # ------------------------------
    async def create_session(self) -> int:
        async def task(session: AsyncSession):
            new_session = SessionTable(start=None, end=None)
            session.add(new_session)
            await session.flush()
            await session.refresh(new_session)
            return new_session.id

        if self._logger:
            self._logger.debug("Create session initiated")
        new_id = await self._worker.submit(task)
        if self._logger:
            self._logger.debug("Create session successful")

        self.session_id = new_id
        return new_id

    async def start_session(self, session_id: Optional[int] = None, start_time: Optional[datetime.datetime] = None):
        if not session_id:
            session_id = self.session_id

        async def task(session: AsyncSession):
            db_session = await session.get(SessionTable, session_id)
            if not db_session:
                raise ValueError(f"Session ID {session_id} not found")
            db_session.start = start_time or datetime.datetime.now(datetime.timezone.utc)

        await self._worker.submit(task)
        self.session_running = True

    async def end_session(self, session_id: Optional[int] = None, end_time: Optional[datetime.datetime] = None):
        if not session_id:
            session_id = self.session_id

        async def task(session: AsyncSession):
            db_session = await session.get(SessionTable, session_id)
            if not db_session:
                raise ValueError(f"Session ID {session_id} not found")
            db_session.end = end_time or datetime.datetime.now(datetime.timezone.utc)
            db_session.number_of_samples = self.samples_written

        await self._worker.submit(task)
        self.session_running = False

    async def get_last_session_id(self) -> Optional[int]:
        async def task(session: AsyncSession):
            result = await session.execute(
                select(SessionTable.id).order_by(SessionTable.id.desc()).limit(1)
            )
            return result.scalar_one_or_none()
        return await self._worker.submit(task)

    async def get_session(self, session_id: Optional[int] = None) -> Optional[SessionTable]:
        if not session_id:
            session_id = self.session_id

        async def task(session: AsyncSession):
            return await session.get(SessionTable, session_id)

        return await self._worker.submit(task)

    async def get_all_sessions(self) -> List[SessionTable]:
        async def task(session: AsyncSession):
            result = await session.execute(select(SessionTable).order_by(SessionTable.id))
            return result.scalars().all()
        return await self._worker.submit(task)

    # ------------------------------
    # SAMPLE CONTROL
    # ------------------------------
    async def add_sample(self, sample: T, session_id: Optional[int] = None):
        if not sample.is_valid:
            self._logger.info(f"Invalid sample @{datetime.datetime.now(datetime.timezone.utc)}")
            return

        if not session_id:
            session_id = self.session_id

        if session_id is not None:
            sample.session_id = session_id

        async def task(session: AsyncSession):
            session.add(sample)

        await self._worker.submit(task)
        self.samples_written += 1

    async def get_all_samples(self) -> List[T]:
        async def task(session: AsyncSession):
            result = await session.execute(select(self._sample_model))
            return result.scalars().all()
        return await self._worker.submit(task)

    async def get_samples_by_timestamp_range(self, start_ts: int, end_ts: int) -> List[T]:
        async def task(session: AsyncSession):
            stmt = select(self._sample_model).where(
                self._sample_model.instrument_unix_timestamp >= start_ts,
                self._sample_model.instrument_unix_timestamp <= end_ts,
            )
            result = await session.execute(stmt)
            return result.scalars().all()
        return await self._worker.submit(task)

    async def get_samples_for_session(self, session_id: Optional[int] = None) -> List[T]:
        if not session_id:
            session_id = self.session_id

        async def task(session: AsyncSession):
            stmt = select(self._sample_model).where(self._sample_model.session_id == session_id)
            result = await session.execute(stmt)
            return result.scalars().all()
        return await self._worker.submit(task)