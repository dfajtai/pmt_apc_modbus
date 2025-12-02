import datetime

from typing import List, Optional
from typing import Type, Generic, TypeVar, Callable, Tuple, Coroutine, Any

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

QueueItem = Tuple[
    Callable[..., Coroutine[Any, Any, Any]],
    Tuple[Any, ...],
    asyncio.Future
]


class AsyncDBHandler(Generic[T]):

    def __init__(self, sample_model: Type[T], config: AppConfig, logger: Optional[logging.Logger] = None):
        self._sample_model = sample_model
        self._config = config
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
        self._logger: Optional[logging.Logger] = logger or logging.getLogger(__name__)

                
        self._lock = asyncio.Lock()
        self._queue: asyncio.Queue[Optional[QueueItem]] = asyncio.Queue()
        self._worker_task = Optional[asyncio.Task] = None
        

        
        self.session_id = None
        self.session_running = False
        self.samples_written = 0