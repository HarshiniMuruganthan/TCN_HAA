"""
compare_models.py
-----------------
Generates research-grade visualization figures for model benchmarking:
1. Model Comparison Bar Chart (MAE, RMSE, R²) across all 5 models
2. Actual vs. Predicted Curve for TCN-HAA
3. Attention Distribution Heatmap across the 7-day receptive field
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import tensorflow as tf

import sys

BASE_DIR = r"D:\AQI_Health-Risk-System"
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ml.haa_layer import HealthAwareAttention
DATA_DIR = os.path.join(BASE_DIR, "ml", "data")
ML_DIR = os.path.join(BASE_DIR, "ml")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

# Set aesthetic styling
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#cccccc"
plt.rcParams["axes.linewidth"] = 0.8

# Load comparison results
json_path = os.path.join(ML_DIR, "model_comparison_results.json")
if not os.path.exists(json_path):
    print(f"Error: {json_path} does not exist. Run train_baselines.py first.")
    exit(1)

with open(json_path, "r") as f:
    data = json.load(f)

models = data["models"]
model_names = list(models.keys())
mae_vals = [models[m]["MAE"] for m in model_names]
rmse_vals = [models[m]["RMSE"] for m in model_names]
r2_vals = [models[m]["R2"] for m in model_names]
ground_truth = np.array(data["ground_truth"])

# ── Chart 1: Multi-Metric Benchmark Comparison ─────────────────
print("Generating Chart 1: Model Benchmark Metrics Comparison...")
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle("AQI Forecasting Model Benchmark Comparison", fontsize=15, weight="bold", y=1.03)

colors = ["#4A90E2", "#50E3C2", "#F5A623", "#9013FE", "#E91E63"]

# MAE
bars1 = axes[0].bar(model_names, mae_vals, color=colors, alpha=0.9, edgecolor="#333333", linewidth=1)
axes[0].set_title("Mean Absolute Error (MAE) ↓", fontsize=12, weight="bold")
axes[0].set_ylabel("AQI Units")
axes[0].tick_params(axis="x", rotation=30)
for bar in bars1:
    yval = bar.get_height()
    axes[0].text(bar.get_x() + bar.get_width()/2, yval + 0.1, f"{yval:.2f}", ha="center", va="bottom", fontsize=10, weight="bold")

# RMSE
bars2 = axes[1].bar(model_names, rmse_vals, color=colors, alpha=0.9, edgecolor="#333333", linewidth=1)
axes[1].set_title("Root Mean Squared Error (RMSE) ↓", fontsize=12, weight="bold")
axes[1].set_ylabel("AQI Units")
axes[1].tick_params(axis="x", rotation=30)
for bar in bars2:
    yval = bar.get_height()
    axes[1].text(bar.get_x() + bar.get_width()/2, yval + 0.1, f"{yval:.2f}", ha="center", va="bottom", fontsize=10, weight="bold")

# R2 Score
bars3 = axes[2].bar(model_names, r2_vals, color=colors, alpha=0.9, edgecolor="#333333", linewidth=1)
axes[2].set_title("Goodness of Fit (R² Score) ↑", fontsize=12, weight="bold")
axes[2].set_ylabel("R²")
axes[2].set_ylim([0, 1.05])
axes[2].tick_params(axis="x", rotation=30)
for bar in bars3:
    yval = bar.get_height()
    axes[2].text(bar.get_x() + bar.get_width()/2, yval + 0.02, f"{yval:.3f}", ha="center", va="bottom", fontsize=10, weight="bold")

plt.tight_layout()
chart1_path = os.path.join(PROCESSED_DIR, "model_comparison.png")
fig.savefig(chart1_path, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {chart1_path}")


# ── Chart 2: Actual vs Predicted (TCN-HAA) ─────────────────────
print("Generating Chart 2: Actual vs Predicted AQI for TCN-HAA...")
tcn_haa_preds = np.array(models.get("TCN-HAA (Proposed)", {}).get("predictions", []))

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(ground_truth, label="Ground Truth AQI", color="#111827", linewidth=2.2, marker="o", markersize=6)
if len(tcn_haa_preds) > 0:
    ax.plot(tcn_haa_preds, label="TCN-HAA Forecast", color="#E11D48", linewidth=2.0, linestyle="--", marker="s", markersize=6)
if "Standard TCN" in models:
    std_preds = np.array(models["Standard TCN"]["predictions"])
    ax.plot(std_preds, label="Standard TCN Forecast", color="#3B82F6", linewidth=1.5, linestyle=":", marker="^", markersize=5, alpha=0.7)

ax.set_title("AQI Forecasting: Ground Truth vs. Deep Learning Models (Test Set)", fontsize=13, weight="bold")
ax.set_xlabel("Test Samples (Chronological Time Windows)", fontsize=11)
ax.set_ylabel("AQI Value", fontsize=11)
ax.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="#e2e8f0")
ax.grid(True, linestyle="--", alpha=0.5)

chart2_path = os.path.join(PROCESSED_DIR, "tcn_haa_actual_vs_predicted.png")
fig.savefig(chart2_path, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"Saved: {chart2_path}")


# ── Chart 3: Temporal Attention Weight Heatmap ─────────────────
print("Generating Chart 3: Health-Aware Attention Weight Distribution...")
model_path = os.path.join(ML_DIR, "tcn_haa_model.keras")
if os.path.exists(model_path):
    try:
        model = tf.keras.models.load_model(
            model_path,
            custom_objects={"HealthAwareAttention": HealthAwareAttention}
        )
        X_test = np.load(os.path.join(DATA_DIR, "X_test.npy"))
        attn_layer = model.get_layer("health_aware_attention")
        conv_out_model = tf.keras.Model(inputs=model.input, outputs=model.get_layer("tcn_drop3").output)
        conv_feats = conv_out_model.predict(X_test, verbose=0)
        score_proj = np.tanh(np.dot(conv_feats, attn_layer.W_a.numpy()) + attn_layer.b_a.numpy())
        scores = np.dot(score_proj, attn_layer.u_h.numpy())
        exp_s = np.exp(scores - np.max(scores, axis=1, keepdims=True))
        attn_matrix = np.squeeze(exp_s / np.sum(exp_s, axis=1, keepdims=True))

        fig, ax = plt.subplots(figsize=(10, 6))
        days = [f"t-{6-i}d" if 6-i > 0 else "Today (t)" for i in range(7)]
        cax = ax.imshow(attn_matrix[:15], aspect="auto", cmap="YlOrRd", interpolation="nearest")

        ax.set_xticks(range(7))
        ax.set_xticklabels(days, fontsize=10, weight="bold")
        ax.set_ylabel("Test Sequence Index", fontsize=11)
        ax.set_xlabel("Receptive Field Time Steps", fontsize=11)
        ax.set_title("Health-Aware Attention (HAA) Weight Distribution Over 7-Day Window", fontsize=12, weight="bold")

        cbar = fig.colorbar(cax, orientation="vertical")
        cbar.set_label("Attention Probability α_t", fontsize=10)

        chart3_path = os.path.join(PROCESSED_DIR, "tcn_haa_attention_weights.png")
        fig.savefig(chart3_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved: {chart3_path}")
    except Exception as e:
        print(f"Could not generate attention heatmap: {e}")

print("All charts successfully generated!")
