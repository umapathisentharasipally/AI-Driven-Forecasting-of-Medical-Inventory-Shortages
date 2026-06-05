from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from src.utils.exceptions import ConfigurationError
from src.utils.logger import get_logger, log_exception

logger = get_logger(__name__)


def load_yaml_config(path: str | Path, required_keys: list[str] | None = None) -> dict[str, Any]:
    """Load a YAML config file and validate required top-level keys."""
    config_path = Path(path)
    try:
        if not config_path.exists():
            raise ConfigurationError(f"Config file not found: {config_path}")
        with config_path.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
        if not isinstance(config, dict):
            raise ConfigurationError(f"Config file must contain a YAML object: {config_path}")
        missing = [key for key in (required_keys or []) if key not in config]
        if missing:
            raise ConfigurationError(f"Missing required config keys in {config_path}: {missing}")
        return config
    except ConfigurationError:
        raise
    except Exception as exc:
        log_exception(logger, f"Failed to load YAML config: {config_path}", exc)
        raise ConfigurationError(f"Failed to load YAML config: {config_path}") from exc
