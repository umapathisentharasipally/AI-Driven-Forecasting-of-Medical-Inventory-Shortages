# Medical Inventory ML Production Codebase

This package converts the notebook workflow into production-style Python modules for stockout prediction, demand forecasting, LSTM forecasting, anomaly detection, and business risk scoring.

## Expected input
Place the dataset here:

```text
data/raw/medical_inventory.csv
```

The target column is `stockout_event` and the main date column is `snapshot_date`.

## Train models

```bash
python -m src.training.train_xgboost
python -m src.training.train_prophet
python -m src.training.train_anomaly_model
python -m src.training.train_lstm
```

## Run inference

```bash
python -m src.inference.batch_predict --input data/raw/medical_inventory.csv --output data/predictions/prediction_results.csv
```

## Realtime prediction

```python
from src.inference.realtime_predict import RealtimeStockoutPredictor
predictor = RealtimeStockoutPredictor()
result = predictor.predict_one(record)
```

## Production Additions

### Monitoring
- `src/monitoring/data_drift.py` compares baseline processed training data with current incoming data and writes `artifacts/data_drift_report.json`.
- `src/monitoring/model_drift.py` evaluates the saved XGBoost model on labeled current data and writes `artifacts/model_drift_report.json`.
- `src/monitoring/prediction_monitor.py` summarizes generated predictions and writes `artifacts/prediction_monitor_report.json`.

### Pipelines
- `src/pipelines/training_pipeline.py` runs XGBoost training, anomaly model training, and Prophet forecasting together.
- `src/pipelines/forecast_pipeline.py` runs demand forecasting with Prophet and optionally LSTM.
- `src/pipelines/anomaly_pipeline.py` trains Isolation Forest and generates anomaly results.

### Dataset name
Place your file here:

```text
data/raw/healthcare_supply_chain_01.csv
```

### Main commands

```bash
python -m src.pipelines.training_pipeline
python -m src.inference.batch_predict --input data/raw/healthcare_supply_chain_01.csv
python -m src.monitoring.data_drift
python -m src.monitoring.model_drift
python -m src.monitoring.prediction_monitor
```

## Exception Handling and Logging

This version includes production-style exception handling and logging.

### What was added

- `src/utils/exceptions.py` centralizes project-specific exceptions.
- `src/utils/logger.py` writes logs to both terminal and `logs/ml_pipeline.log` using rotating log files.
- `src/utils/config.py` validates YAML config loading.
- `src/utils/error_handler.py` provides a reusable decorator for pipeline-level error handling.
- Data loading, validation, cleaning, feature engineering, training, inference, monitoring, and pipelines now log start/completion/failure details.

### Log location

```bash
logs/ml_pipeline.log
```

### Example run

```bash
python -m src.pipelines.training_pipeline
python -m src.inference.batch_predict
python -m src.monitoring.prediction_monitor
```

If an error happens, the terminal shows a clean message and the full stack trace is written to the log file.
