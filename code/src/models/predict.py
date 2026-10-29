from pathlib import Path
from typing import Any
import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from src.models.config import DATASET_PATH, ML_FEATURES, MODEL_PATH


def get_default_model_path() -> Path:
    """Return default model artifact path."""
    project_root = Path(__file__).resolve().parents[2]
    return project_root / MODEL_PATH


def load_model(model_path: Path | str | None = None) -> Pipeline:
    """Load and validate the saved Scikit-Learn pipeline artifact."""
    artifact_path = Path(model_path) if model_path is not None else get_default_model_path()

    if not artifact_path.is_file():
        raise FileNotFoundError(
            f"Model artifact not found at {artifact_path}. Run train_model.py first."
        )

    try:
        model = joblib.load(artifact_path)
    except Exception as err:
        raise ValueError(f"Failed to load model artifact from {artifact_path}: {err}") from err

    if not isinstance(model, Pipeline):
        raise ValueError(f"Loaded object is {type(model).__name__}, expected Pipeline.")

    return model


def prepare_feature_row(features: dict[str, Any] | pd.DataFrame | pd.Series) -> pd.DataFrame:
    """Align input features with the ML_FEATURES schema, preserving NaNs for imputation."""
    if isinstance(features, pd.DataFrame):
        if len(features) != 1:
            raise ValueError(f"Expected single-row DataFrame, got {len(features)} rows.")
        feature_dict = features.iloc[0].to_dict()
    elif isinstance(features, pd.Series):
        feature_dict = features.to_dict()
    elif isinstance(features, dict):
        feature_dict = features
    else:
        raise TypeError(f"Features must be dict, Series, or 1-row DataFrame, got {type(features).__name__}.")

    if not any(k in feature_dict for k in ML_FEATURES):
        raise ValueError(f"Input features must contain recognized ML features: {ML_FEATURES}")

    row_data = {}
    for name in ML_FEATURES:
        val = feature_dict.get(name, np.nan)
        if val is None or (isinstance(val, float) and np.isnan(val)):
            row_data[name] = np.nan
        else:
            try:
                row_data[name] = float(val)
            except (ValueError, TypeError) as err:
                raise ValueError(f"Feature '{name}' has non-numeric value: {val!r}") from err

    return pd.DataFrame([row_data], columns=ML_FEATURES)


def predict(
    features: dict[str, Any] | pd.DataFrame | pd.Series,
    model: Pipeline | None = None,
) -> dict[str, Any]:
    """Score a behavioral feature vector through the anomaly model pipeline."""
    if model is None:
        model = load_model()

    if not isinstance(model, Pipeline):
        raise ValueError(f"Expected model to be a Pipeline, got {type(model).__name__}.")

    row = prepare_feature_row(features)
    pred = int(model.predict(row)[0])
    score = float(model.decision_function(row)[0])

    return {
        "prediction": pred,
        "anomaly_score": score,
    }


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    dataset_path = project_root / DATASET_PATH
    model_path = project_root / MODEL_PATH

    print(f"Loading model from {model_path}...")
    pipeline = load_model(model_path)

    windows = pd.read_csv(dataset_path)
    active_mask = windows["is_active"].astype(str).str.strip().str.lower().eq("true")
    active_windows = windows.loc[active_mask]
    first_window = active_windows.iloc[0].to_dict()

    print("\nEvaluating sample active window:")
    result = predict(first_window, model=pipeline)
    print(f"Prediction:    {result['prediction']} (1=normal, -1=anomaly)")
    print(f"Decision Score: {result['anomaly_score']:.6f}")


if __name__ == "__main__":
    main()
