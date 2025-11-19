import datetime
from typing import List, Optional
from typing import Type, Generic, TypeVar

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine, AsyncSession

import logging

from model.init import AppConfig
from model.database_model import Base
from model.sample_model import BaseSample
from model.session_model import SessionTable


T = TypeVar('T', bound=BaseSample)

class AsyncDBHandler(Generic[T]):

    def __init__(self, sample_model: Type[T], config: AppConfig, logger: Optional[logging.Logger] = None):
        self._sample_model = sample_model       # ORM class
        self._config = config
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
        self._logger = logger or logging.getLogger(__name__)

        self.session_id = None
        self.session_running = False
        self.samples_written = 0

    # CONNECTION CONTROL

    async def connect(self, create_session = False):
        try:
            database_url = f"sqlite+aiosqlite:///{self._config.db_path.resolve()}"
            self._engine = create_async_engine(
                database_url,
                echo=False,
                future=True,
            )
            self._session_factory = async_sessionmaker(
                self._engine,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )
            await self._init_db()
        except Exception as e:
            self._logger.error(f"Failed to connect to DB: {e}")
            raise

        if create_session:
            await self.create_session()

    async def _init_db(self):
        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            self._logger.error(f"Failed to initialize DB schema: {e}")
            raise

    async def close(self):
        if self._engine:
            try:
                if self.session_running:
                    await self.end_session()

                await self._engine.dispose()
            except Exception as e:
                self._logger.warning(f"Error on DB engine dispose: {e}")
            finally:
                self._engine = None
                self._session_factory = None


    async def check_connection(self) -> bool:
        if not self._engine:
            self._logger.error("Check connection failed: no engine")
            return False
        try:
            async with self._engine.connect() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            self._logger.error(f"DB connection check failed: {e}")
            return False


    # SESSION CONTROL

    async def create_session(self) -> int:
        """Creates a new session, returns the session_id"""
        if not self._session_factory:
            raise RuntimeError("Database not connected")
        async with self._session_factory() as session:
            new_session = SessionTable(start=None, end=None)
            session.add(new_session)
            await session.commit()
            await session.refresh(new_session)
            self._logger.debug(f"Created new session with id {new_session.id}")
            
            self.session_id = new_session.id
            return new_session.id
        
    async def get_last_session_id(self) -> Optional[int]:
        """Returns the last sessions's session id"""
        if not self._session_factory:
            raise RuntimeError("Database not connected")
        async with self._session_factory() as session:
            result = await session.execute(
                select(SessionTable.id).order_by(SessionTable.id.desc()).limit(1)
            )
            last_id = result.scalar_one_or_none()
            self._logger.debug(f"Last session id: {last_id}")
            return last_id

    async def get_session(self, session_id: Optional[int] = None) -> None:
        """Sets the start time of a selected session"""
        if not self._session_factory:
            raise RuntimeError("Database not connected")
        
        if not session_id:
            session_id = self.session_id

        async with self._session_factory() as session:
            db_session = await session.get(SessionTable, session_id)
            return db_session

    async def get_all_sessions(self) -> List[SessionTable]:
        """Returns all session's info"""
        if not self._session_factory:
            raise RuntimeError("Database not connected")
        async with self._session_factory() as session:
            result = await session.execute(select(SessionTable).order_by(SessionTable.id))
            sessions = result.scalars().all()
            self._logger.debug(f"Fetched {len(sessions)} sessions")
            return sessions


    async def start_session(self, session_id: Optional[int] = None, start_time: Optional[datetime.datetime] = None) -> None:
        """Sets the start time of a selected session"""
        if not self._session_factory:
            raise RuntimeError("Database not connected")
        
        if not session_id:
            session_id = self.session_id

        async with self._session_factory() as session:
            db_session = await session.get(SessionTable, session_id)
            if not db_session:
                raise ValueError(f"Session ID {session_id} not found")
            db_session.start = start_time or datetime.datetime.now(datetime.timezone.utc)
            await session.commit()
            self._logger.debug(f"Started session {session_id} at {db_session.start}")
            self.session_running = True

    async def end_session(self, session_id: Optional[int] = None, end_time: Optional[datetime.datetime] = None) -> None:
        """Sets the end time of a selected session"""
        if not self._session_factory:
            raise RuntimeError("Database not connected")
        
        if not session_id:
            session_id = self.session_id

        async with self._session_factory() as session:
            db_session = await session.get(SessionTable, session_id)
            if not db_session:
                raise ValueError(f"Session ID {session_id} not found")
            db_session.end = end_time or datetime.datetime.now(datetime.timezone.utc)
            db_session.number_of_samples = self.samples_written
            await session.commit()
            self._logger.debug(f"Ended session {session_id} at {db_session.end}")
            self.session_running = False

    # MANIPULATION
    async def add_sample(self, sample: T, session_id: Optional[int] = None) -> None:
        if not sample.is_vaild:
            self._logger.info(f"Invalid sample @{datetime.datetime.now(datetime.timezone.utc)}: Instrument timestamp = {sample.instrument_datetime}")
            return

        if not self._session_factory:
            msg = "Database not connected"
            self._logger.error(msg)
            raise RuntimeError(msg)
        
        if not session_id:
            session_id = self.session_id

        if session_id is not None:
            sample.session_id = session_id
        try:
            async with self._session_factory() as session:
                async with session.begin():
                    session.add(sample)
                    self.samples_written+=1

        except Exception as e:
            self._logger.error(f"Failed to add sample: {e}")
            raise

    async def get_all_samples(self) -> List[T]:
        if not self._session_factory:
            msg = "Database not connected"
            self._logger.error(msg)
            raise RuntimeError(msg)
        try:
            async with self._session_factory() as session:
                result = await session.execute(select(self._sample_model))
                return result.scalars().all()
        except Exception as e:
            self._logger.error(f"Failed to fetch all samples: {e}")
            raise

    async def get_samples_by_timestamp_range(self, start_ts: int, end_ts: int) -> List[T]:
        if not self._session_factory:
            msg = "Database not connected"
            self._logger.error(msg)
            raise RuntimeError(msg)
        try:
            async with self._session_factory() as session:
                stmt = select(self._sample_model).where(
                    self._sample_model.instrument_unix_timestamp >= start_ts,
                    self._sample_model.instrument_unix_timestamp <= end_ts,
                )
                result = await session.execute(stmt)
                return result.scalars().all()
        except Exception as e:
            self._logger.error(f"Failed to fetch samples by timestamp range: {e}")
            raise
    
    async def get_samples_for_session(self, session_id: Optional[int] = None) -> List[T]:
        if not self._session_factory:
            msg = "Database not connected"
            self._logger.error(msg)
            raise RuntimeError(msg)
        try:
            if not session_id:
                session_id = self.session_id

            async with self._session_factory() as session:
                stmt = select(self._sample_model).where(self._sample_model.session_id == session_id)
                result = await session.execute(stmt)
                return result.scalars().all()
        except Exception as e:
            self._logger.error(f"Failed to fetch samples for session {session_id}: {e}")
            raise