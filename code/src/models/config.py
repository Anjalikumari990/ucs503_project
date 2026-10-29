"""Configuration constants for model training and inference."""

# Core behavioral features used for anomaly detection
ML_FEATURES = [
    "characters_per_second",
    "mean_hold_ms",
    "std_hold_ms",
    "mean_flight_ms",
    "pause_count",
]

DATASET_PATH = "data/processed/keyboard_window_features.csv"
MODEL_PATH = "models/anomaly_model.pkl"

# Isolation Forest hyper-parameters
RANDOM_STATE = 42
N_ESTIMATORS = 100
