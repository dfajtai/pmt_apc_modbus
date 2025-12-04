import asyncio
import logging
import datetime
import time

import sys

from typing import Optional, Any, Dict

from sqlalchemy import Integer, Column, DateTime, text

from sqlalchemy import func

from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine, AsyncSession

import threading

Base = declarative_base()

class S(Base):
    __tablename__ = "test_table"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        index=True,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )


class QueuedWriter():
    def __init__(self, logger:logging.Logger = None):
        self.logger = logger
        
        self._stop = asyncio.Event()
        self._main_loop_task: Optional[asyncio.Task] = None 
        
        self.engine = None
        self.SessionLocal: Optional[async_sessionmaker[AsyncSession]] = None 
        
        self.queue = asyncio.Queue()
        self.lock = asyncio.Lock()
        self._worker_task: Optional[asyncio.Task] = None 

    async def _submit_job(self, coro):
        future = asyncio.Future()
        async def wrapped_job():
            try:
                result = await coro()
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)
            finally:
                self.queue.task_done()
        
        await self.queue.put(wrapped_job)
        return future
    
        
    async def _worker(self):
        while True:
            try:
                job = await asyncio.wait_for(self.queue.get(), timeout=1)
            except asyncio.TimeoutError:
                continue
            
            if job is None:
                self.queue.task_done() 
                break
            
            async with self.lock:
                await job()

        return True

    
    async def initialize_db(self) -> bool:
        async with self.lock:
            url = "sqlite+aiosqlite:///test_db.db"

            self.logger.debug(f"Creating async engine")
            self.engine = create_async_engine(
                url,
                echo=False,               # SQL log
            )
            
            self.SessionLocal = async_sessionmaker(
                bind=self.engine, 
                expire_on_commit=False,
                class_=AsyncSession # Explicit megadás, bár alapértelmezett
            )

            self.logger.debug(f"Async engine created")
            self.logger.debug(f"Connecting, initializing")

            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            self.logger.debug(f"DB Initialized")
        
   
    
    
    async def add_sample(self) -> bool:
        async with self.SessionLocal() as sess: 
            obj = S()
            sess.add(obj)
            self.logger.debug(f"Before commit")
            await sess.commit()
            self.logger.debug(f"After commit")
            await sess.refresh(obj)
            self.logger.debug(f"Object refreshed")
        return True
        
    
    async def get_num_of_samples(self) -> int:
        async with self.lock:
            async with self.SessionLocal() as sess: 
                q = select(func.count()).select_from(S)
                result = await sess.execute(q)
                print(result.scalar())
            return True
        
    async def _main_loop(self):
        start = time.monotonic()
        next_time = start
        
        while not self._stop.is_set():
            next_time = next_time + 1.0
            await self._submit_job(self.add_sample)
            
            delay = next_time - time.monotonic()
            if delay > 0:
                await asyncio.sleep(delay)
            await self.get_num_of_samples()
    
    
    async def start(self):
        self._worker_task = asyncio.create_task(self._worker())
        self._main_loop_task = asyncio.create_task(self._main_loop())
    
       
    async def stop(self):
        self.logger.info("Stopping QueuedWriter...")
        
        # 1. Jelezd a main_loopnak, hogy ne generáljon több feladatot
        self._stop.set()
        
        # 2. Várd meg, amíg a main_loop befejezi a jelenlegi ciklust és leáll
        await self._main_loop_task
        self.logger.info("Main loop stopped.")

        # 3. Várjuk meg, amíg a queue-ban lévő ÖSSZES feladat feldolgozásra kerül
        await self.queue.join()
        self.logger.info("All queue tasks processed.")

        # 4. Küldd el a None jelet a workernek, hogy a ciklusa befejeződjön
        await self.queue.put(None)
        
        # 5. Várd meg a worker task tényleges befejezését
        await self._worker_task
        self.logger.info("Worker task stopped.")
        
        await self.get_num_of_samples()
        
        # 6. Zárd be az engine-t
        if self.engine:
            await self.engine.dispose()
            self.logger.info("DB engine disposed.")
        
        self.logger.info("QueuedWriter successfully stopped.")
        

async def test_writer(writer:QueuedWriter):
    await writer.initialize_db()
    
    _task = asyncio.create_task(writer.start())
    
    await asyncio.sleep(5.0)
    
    await writer.stop()
    await _task


if __name__ == "__main__":
    logger = logging.getLogger("asyncio")
    logger.setLevel(logging.DEBUG)
    
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    writer = QueuedWriter(logger=logger)
    
    asyncio.run(test_writer(writer=writer))