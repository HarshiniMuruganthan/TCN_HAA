import os
import numpy as np
import matplotlib.pyplot as plt

from tensorflow.keras.models import load_model
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# ============================================================
# PATHS
# ============================================================

BASE_DIR = r"D:\AQI_Health-Risk-System"
DATA_DIR = os.path.join(BASE_DIR, "ml", "data")
MODEL_PATH = os.path.join(BASE_DIR, "ml", "tcn_aqi_model.keras")

OUTPUT_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "tcn_actual_vs_predicted.png"
)


# ============================================================
# LOAD TEST DATA
# ============================================================

print("=" * 60)
print("LOADING TEST DATA")
print("=" * 60)

X_test = np.load(os.path.join(DATA_DIR, "X_test.npy"))
y_test = np.load(os.path.join(DATA_DIR, "y_test.npy"))

print("X_test:", X_test.shape)
print("y_test:", y_test.shape)


# ============================================================
# LOAD MODEL
# ============================================================

print("\n" + "=" * 60)
print("LOADING TCN MODEL")
print("=" * 60)

model = load_model(MODEL_PATH)

print("Model loaded successfully.")


# ============================================================
# PREDICTIONS
# ============================================================

predictions = model.predict(X_test, verbose=0).flatten()


# ============================================================
# METRICS
# ============================================================

mae = mean_absolute_error(y_test, predictions)

rmse = np.sqrt(
    mean_squared_error(y_test, predictions)
)

r2 = r2_score(y_test, predictions)


print("\n" + "=" * 60)
print("TCN MODEL PERFORMANCE")
print("=" * 60)

print(f"MAE  : {mae:.4f}")
print(f"RMSE : {rmse:.4f}")
print(f"R²   : {r2:.4f}")


# ============================================================
# ACTUAL VS PREDICTED
# ============================================================

print("\n" + "=" * 60)
print("CREATING ACTUAL VS PREDICTED GRAPH")
print("=" * 60)

plt.figure(figsize=(10, 6))

plt.plot(
    y_test,
    marker="o",
    label="Actual AQI"
)

plt.plot(
    predictions,
    marker="x",
    label="Predicted AQI"
)

plt.xlabel("Test Sample")
plt.ylabel("AQI")

plt.title("TCN - Actual vs Predicted AQI")

plt.legend()
plt.grid(True)

plt.tight_layout()

plt.savefig(OUTPUT_PATH, dpi=300)

plt.show()

print("\nGraph saved at:")
print(OUTPUT_PATH)


# ============================================================
# SAMPLE RESULTS
# ============================================================

print("\n" + "=" * 60)
print("ACTUAL VS PREDICTED")
print("=" * 60)

for i in range(len(y_test)):
    print(
        f"{i + 1:02d}. "
        f"Actual: {y_test[i]:6.2f} | "
        f"Predicted: {predictions[i]:6.2f} | "
        f"Error: {abs(y_test[i] - predictions[i]):6.2f}"
    )

print("\n" + "=" * 60)
print("TCN EVALUATION COMPLETED")
print("=" * 60)