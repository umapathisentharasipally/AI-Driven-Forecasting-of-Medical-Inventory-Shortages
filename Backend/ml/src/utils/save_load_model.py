from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from src.utils.exceptions import ArtifactError
from src.utils.logger import get_logger, log_exception

logger = get_logger(__name__)


def save_object(obj: Any, path: str | Path) -> None:
    """Persist Python objects such as sklearn pipelines and models."""
    artifact_path = Path(path)
    try:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(obj, artifact_path)
        logger.info("Saved artifact: %s", artifact_path)
    except Exception as exc:
        log_exception(logger, f"Failed to save artifact: {artifact_path}", exc)
        raise ArtifactError(f"Failed to save artifact: {artifact_path}") from exc


def load_object(path: str | Path) -> Any:
    """Load a persisted Python object with clear error reporting."""
    artifact_path = Path(path)
    try:
        if not artifact_path.exists():
            raise ArtifactError(f"Artifact not found: {artifact_path}")
        obj = joblib.load(artifact_path)
        logger.info("Loaded artifact: %s", artifact_path)
        return obj
    except ArtifactError:
        raise
    except Exception as exc:
        log_exception(logger, f"Failed to load artifact: {artifact_path}", exc)
        raise ArtifactError(f"Failed to load artifact: {artifact_path}") from exc
