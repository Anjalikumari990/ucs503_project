"""Inference API for keystroke anomaly detection.

This module loads the trained scikit-learn Pipeline artifact and evaluates
individual 10-second behavioral feature vectors without retraining or bypassing
preprocessing.

The input vector is mapped to the centralized ML_FEATURES order defined in
src.models.config. Missing values (None / NaN) are passed through to the
pipeline's SimpleImputer(strategy="median").
"""

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from src.models.config import DATASET_PATH, ML_FEATURES, MODEL_PATH


def get_default_model_path() -> Path:
    """Return the absolute path to the default trained model artifact."""
    project_root = Path(__file__).resolve().parents[2]
    return project_root / MODEL_PATH


def load_model(model_path: Path | str | None = None) -> Pipeline:
    """Load and validate the saved scikit-learn anomaly detection pipeline.

    Parameters
    ----------
    model_path : Path or str, optional
        Path to the saved pipeline artifact (.pkl). If None, defaults to
        the path configured in src.models.config.

    Returns
    -------
    Pipeline
        The loaded scikit-learn Pipeline object.

    Raises
    ------
    FileNotFoundError
        If the model artifact file does not exist on disk.
    ValueError
        If the loaded artifact is not a scikit-learn Pipeline.
    """
    if model_path is None:
        artifact_path = get_default_model_path()
    else:
        artifact_path = Path(model_path)

    if not artifact_path.is_file():
        raise FileNotFoundError(
            f"Model artifact not found: {artifact_path}. "
            "Please train the model first using 'python -m src.models.train_model'."
        )

    try:
        model = joblib.load(artifact_path)
    except Exception as error:
        raise ValueError(
            f"Could not load model artifact from {artifact_path}: {error}"
        ) from error

    if not isinstance(model, Pipeline):
        raise ValueError(
            f"Loaded object from {artifact_path} is of type {type(model).__name__}, "
            "expected sklearn.pipeline.Pipeline."
        )

    return model


def prepare_feature_row(
    features: dict[str, Any] | pd.DataFrame | pd.Series,
) -> pd.DataFrame:
    """Validate and align input features to the centralized ML_FEATURES order.

    Accepts a dictionary, pandas Series, or single-row DataFrame. Missing values
    (None or NaN) are preserved as NaN to allow pipeline imputation. Non-numeric
    values raise a ValueError.

    Parameters
    ----------
    features : dict[str, Any], pd.DataFrame, or pd.Series
        Raw behavioral features for a single 10-second window.

    Returns
    -------
    pd.DataFrame
        A single-row DataFrame with columns matching ML_FEATURES in order.

    Raises
    ------
    TypeError
        If the input is not a dict, Series, or DataFrame.
    ValueError
        If the input has no recognized features or contains non-numeric values.
    """
    if isinstance(features, pd.DataFrame):
        if len(features) != 1:
            raise ValueError(
                f"Expected a single-row DataFrame, got {len(features)} rows."
            )
        feature_dict = features.iloc[0].to_dict()
    elif isinstance(features, pd.Series):
        feature_dict = features.to_dict()
    elif isinstance(features, dict):
        feature_dict = features
    else:
        raise TypeError(
            "Features must be a dict, pd.Series, or single-row pd.DataFrame, "
            f"got {type(features).__name__}."
        )

    # Check that at least one recognizable feature is present
    if not any(key in feature_dict for key in ML_FEATURES):
        raise ValueError(
            f"Input features dictionary must contain recognized ML features: {ML_FEATURES}"
        )

    row_data: dict[str, Any] = {}
    for name in ML_FEATURES:
        val = feature_dict.get(name, np.nan)
        if val is None or (isinstance(val, float) and np.isnan(val)):
            row_data[name] = np.nan
        else:
            try:
                row_data[name] = float(val)
            except (ValueError, TypeError) as error:
                raise ValueError(
                    f"Feature '{name}' has non-numeric value: {val!r}"
                ) from error

    return pd.DataFrame([row_data], columns=ML_FEATURES)


