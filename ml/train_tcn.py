import os
import numpy as np
import tensorflow as tf

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (
    Input,
    Conv1D,
    BatchNormalization,
    ReLU,
    Dropout,
    GlobalAveragePooling1D,
    Dense
)
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau


# ============================================================
# PATHS
# ============================================================

BASE_DIR = r"D:\AQI_Health-Risk-System"

DATA_DIR = os.path.join(
    BASE_DIR,
    "ml",
    "data"
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "ml",
    "tcn_aqi_model.keras"
)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 60)
print("LOADING IMPROVED TCN DATA")
print("=" * 60)

X_train = np.load(
    os.path.join(DATA_DIR, "X_train.npy")
)

X_test = np.load(
    os.path.join(DATA_DIR, "X_test.npy")
)

y_train = np.load(
    os.path.join(DATA_DIR, "y_train.npy")
)

y_test = np.load(
    os.path.join(DATA_DIR, "y_test.npy")
)

print("X_train:", X_train.shape)
print("y_train:", y_train.shape)

print("X_test :", X_test.shape)
print("y_test :", y_test.shape)


# ============================================================
# BUILD TCN
# ============================================================

print("\n" + "=" * 60)
print("BUILDING IMPROVED TCN")
print("=" * 60)

model = Sequential([

    Input(
        shape=(
            X_train.shape[1],
            X_train.shape[2]
        )
    ),

    # TCN Block 1
    Conv1D(
        filters=32,
        kernel_size=3,
        padding="causal",
        dilation_rate=1
    ),

    BatchNormalization(),
    ReLU(),
    Dropout(0.15),


    # TCN Block 2
    Conv1D(
        filters=64,
        kernel_size=3,
        padding="causal",
        dilation_rate=2
    ),

    BatchNormalization(),
    ReLU(),
    Dropout(0.15),


    # TCN Block 3
    Conv1D(
        filters=64,
        kernel_size=3,
        padding="causal",
        dilation_rate=4
    ),

    BatchNormalization(),
    ReLU(),
    Dropout(0.15),


    # Convert temporal features
    GlobalAveragePooling1D(),


    # Dense layer
    Dense(
        32,
        activation="relu"
    ),

    Dropout(0.15),


    # Next-day AQI
    Dense(
        1,
        activation="linear"
    )
])


# ============================================================
# COMPILE
# ============================================================

model.compile(

    optimizer=tf.keras.optimizers.Adam(
        learning_rate=0.001
    ),

    loss="mse",

    metrics=["mae"]
)


model.summary()


# ============================================================
# CALLBACKS
# ============================================================

early_stopping = EarlyStopping(

    monitor="val_loss",

    patience=20,

    restore_best_weights=True
)


reduce_lr = ReduceLROnPlateau(

    monitor="val_loss",

    factor=0.5,

    patience=7,

    min_lr=0.00001
)


# ============================================================
# TRAIN
# ============================================================

print("\n" + "=" * 60)
print("TRAINING IMPROVED TCN")
print("=" * 60)

history = model.fit(

    X_train,

    y_train,

    epochs=150,

    batch_size=8,

    validation_split=0.2,

    callbacks=[
        early_stopping,
        reduce_lr
    ],

    verbose=1
)


# ============================================================
# EVALUATE
# ============================================================

print("\n" + "=" * 60)
print("EVALUATING IMPROVED TCN")
print("=" * 60)

test_loss, test_mae = model.evaluate(

    X_test,

    y_test,

    verbose=0
)


print(
    f"Test Loss (MSE): {test_loss:.4f}"
)

print(
    f"Test MAE       : {test_mae:.4f}"
)


# ============================================================
# PREDICTIONS
# ============================================================

predictions = model.predict(
    X_test,
    verbose=0
).flatten()


print("\n" + "=" * 60)
print("SAMPLE PREDICTIONS")
print("=" * 60)


for i in range(
    min(10, len(y_test))
):

    print(

        f"Actual AQI: "
        f"{y_test[i]:.2f}  |  "

        f"Predicted AQI: "
        f"{predictions[i]:.2f}"

    )


# ============================================================
# SAVE MODEL
# ============================================================

model.save(MODEL_PATH)


print("\n" + "=" * 60)
print("IMPROVED TCN TRAINING COMPLETED")
print("=" * 60)

print("Model saved at:")

print(MODEL_PATH)