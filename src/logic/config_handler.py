from __future__ import annotations
from typing import Union, Optional, Dict
from pathlib import Path
import json
import logging

from model.config_model import AppConfig


class AppConfigHandler:

    def __init__(self, config_path: Union[str, Path],
                 auto_initialize_if_missing:bool = True,
                 logger: Optional[logging.Logger] = None):
        
        self.config_path = Path(config_path)
        self.auto_initialize_if_missing = auto_initialize_if_missing
        self.config: Optional[AppConfig] = None
        self.logger: Optional[logging.Logger] = logger

    # --- Core operations ---

    def load_from_json(self) -> AppConfig:
        """Load configuration from JSON and merge with defaults."""
        if not self.config_path.exists():
            if self.auto_initialize_if_missing:
                self.initialize_defaults()
                return self.config
            else:
                raise FileNotFoundError(f"Config file not found: {self.config_path}")
        else:
            with self.config_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            merged = {**AppConfig.DEFAULTS, **data}
            self.config = AppConfig.model_validate(merged)

            if self.logger:
                self.logger.info("Config successfully loaded.")
        return self.config

    def save_to_json(self) -> None:
        """Save current configuration to disk."""
        if self.config is None:
            raise ValueError("No configuration loaded to save.")
        with self.config_path.open("w", encoding="utf-8") as f:
            f.write(self.to_json())

    # --- Helpers ---

    def initialize_defaults(self) -> AppConfig:
        """Initialize configuration with default values."""
        self.config = AppConfig.model_validate(AppConfig.DEFAULTS)
        if self.logger:
            self.logger.info("Config initialized form defaults.")
        return self.config

    def update_from_dict(self, updates: Dict[str, Union[str, int, float, bool]]):
        """Update configuration with given dictionary."""
        if self.config is None:
            raise ValueError("Config not loaded yet.")
        updated = self.config.model_copy(update=updates)
        self.config = AppConfig.model_validate(updated.model_dump())

    def to_json(self) -> str:
        """Return the current config as a JSON string."""
        if self.config is None:
            raise ValueError("Config not loaded yet.")
        return self.config.model_dump_json(indent=4)

    def initialize_if_missing(self) -> AppConfig:
        """Ensure config exists and has all required fields."""
        if self.config is None:
            self.initialize_defaults()
            self.save_to_json()
            return self.config

        updated_fields = {}
        for key, default in AppConfig.DEFAULTS.items():
            if getattr(self.config, key, None) in (None, "", 0):
                updated_fields[key] = default

        if updated_fields:
            self.update_from_dict(updated_fields)
            self.save_to_json()

        return self.config
