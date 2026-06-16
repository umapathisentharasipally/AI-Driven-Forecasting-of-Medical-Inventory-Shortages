from __future__ import annotations
import argparse
from src.inference.detect_anomalies import detect_anomalies
from src.inference.predict_stockout import predict_stockout


def run_batch_prediction(input_path: str, output_path: str):
    predictions = predict_stockout(input_path=input_path, output_path=output_path)
    try:
        detect_anomalies(input_path=input_path)
    except FileNotFoundError:
        pass
    return predictions


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/raw/medical_inventory.csv")
    parser.add_argument("--output", default="data/predictions/prediction_results.csv")
    args = parser.parse_args()
    run_batch_prediction(args.input, args.output)
    print(f"Batch predictions saved to {args.output}")
