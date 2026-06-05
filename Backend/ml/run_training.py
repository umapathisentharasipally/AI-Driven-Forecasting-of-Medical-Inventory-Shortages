from backend.ml.src.training.train_anomaly_model import train_anomaly_model
from src.training.train_prophet import train_prophet
from src.training.train_xgboost import train_xgboost

if __name__ == "__main__":
    print("Training XGBoost...")
    print(train_xgboost())
    print("Training Prophet...")
    print(train_prophet())
    print("Training Isolation Forest...")
    print(train_anomaly_model())
