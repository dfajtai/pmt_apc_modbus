from typing import Optional
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, DateTime, ForeignKey
import datetime

from model.database_model import Base

class BaseSample(Base, AsyncAttrs):
    __abstract__ = True  # Absztrakt osztály, nem hoz létre saját táblát

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    session_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sessions.id"), nullable=False, index=True)

    local_datetime: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        index=True,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    local_unix_timestamp: Mapped[int] = mapped_column(
        Integer,
        index=False,
        default=lambda: int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    )
    instrument_unix_timestamp: Mapped[int] = mapped_column(Integer, index=True)

    @property
    def instrument_datetime(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self.instrument_unix_timestamp, datetime.timezone.utc)
    
    @property
    def is_valid(self)->bool:
        print()
        return abs(datetime.datetime.now(datetime.timezone.utc).timestamp() - self.instrument_unix_timestamp) < (24*3600.0)