def predict(
    features: dict[str, Any] | pd.DataFrame | pd.Series,
    model: Pipeline | None = None,
) -> dict[str, Any]:
    """Run a behavioral feature vector through the trained anomaly model pipeline.

    Parameters
    ----------
    features : dict[str, Any], pd.DataFrame, or pd.Series
        Behavioral feature vector for a 10-second window.
    model : Pipeline, optional
        Pre-loaded scikit-learn Pipeline. If None, the default model artifact
        is loaded from models/anomaly_model.pkl.

    Returns
    -------
    dict[str, Any]
        {
            "prediction": int,       # 1 for inlier (normal), -1 for outlier (anomalous)
            "anomaly_score": float,  # Raw decision_function score from Isolation Forest
        }
    """
    if model is None:
        model = load_model()

    if not isinstance(model, Pipeline):
        raise ValueError(
            f"Expected model to be a sklearn.pipeline.Pipeline, got {type(model).__name__}."
        )

    row = prepare_feature_row(features)
    raw_pred = model.predict(row)[0]
    raw_score = model.decision_function(row)[0]

    return {
        "prediction": int(raw_pred),
        "anomaly_score": float(raw_score),
    }


def main() -> None:
    """Run Stage 2A inference demonstration and verification tests."""
    project_root = Path(__file__).resolve().parents[2]
    dataset_path = project_root / DATASET_PATH
    model_path = project_root / MODEL_PATH

    print("=" * 60)
    print("Adaptive Continuous Authentication - Stage 2A Inference API")
    print("=" * 60)

    # 1. Load model artifact
    print(f"\n[1] Loading model artifact from: {model_path.relative_to(project_root)}")
    pipeline = load_model(model_path)
    print(f"    Loaded successfully: {type(pipeline).__name__}")
    print(f"    Pipeline steps: {list(pipeline.named_steps.keys())}")

    # 2. Load processed feature CSV
    print(f"\n[2] Loading processed features from: {dataset_path.relative_to(project_root)}")
    windows = pd.read_csv(dataset_path)

    # 3. Select the first active window
    active_mask = windows["is_active"].astype(str).str.strip().str.lower().eq("true")
    active_windows = windows.loc[active_mask]
    first_active_row = active_windows.iloc[0]
    print(f"    Total windows: {len(windows)} | Active windows: {len(active_windows)}")
    print(f"    Selected window start: {first_active_row['window_start_ms']} ms")

    # 4. Construct dictionary containing only the five ML features
    first_window_features = {
        feature: first_active_row[feature] for feature in ML_FEATURES
    }
    print("\n[3] Input Feature Vector (First Active Window):")
    for k, v in first_window_features.items():
        print(f"    {k}: {v:.4f}" if isinstance(v, float) else f"    {k}: {v}")

    # 5. Call public inference function
    result_active = predict(first_window_features, model=pipeline)

    # 6. Print result
    print("\n[4] Inference Output:")
    print(f"    prediction:    {result_active['prediction']}  (1 = inlier/normal, -1 = outlier/anomalous)")
    print(f"    anomaly_score: {result_active['anomaly_score']:.6f}  (raw decision_function)")

    # 7. Create another test with one missing feature (std_hold_ms = None)
    test_missing_features = dict(first_window_features)
    test_missing_features["std_hold_ms"] = None
    print("\n[5] Missing-Value Test Vector (std_hold_ms = None):")
    for k, v in test_missing_features.items():
        val_str = "None (will be imputed via median)" if v is None else f"{v:.4f}"
        print(f"    {k}: {val_str}")

    # 8. Verify missing-value case still works
    result_missing = predict(test_missing_features, model=pipeline)
    print("\n[6] Missing-Value Inference Output:")
    print(f"    prediction:    {result_missing['prediction']}")
    print(f"    anomaly_score: {result_missing['anomaly_score']:.6f}")
    print("    Missing-value test: passed (pipeline imputer handled None value).")

    print("\n" + "=" * 60)
    print("Stage 2A Verification Complete.")
    print("Note: Prediction represents anomaly model classification only.")
    print("Trust scoring and authentication decisions will be added in subsequent stages.")
    print("=" * 60)


if __name__ == "__main__":
    main()
