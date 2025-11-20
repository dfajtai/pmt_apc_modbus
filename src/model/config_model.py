from typing import Dict, Optional, Union, ClassVar
from ipaddress import ip_address
from pydantic import BaseModel, Field
from ipaddress import IPv4Address
from pydantic import model_validator
from pathlib import Path
import json

class AppConfig(BaseModel):
    DEFAULTS: ClassVar[Dict] = {
        "ip": "10.10.7.60",
        "port": 1502,
        "db_path": "./records.db",

        "sampling_time": 1800,
        "sampling_step": 1000,

        "timeout": 100,

        "live_window_len": 120,
        "moving_average_window_len": 5,

        "flow": 28300.0,

        # "derived_metrics": False,
        # "log_enabled": True,

        "allow_missing_path": True,
    }

    ip: IPv4Address = Field(..., description="IPv4 address of the Modbus server")
    port: int = Field(..., gt=0, lt=65536, description="Port number")
    db_path: Path = Field(..., description="Path to database file")

    sampling_time: int = Field(1800, gt = 0, description = "Sampling time in seconds.")
    sampling_step: int = Field(1000, gt=0, description="Delay between polls in milliseconds.")


    timeout: int = Field(100,gt=0,description = "MODBUS async timeout in milliseconds.")
    
    live_window_len: int = Field(120, gt=0, description="Number of data points in local deque.")
    moving_average_window_len: int = Field(5, gt=0, description="Moving average window size.")
    
    flow: float = Field(28300.0, description="Flow rate in ml/min.")

    # derived_metrics: bool = False
    # log_enabled: bool = True
    allow_missing_path: bool = True

    @model_validator(mode="after")
    def check_path_exists(self):
        """Ensure the path exists unless allow_missing_path is True."""
        if self.db_path and not self.db_path.exists() and not self.allow_missing_path:
            raise ValueError(f"Path does not exist: {self.db_path}")
        return self