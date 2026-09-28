"""
train_baselines.py
------------------
Academic Benchmark & Multi-Model Comparative Evaluation for AQI Forecasting:
1. Linear Regression (Baseline statistical trend)
2. Random Forest Regressor (Ensemble baseline)
3. LSTM (Recurrent Neural Network baseline)
4. Standard TCN (Dilated Causal Convolutions baseline)
5. TCN-HAA (Proposed Architecture: TCN with Health-Aware Attention)

Outputs:
- ml/tcn_haa_model.keras (Saved proposed model)
- ml/model_comparison_results.json
- data/processed/model_comparison_table.csv
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

import tensorflow as tf
from tensorflow.keras import Model
from tensorflow.keras.layers import (
    Input,
    Conv1D,
    BatchNormalization,
    ReLU,
    Dropout,
    GlobalAveragePooling1D,
    Dense,
    LSTM,
)
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

BASE_DIR = r"D:\AQI_Health-Risk-System"
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ml.haa_layer import HealthAwareAttention

# Set seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)

DATA_DIR = os.path.join(BASE_DIR, "ml", "data")
ML_DIR = os.path.join(BASE_DIR, "ml")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

# ── 1. Load Data ──────────────────────────────────────────────
print("=" * 60)
print("LOADING DATA FOR BENCHMARK EXPERIMENTS")
print("=" * 60)

X_train = np.load(os.path.join(DATA_DIR, "X_train.npy"))
y_train = np.load(os.path.join(DATA_DIR, "y_train.npy"))
X_test = np.load(os.path.join(DATA_DIR, "X_test.npy"))
y_test = np.load(os.path.join(DATA_DIR, "y_test.npy"))

print(f"Train samples: {X_train.shape[0]}, Sequence length: {X_train.shape[1]}, Features: {X_train.shape[2]}")
print(f"Test samples : {X_test.shape[0]}")

time_steps = X_train.shape[1]
num_features = X_train.shape[2]

# Flatten 3D tensors to 2D for scikit-learn tabular baselines
X_train_flat = X_train.reshape(X_train.shape[0], time_steps * num_features)
X_test_flat = X_test.reshape(X_test.shape[0], time_steps * num_features)

results = {}


def evaluate_model(name: str, y_true, y_pred):
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))
    print(f"[{name:20s}] MAE: {mae:.4f} | RMSE: {rmse:.4f} | R2: {r2:.4f}")
    results[name] = {
        "MAE": round(mae, 4),
        "RMSE": round(rmse, 4),
        "R2": round(r2, 4),
        "predictions": [round(float(p), 2) for p in y_pred],
    }
    return results[name]


# ── 2. Baseline 1: Linear Regression ──────────────────────────
print("\n" + "-" * 50)
print("1. Training Linear Regression Baseline...")
lr_model = LinearRegression()
lr_model.fit(X_train_flat, y_train)
lr_preds = lr_model.predict(X_test_flat)
evaluate_model("Linear Regression", y_test, lr_preds)
joblib.dump(lr_model, os.path.join(ML_DIR, "baseline_linear_regression.pkl"))


# ── 3. Baseline 2: Random Forest Regressor ─────────────────────
print("\n" + "-" * 50)
print("2. Training Random Forest Baseline...")
rf_model = RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42)
rf_model.fit(X_train_flat, y_train)
rf_preds = rf_model.predict(X_test_flat)
evaluate_model("Random Forest", y_test, rf_preds)
joblib.dump(rf_model, os.path.join(ML_DIR, "baseline_random_forest.pkl"))


# ── 4. Baseline 3: LSTM ───────────────────────────────────────
print("\n" + "-" * 50)
print("3. Training LSTM Baseline...")
lstm_inputs = Input(shape=(time_steps, num_features))
x = LSTM(64, return_sequences=True)(lstm_inputs)
x = Dropout(0.15)(x)
x = LSTM(32, return_sequences=False)(x)
x = Dropout(0.15)(x)
x = Dense(32, activation="relu")(x)
lstm_outputs = Dense(1, activation="linear")(x)

lstm_model = Model(inputs=lstm_inputs, outputs=lstm_outputs, name="LSTM_Baseline")
lstm_model.compile(optimizer=tf.keras.optimizers.Adam(0.001), loss="mse", metrics=["mae"])

callbacks = [
    EarlyStopping(monitor="val_loss", patience=20, restore_best_weights=True),
    ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=7, min_lr=1e-5),
]

lstm_model.fit(
    X_train, y_train,
    validation_split=0.2,
    epochs=120,
    batch_size=8,
    callbacks=callbacks,
    verbose=0,
)
lstm_preds = lstm_model.predict(X_test, verbose=0).flatten()
evaluate_model("LSTM", y_test, lstm_preds)
lstm_model.save(os.path.join(ML_DIR, "baseline_lstm.keras"))


# ── 5. Baseline 4: Standard TCN (No Attention) ────────────────
print("\n" + "-" * 50)
print("4. Evaluating Standard TCN Baseline...")
tcn_path = os.path.join(ML_DIR, "tcn_aqi_model.keras")
if os.path.exists(tcn_path):
    std_tcn = tf.keras.models.load_model(tcn_path)
    std_tcn_preds = std_tcn.predict(X_test, verbose=0).flatten()
    evaluate_model("Standard TCN", y_test, std_tcn_preds)
else:
    # Train fresh if not existing
    tcn_inputs = Input(shape=(time_steps, num_features))
    x = Conv1D(32, 3, padding="causal", dilation_rate=1)(tcn_inputs)
    x = BatchNormalization()(x)
    x = ReLU()(x)
    x = Dropout(0.15)(x)
    x = Conv1D(64, 3, padding="causal", dilation_rate=2)(x)
    x = BatchNormalization()(x)
    x = ReLU()(x)
    x = Dropout(0.15)(x)
    x = Conv1D(64, 3, padding="causal", dilation_rate=4)(x)
    x = BatchNormalization()(x)
    x = ReLU()(x)
    x = Dropout(0.15)(x)
    x = GlobalAveragePooling1D()(x)
    x = Dense(32, activation="relu")(x)
    x = Dropout(0.15)(x)
    tcn_outputs = Dense(1, activation="linear")(x)
    std_tcn = Model(inputs=tcn_inputs, outputs=tcn_outputs)
    std_tcn.compile(optimizer=tf.keras.optimizers.Adam(0.001), loss="mse", metrics=["mae"])
    std_tcn.fit(X_train, y_train, validation_split=0.2, epochs=150, batch_size=8, callbacks=callbacks, verbose=0)
    std_tcn_preds = std_tcn.predict(X_test, verbose=0).flatten()
    evaluate_model("Standard TCN", y_test, std_tcn_preds)


# ── 6. Proposed Architecture: TCN-HAA ─────────────────────────
print("\n" + "-" * 50)
print("5. Training Proposed TCN-HAA (with Health-Aware Attention)...")
haa_inputs = Input(shape=(time_steps, num_features), name="aqi_sequence_input")

# Dilated Causal Convolutional Blocks
x = Conv1D(filters=32, kernel_size=3, padding="causal", dilation_rate=1, name="tcn_c1")(haa_inputs)
x = BatchNormalization(name="tcn_bn1")(x)
x = ReLU(name="tcn_relu1")(x)
x = Dropout(0.15, name="tcn_drop1")(x)

x = Conv1D(filters=64, kernel_size=3, padding="causal", dilation_rate=2, name="tcn_c2")(x)
x = BatchNormalization(name="tcn_bn2")(x)
x = ReLU(name="tcn_relu2")(x)
x = Dropout(0.15, name="tcn_drop2")(x)

x = Conv1D(filters=64, kernel_size=3, padding="causal", dilation_rate=4, name="tcn_c3")(x)
x = BatchNormalization(name="tcn_bn3")(x)
x = ReLU(name="tcn_relu3")(x)
x = Dropout(0.15, name="tcn_drop3")(x)

# Health-Aware Attention Layer
haa_context = HealthAwareAttention(return_attention=False, name="health_aware_attention")(x)

x = Dense(32, activation="relu", name="dense_proj")(haa_context)
x = Dropout(0.15, name="proj_dropout")(x)
forecast_output = Dense(1, activation="linear", name="aqi_forecast")(x)

tcn_haa_model = Model(
    inputs=haa_inputs,
    outputs=forecast_output,
    name="TCN_HAA_Forecasting_System"
)

# Transfer feature-extractor weights from base TCN for stable initialization
if os.path.exists(tcn_path):
    std_model = tf.keras.models.load_model(tcn_path)
    # Transfer conv blocks
    tcn_haa_model.get_layer("tcn_c1").set_weights(std_model.layers[0].get_weights())
    tcn_haa_model.get_layer("tcn_bn1").set_weights(std_model.layers[1].get_weights())
    tcn_haa_model.get_layer("tcn_c2").set_weights(std_model.layers[4].get_weights())
    tcn_haa_model.get_layer("tcn_bn2").set_weights(std_model.layers[5].get_weights())
    tcn_haa_model.get_layer("tcn_c3").set_weights(std_model.layers[8].get_weights())
    tcn_haa_model.get_layer("tcn_bn3").set_weights(std_model.layers[9].get_weights())
    tcn_haa_model.get_layer("dense_proj").set_weights(std_model.layers[13].get_weights())
    tcn_haa_model.get_layer("aqi_forecast").set_weights(std_model.layers[15].get_weights())
    print("Transferred pretrained feature representation weights to TCN-HAA.")

tcn_haa_model.compile(
    optimizer=tf.keras.optimizers.Adam(0.0003),
    loss="mse",
    metrics=["mae"]
)

# Train with fine-tuning on health attention
haa_callbacks = [
    EarlyStopping(monitor="val_loss", patience=25, restore_best_weights=True),
    ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=8, min_lr=1e-5),
]

tcn_haa_model.fit(
    X_train, y_train,
    validation_split=0.2,
    epochs=100,
    batch_size=8,
    callbacks=haa_callbacks,
    verbose=0,
)

tcn_haa_preds = tcn_haa_model.predict(X_test, verbose=0).flatten()
evaluate_model("TCN-HAA (Proposed)", y_test, tcn_haa_preds)

# Save the primary TCN-HAA model
tcn_haa_path = os.path.join(ML_DIR, "tcn_haa_model.keras")
tcn_haa_model.save(tcn_haa_path)
print(f"\nSaved TCN-HAA model to: {tcn_haa_path}")


# ── 7. Generate Comparison Table ──────────────────────────────
print("\n" + "=" * 60)
print("FINAL BENCHMARK COMPARISON TABLE")
print("=" * 60)

comparison_rows = []
for model_name, metrics in results.items():
    comparison_rows.append({
        "Model": model_name,
        "MAE": metrics["MAE"],
        "RMSE": metrics["RMSE"],
        "R2_Score": metrics["R2"],
    })

comparison_df = pd.DataFrame(comparison_rows).sort_values("MAE")
print(comparison_df.to_string(index=False))

csv_path = os.path.join(PROCESSED_DIR, "model_comparison_table.csv")
comparison_df.to_csv(csv_path, index=False)
print(f"\nSaved comparison CSV to: {csv_path}")

json_path = os.path.join(ML_DIR, "model_comparison_results.json")
with open(json_path, "w") as f:
    json.dump({
        "ground_truth": [round(float(y), 2) for y in y_test],
        "models": results,
    }, f, indent=2)
print(f"Saved comparison JSON to: {json_path}")
print("\nAll models successfully trained and evaluated!")
