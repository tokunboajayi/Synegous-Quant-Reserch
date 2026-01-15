import argparse
import numpy as np
import polars as pl
import pandas as pd
from pathlib import Path

from nmie.config import DATA_DIR
from nmie.store.feature_store import FeatureStore
from nmie.features.microstructure import compute_features, aggregate_features_for_order
from nmie.models.impact_transformer import ImpactPredictor, ModelConfig

def prepare_training_data(labels_path: Path, bars_dir: Path):
    """
    Loads labels and builds training dataset.
    """
    labels_df = pl.read_parquet(labels_path)
    
    X_list = []
    y_list = []
    
    store = FeatureStore()
    
    for row in labels_df.iter_rows(named=True):
        date = row["date"]
        ticker = row["ticker"]
        
        # Load bars for date
        bars = store.load_bars(ticker, date)
        if bars.is_empty():
            continue
            
        # Compute features
        features = compute_features(bars)
        
        # Get order horizon
        # We'll use a fixed window of features as input sequence
        # For simplicity, use first 20 bars of the day as context
        # In production, would align to order start time
        
        if features.height < 20:
            continue
            
        # Extract feature columns
        feat_cols = ["rolling_spread", "rolling_volatility", "volume_imbalance",
                     "vwap_deviation", "time_sin", "time_cos"]
        
        # Handle missing columns
        available = [c for c in feat_cols if c in features.columns]
        
        feat_matrix = features.head(20).select(available).to_numpy()
        
        # Pad if needed
        if feat_matrix.shape[1] < 6:
            pad = np.zeros((20, 6 - feat_matrix.shape[1]))
            feat_matrix = np.hstack([feat_matrix, pad])
            
        X_list.append(feat_matrix)
        y_list.append(row["is_bps"])
        
    if len(X_list) == 0:
        return None, None
        
    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.float32)
    
    return X, y

def main():
    parser = argparse.ArgumentParser(description="Train Impact Transformer model")
    parser.add_argument("--labels", type=str, required=True, help="Path to labels parquet")
    parser.add_argument("--epochs", type=int, default=50, help="Training epochs")
    parser.add_argument("--output", type=str, default="models/impact_transformer.pt")
    
    args = parser.parse_args()
    
    labels_path = Path(args.labels)
    if not labels_path.exists():
        print(f"Labels file not found: {labels_path}")
        return
        
    print("Preparing training data...")
    X, y = prepare_training_data(labels_path, DATA_DIR / "raw/bars")
    
    if X is None:
        print("No training data generated")
        return
        
    print(f"Training data: X={X.shape}, y={y.shape}")
    print(f"IS range: [{y.min():.2f}, {y.max():.2f}] bps")
    
    # Configure model
    config = ModelConfig(
        input_dim=X.shape[2],
        d_model=32,
        n_heads=2,
        n_layers=2,
        quantiles=[0.5, 0.9, 0.95]
    )
    
    predictor = ImpactPredictor(config)
    
    print(f"\nTraining for {args.epochs} epochs...")
    losses = predictor.train(X, y, epochs=args.epochs, batch_size=8, lr=1e-3)
    
    # Test prediction
    preds = predictor.predict(X[:5])
    print(f"\nSample predictions (p50, p90, p95):")
    for i in range(5):
        print(f"  [{i}] True: {y[i]:.2f} | Pred: {preds[i]}")
        
    # Save
    output_path = DATA_DIR / args.output
    output_path.parent.mkdir(exist_ok=True)
    predictor.save(str(output_path))
    print(f"\nModel saved to {output_path}")

if __name__ == "__main__":
    main()
