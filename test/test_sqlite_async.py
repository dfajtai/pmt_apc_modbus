
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import Integer, Column, DateTime, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool

Base = declarative_base()

class S(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    start = Column(DateTime, nullable=True)

async def main():
    url = "sqlite+aiosqlite:///./test_db.sqlite"
    engine = create_async_engine(
        url,
        echo=True,               # SQL log
        connect_args={"check_same_thread": False, "timeout": 30},
        poolclass=StaticPool,    # vagy NullPool teszthez
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as s:
        obj = S()
        s.add(obj)
        print("Before commit")
        await s.commit()
        print("After commit")
        await s.refresh(obj)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
