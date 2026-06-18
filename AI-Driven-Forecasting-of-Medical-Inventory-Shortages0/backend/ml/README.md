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
