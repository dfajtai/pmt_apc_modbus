from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Float

from model.sample_model import BaseSample



class APCSample(BaseSample):
    __tablename__ = "apc_samples"

    pc1: Mapped[float] = mapped_column(Float)
    pc2: Mapped[float] = mapped_column(Float)
    pc3: Mapped[float] = mapped_column(Float)

    @staticmethod
    def from_dict(dictionary: dict) -> "APCSample":
        return APCSample(
            instrument_unix_timestamp=dictionary.get("timestamp", 0),
            pc1=dictionary.get("pc1"),
            pc2=dictionary.get("pc2"),
            pc3=dictionary.get("pc3"),
        )

    
    def __str__(self):
        return (f"{self.instrument_datetime}:\t"
                f"pc1 = {self.pc1}\t|\tpc2 = {self.pc2}\t|\tpc3 = {self.pc3}")