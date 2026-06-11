from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "configs"
ARTIFACT_DIR = PROJECT_ROOT / "artifacts"
LOG_DIR = PROJECT_ROOT / "logs"

TARGET_COLUMN = "stockout_event"
DATE_COLUMN = "snapshot_date"
ID_COLUMNS = ["record_id", "item_id", "facility_id"]

RAW_DATA_PATH = DATA_DIR / "raw" / "medical_inventory.csv"
PROCESSED_DATA_PATH = DATA_DIR / "processed" / "processed_inventory.csv"
PREDICTION_OUTPUT_PATH = DATA_DIR / "predictions" / "prediction_results.csv"
FORECAST_OUTPUT_PATH = DATA_DIR / "forecasts" / "demand_forecast.csv"
ANOMALY_OUTPUT_PATH = DATA_DIR / "anomalies" / "anomaly_results.csv"
