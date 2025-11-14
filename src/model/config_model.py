from typing import Dict, Optional, Union
from ipaddress import ip_address
from pydantic import BaseModel, Field
from ipaddress import IPv4Address
from pydantic import model_validator
from pathlib import Path
import json

class AppConfig(BaseModel):
    ip: IPv4Address = Field(..., description="IPv4 address of the Modbus server")
    port: int = Field(..., gt=0, lt=65536, description="Port number")
    path: Path = Field(..., description="Path to database file")

    query_delay_ms: int = Field(1000, gt=0, description="Delay between polls in milliseconds")
    live_window_len: int = Field(120, gt=0, description="Number of data points in local deque")
    moving_average_window_len: int = Field(5, gt=0, description="Moving average window size")
    flow: float = Field(28300.0, description="Flow rate in ml/min")

    derived_metrics: bool = False
    log_enabled: bool = False
    allow_missing_path: bool = True

    @model_validator(mode="after")
    def check_path_exists(self):
        """Ensure the path exists unless allow_missing_path is True."""
        if self.path and not self.path.exists() and not self.allow_missing_path:
            raise ValueError(f"Path does not exist: {self.path}")
        return self