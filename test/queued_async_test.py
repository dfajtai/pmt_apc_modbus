import asyncio
import logging
import datetime
import time
import random
from typing import Optional, Any, Dict

from sqlalchemy import Integer, Column, DateTime, text
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine, AsyncSession
from sqlalchemy.pool import StaticPool

import threading

Base = declarative_base()

class S(Base):
    __tablename__ = "test_table"
    id = Column(Integer, primary_key=True, autoincrement=True)
    start = Column(DateTime, nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        index=True,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

class SampleWriter:
    def __init__(
        self,
        logger: logging.Logger,
        db_url: str = "sqlite+aiosqlite:///test_db.db",
        loop: Optional[asyncio.AbstractEventLoop] = None,
        queue_maxsize: int = 1000,
    ):
        self.logger = logger
        self.db_url = db_url
        self.loop = loop or asyncio.get_event_loop()
        self.queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=queue_maxsize)
        self._stop_event = asyncio.Event()
        self._consumer_task: Optional[asyncio.Task] = None
        self.engine: Optional[AsyncEngine] = None
        self.Session: Optional[async_sessionmaker[AsyncSession]] = None

    async def start(self) -> None:
        self.logger.debug("[SampleWriter] Creating async engine")
        self.engine = create_async_engine(
            self.db_url,
            echo=False,
            connect_args={"check_same_thread": False, "timeout": 30},
            poolclass=StaticPool,
        )
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.Session = async_sessionmaker(self.engine, expire_on_commit=False)
        self._consumer_task = self.loop.create_task(self._consumer())
        self.logger.debug("[SampleWriter] Started consumer task")

    async def stop(self) -> None:
        self.logger.debug("[SampleWriter] Stopping")
        self._stop_event.set()
        await self.queue.put({"type": "stop"})
        if self._consumer_task is not None:
            await self._consumer_task
        if self.engine is not None:
            await self.engine.dispose()
        self.logger.debug("[SampleWriter] Stopped and engine disposed")

    async def _consumer(self) -> None:
        assert self.Session is not None, "Session not initialized"
        self.logger.debug("[SampleWriter] Consumer loop started")
        try:
            while True:
                item = await self.queue.get()
                try:
                    if item.get("type") == "stop":
                        self.logger.debug("[SampleWriter] Stop item received")
                        break
                    async with self.Session() as session:
                        obj = S()
                        start_value = item.get("start")
                        if start_value is not None:
                            obj.start = start_value
                        session.add(obj)
                        self.logger.debug("[SampleWriter] Before commit")
                        await session.commit()
                        self.logger.debug("[SampleWriter] After commit")
                except Exception as e:
                    self.logger.error(f"[SampleWriter] Error writing sample: {e}")
                finally:
                    self.queue.task_done()
        finally:
            self.logger.debug("[SampleWriter] Consumer loop finished")

    def add_sample(self, start: Optional[datetime.datetime] = None) -> None:
        if self.loop.is_closed():
            raise RuntimeError("Event loop is closed")
        item = {"type": "sample", "start": start}
        fut = asyncio.run_coroutine_threadsafe(self.queue.put(item), self.loop)
        fut.result()

async def squlite_task(logger: logging.Logger, event: asyncio.Event, task: str = "", writer: SampleWriter = None):
    logger.debug(f"[T{task}] Producer started")
    start = time.monotonic()
    next_time = start
    while not event.is_set():
        next_time = next_time + 1.0
        writer.add_sample(start=datetime.datetime.now(datetime.timezone.utc))
        delay = next_time - time.monotonic()
        if delay > 0:
            await asyncio.sleep(delay)
    logger.debug(f"[T{task}] Producer stopped")

async def dummy_interrupt_task(logger: logging.Logger, event: asyncio.Event, task: str = ""):
    i = 0
    while True:
        rnd = random.random()
        if rnd > 0.995:
            logger.debug(f"[T{task}] Dummy interrupt initiated in {i} steps.")
            event.set()
            break
        if event.is_set():
            break
        await asyncio.sleep(.1)
    return True

async def create_run_tasks(logger: logging.Logger, event: asyncio.Event):
    logger.debug("Creating task")
    writer = SampleWriter(logger=logger)
    await writer.start()
    t1 = asyncio.create_task(squlite_task(logger=logger, task="1", event=event, writer=writer))
    t2 = asyncio.create_task(dummy_interrupt_task(logger=logger, task="2", event=event))
    await asyncio.gather(t1, t2)
    await writer.stop()
    logger.debug("Task done")
    return True

def _thread_with_interrupt(logger: logging.Logger, event: asyncio.Event):
    try:
        logger.debug("Thread based approach ...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(create_run_tasks(logger=logger, event=event))
    except Exception as e:
        logger.error(e)
        raise Exception from e

def run_test_on_thread_with_internal_interrupt(logger: logging.Logger):
    stop_event = asyncio.Event()
    start = time.monotonic()
    thread = threading.Thread(target=_thread_with_interrupt, args=(logger, stop_event), daemon=False)
    logger.debug("Starting thread")
    thread.start()
    logger.debug("Thread started")
    while True:
        time.sleep(1)
        if (time.monotonic() - start > 20) or stop_event.is_set():
            break
    stop_event.set()
    thread.join()
    logger.debug("Thread finished")

if __name__ == "__main__":
    logger = logging.getLogger("asyncio")
    logger.setLevel(logging.DEBUG)
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    run_test_on_thread_with_internal_interrupt(logger)
