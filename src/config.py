"""Configuration loading and validation."""
import json
import os
from dataclasses import dataclass


class ConfigError(Exception):
    """Raised when config.json contains invalid values."""


@dataclass
class Config:
    interface: str = "auto"
    interval_seconds: float = 1.0
    warning_mbps: float = 5.0
    critical_mbps: float = 20.0
    warning_utilization_percent: float = 70.0
    critical_utilization_percent: float = 90.0
    history_file: str = "logs/bandwidth_history.csv"
    alert_file: str = "logs/alerts.log"
    recent_events_shown: int = 6

    def validate(self):
        if self.interval_seconds <= 0:
            raise ConfigError("interval_seconds must be greater than 0.")
        if not 0 < self.warning_mbps < self.critical_mbps:
            raise ConfigError("Need 0 < warning_mbps < critical_mbps.")
        if not 0 < self.warning_utilization_percent < self.critical_utilization_percent <= 100:
            raise ConfigError("Need 0 < warning_utilization_percent < critical_utilization_percent <= 100.")


def load_config(path, overrides=None):
    """Load config.json (falling back to defaults) and apply CLI overrides."""
    values = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                values = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            raise ConfigError(f"Cannot read {path}: {exc}")
    known = Config.__dataclass_fields__
    cfg = Config(**{k: v for k, v in values.items() if k in known})
    for key, val in (overrides or {}).items():
        if val is not None:
            setattr(cfg, key, val)
    cfg.validate()
    return cfg
