"""
Model Training - FIXED VERSION
==============================
Trains a well-regularized model for efficiency prediction.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import joblib
import os
from pathlib import Path


def train_model(dataset_path: str = "dataset/dataset.csv",
                model_path: str = "models/efficiency_model.pkl",
                scaler_path: str = "models/scaler.pkl"):
    """Train efficiency prediction model."""
    
    print("=" * 60)
    print("    Training Efficiency Prediction Model")
    print("=" * 60)
    
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset not found: {dataset_path}")
        print("Run: python generate_dataset.py")
        return None
    
    print(f"\n📂 Loading {dataset_path}...")
    df = pd.read_csv(dataset_path)
    print(f"   {len(df)} samples loaded")
    
    # Features and target
    features = ['servers', 'workload', 'cpu', 'energy', 'temperature']
    X = df[features].values
    y = df['efficiency'].values
    
    print(f"\n📊 Features: {features}")
    print(f"   Target: efficiency (range: {y.min():.1f} - {y.max():.1f})")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"\n📐 Train: {len(X_train)} | Test: {len(X_test)}")
    
    # Scale features
    print("\n⚖️ Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train model with proper regularization
    print("\n🌲 Training RandomForest...")
    print("   Parameters:")
    print("   - n_estimators: 150")
    print("   - max_depth: 12")
    print("   - min_samples_split: 10")
    print("   - min_samples_leaf: 5")
    
    model = RandomForestRegressor(
        n_estimators=150,
        max_depth=12,
        min_samples_split=10,
        min_samples_leaf=5,
        max_features='sqrt',
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train_scaled, y_train)
    print("   ✅ Training complete!")
    
    # Cross-validation
    print("\n🔄 Cross-validation (5-fold)...")
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='r2')
    print(f"   CV R² scores: {cv_scores.round(3)}")
    print(f"   CV R² mean: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
    
    # Evaluate
    print("\n📈 Evaluation:")
    
    y_train_pred = model.predict(X_train_scaled)
    y_test_pred = model.predict(X_test_scaled)
    
    print(f"\n   Training Set:")
    print(f"   - R²: {r2_score(y_train, y_train_pred):.4f}")
    print(f"   - MAE: {mean_absolute_error(y_train, y_train_pred):.4f}")
    
    print(f"\n   Test Set:")
    print(f"   - R²: {r2_score(y_test, y_test_pred):.4f}")
    print(f"   - MAE: {mean_absolute_error(y_test, y_test_pred):.4f}")
    print(f"   - RMSE: {np.sqrt(mean_squared_error(y_test, y_test_pred)):.4f}")
    
    # Feature importance
    print("\n🔍 Feature Importance:")
    for name, importance in sorted(zip(features, model.feature_importances_), 
                                    key=lambda x: -x[1]):
        bar = "█" * int(importance * 40)
        print(f"   {name:12}: {importance:.3f} {bar}")
    
    # Save model
    Path(os.path.dirname(model_path)).mkdir(parents=True, exist_ok=True)
    
    print(f"\n💾 Saving model to {model_path}")
    joblib.dump(model, model_path)
    
    print(f"💾 Saving scaler to {scaler_path}")
    joblib.dump(scaler, scaler_path)
    
    print("\n" + "=" * 60)
    print("    ✅ Model Training Complete!")
    print("=" * 60)
    
    return model, scaler


if __name__ == "__main__":
    train_model()