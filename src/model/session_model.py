from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, DateTime
from sqlalchemy.ext.asyncio import AsyncAttrs

import datetime

from model.database_model import Base


class SamplingSession(Base, AsyncAttrs):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    start: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True, index=True)
    end: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True, index=True)
    number_of_samples: Mapped[int] = mapped_column(Integer, default = 0, nullable= True)


    def __str__(self):
        return (f"SESSION #{self.id}:\t"
                f"STARTED @{self.start}\t|\tENDED @{self.end}\t|\tN = {self.number_of_samples}")