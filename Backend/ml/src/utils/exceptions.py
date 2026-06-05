from __future__ import annotations


class MLProjectError(Exception):
    """Base exception for the medical inventory ML project."""


class ConfigurationError(MLProjectError):
    """Raised when configuration files are missing, invalid, or incomplete."""


class DataLoadError(MLProjectError):
    """Raised when input data cannot be loaded."""


class DataValidationError(MLProjectError):
    """Raised when the dataset schema or values are invalid."""


class FeatureEngineeringError(MLProjectError):
    """Raised when feature generation fails."""


class ModelTrainingError(MLProjectError):
    """Raised when model training fails."""


class ModelInferenceError(MLProjectError):
    """Raised when batch or real-time inference fails."""


class ArtifactError(MLProjectError):
    """Raised when model artifacts cannot be saved or loaded."""


class MonitoringError(MLProjectError):
    """Raised when monitoring or drift calculations fail."""
