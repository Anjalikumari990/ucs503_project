"""Shared configuration for the behavioral anomaly-detection model.

The feature order here is the contract between model training and future
inference code.  It deliberately excludes window boundaries, ``is_active``,
and count features that duplicate typing rate or one another.
"""

# A small, interpretable set is appropriate for the six currently available
# active windows.  ``characters_per_second`` represents activity rate, while
# the remaining fields describe timing and pauses without duplicating the
# closely related press/release/character counts or median timing measures.
ML_FEATURES = [
    "characters_per_second",
    "mean_hold_ms",
    "std_hold_ms",
    "mean_flight_ms",
    "pause_count",
]

DATASET_PATH = "data/processed/keyboard_window_features.csv"
MODEL_PATH = "models/anomaly_model.pkl"

# This is a reproducible prototype configuration, not tuned production
# thresholds.  With only six legitimate windows, automatic contamination is
# preferable to asserting an unsupported expected anomaly rate.
RANDOM_STATE = 42
N_ESTIMATORS = 100
