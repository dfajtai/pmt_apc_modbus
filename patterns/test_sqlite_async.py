
import asyncio
import logging
import sys

import datetime
import time
import random

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import Integer, Column, DateTime, text
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
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

async def simple_sqlite_test(logger:logging.Logger, task:str = ""):
    url = "sqlite+aiosqlite:///test_db.db"

    logger.debug(f"[T{task}] Creating async engine")
    engine = create_async_engine(
        url,
        echo=False,               # SQL log
        connect_args={"check_same_thread": False, "timeout": 30},
        poolclass=StaticPool,    # or NullPool for testing
    )
    logger.debug(f"[T{task}]Async engine created")

    logger.debug(f"[T{task}]Connecting, initializing")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.debug(f"[T{task}]Initialized")

    logger.debug(f"[T{task}]Insert test data")
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as s:
        obj = S()
        s.add(obj)
        logger.debug(f"[T{task}]Before commit")
        await s.commit()
        logger.debug(f"[T{task}]After commit")
        await s.refresh(obj)
        logger.debug(f"[T{task}]Object refreshed")


    logger.debug(f"[T{task}]Insert success")

    logger.debug(f"[T{task}]Disposing engine")
    await engine.dispose()
    logger.debug(f"[T{task}]Engine disposed")


async def sqlite_test_in_task(logger: logging.Logger):
    # re-test
    # await simple_sqlite_test() # still working

    # exits with no error or anything
    # logger.debug("Creating task")
    # asyncio.create_task(simple_sqlite_test(logger=logger))
    # logger.debug("Task done")

    # seems like it is working...?
    logger.debug("Creating task")
    t1 =  asyncio.create_task(simple_sqlite_test(logger=logger, task = "1"))
    t2 =  asyncio.create_task(simple_sqlite_test(logger=logger, task = "2"))

    # asyncio.gather(t1,t2) # not working
    await asyncio.gather(t1,t2) # working

    # equal to "await asyncio.gather(t1,t2)" ?!
    # await t1
    # await t2

    logger.debug("Task done")

    return True


def _thread(logger:logging.Logger):
    try:
        logger.debug("Thread based approach ...")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(sqlite_test_in_task(logger=logger))
    except Exception as e:
        logger.error(e)
        raise Exception from e
    


def simple_run_test(logger:logging.Logger):
    # asyncio.run(simple_sqlite_test(logger=logger)) # -> working
    asyncio.run(sqlite_test_in_task(logger = logger),debug=True) # -> Somewhat working?


def run_test_on_thread(logger:logging.Logger):
    # without threading -> working
    # _thread(logger=logger)

    # on a new thread
    thread = threading.Thread(target = _thread, args = (logger,), daemon=False)
    logger.debug("Starting thread")
    thread.start()
    logger.debug("Thread started")
    
    thread.join()
    logger.debug("Thread finished")


# WITH INTERRUPT

async def simple_sqlite_test_with_interrupt(logger:logging.Logger, event:asyncio.Event, task:str = ""):
    url = "sqlite+aiosqlite:///test_db.db"

    logger.debug(f"[T{task}] Creating async engine")
    engine = create_async_engine(
        url,
        echo=False,               # SQL log
        connect_args={"check_same_thread": False, "timeout": 30},
        poolclass=StaticPool,    # or NullPool for testing
    )
    logger.debug(f"[T{task}]Async engine created")

    logger.debug(f"[T{task}]Connecting, initializing")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.debug(f"[T{task}]Initialized")

    logger.debug(f"[T{task}]Insert test data")
    Session = async_sessionmaker(engine, expire_on_commit=False)

    start = time.monotonic()
    next_time = start

    while not event.is_set():
        next_time = next_time + 1.0

        async with Session() as s:
            obj = S()
            s.add(obj)
            logger.debug(f"[T{task}]Before commit")
            await s.commit()
            logger.debug(f"[T{task}]After commit")
            await s.refresh(obj)
            logger.debug(f"[T{task}]Object refreshed: {obj.timestamp}")
    
        delay = next_time - time.monotonic()
        if delay > 0:
            await asyncio.sleep(delay)

    logger.debug(f"[T{task}]Insert success")

    logger.debug(f"[T{task}]Disposing engine")
    await engine.dispose()
    logger.debug(f"[T{task}]Engine disposed")

    return True

async def dummy_interrupt(logger:logging.Logger, event:asyncio.Event, task:str = ""):
    i = 0
    while True:
        rnd = random.random()
        i+=1
        if  rnd > 0.995:
            logger.debug(f"[T{task}]Dummy interrup initiated in {i} steps.")
            event.set()
            break

        if event.is_set():
            break
        
        await asyncio.sleep(.1)

    return True

async def sqlite_test_in_task_with_interrupt(logger: logging.Logger, event:asyncio.Event):

    logger.debug("Creating task")
    t1 =  asyncio.create_task(simple_sqlite_test_with_interrupt(logger=logger, task = "1", event = event))
    t2 =  asyncio.create_task(dummy_interrupt(logger=logger, task = "2", event = event))
    

    await asyncio.gather(t1,t2)

    logger.debug("Task done")

    return True


def _thread_with_interrupt(logger:logging.Logger, event:asyncio.Event):
    try:
        logger.debug("Thread based approach ...")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(sqlite_test_in_task_with_interrupt(logger=logger, event = event))
    except Exception as e:
        logger.error(e)
        raise Exception from e



def run_test_on_thread_with_internal_interrupt(logger:logging.Logger):
    stop_event = asyncio.Event()


    start = time.monotonic()

    thread = threading.Thread(target = _thread_with_interrupt, args = (logger,stop_event,), daemon=False)
    logger.debug("Starting thread")
    thread.start()
    logger.debug("Thread started")

    while True:
        time.sleep(1)
        if (time.monotonic()-start > 20) or stop_event.is_set():
            break
    
    stop_event.set()

    thread.join()
    logger.debug("Thread finished")

if __name__ == "__main__":
    logger = logging.getLogger("asyncio")
    logger.setLevel(logging.DEBUG)
    
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # simple_run_test(logger = logger)

    # run_test_on_thread(logger = logger)

    run_test_on_thread_with_internal_interrupt(logger=logger)