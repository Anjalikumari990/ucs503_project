"""Train the prototype legitimate-user keystroke anomaly model.

The saved artifact is a single scikit-learn Pipeline.  It accepts raw rows in
the shared ML_FEATURES order and consistently performs imputation, scaling,
and Isolation Forest inference.  The available six active windows demonstrate
that this pipeline runs; they are not enough for meaningful performance
evaluation.
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.models.config import (
    DATASET_PATH,
    ML_FEATURES,
    MODEL_PATH,
    N_ESTIMATORS,
    RANDOM_STATE,
)


def load_active_training_data(dataset_path: Path | str) -> pd.DataFrame:
    """Load, validate, and return active rows containing model features.

    Invalid feature values raise a clear error instead of being silently
    converted. Missing values are allowed because the pipeline imputes them.
    """
    path = Path(dataset_path)
    if not path.is_file():
        raise FileNotFoundError(f"Processed feature CSV not found: {path}")

    try:
        windows = pd.read_csv(path)
    except (OSError, pd.errors.ParserError) as error:
        raise ValueError(f"Could not read processed feature CSV: {path}") from error

    required_columns = {"is_active", *ML_FEATURES}
    missing_columns = required_columns - set(windows.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Processed feature CSV is missing required columns: {missing}")

    active_values = windows["is_active"]
    if active_values.dtype == object:
        normalized = active_values.astype(str).str.strip().str.lower()
        if not normalized.isin({"true", "false"}).all():
            raise ValueError("Column 'is_active' must contain boolean True/False values.")
        active_mask = normalized.eq("true")
    else:
        active_mask = active_values.eq(True)

    active_windows = windows.loc[active_mask, ML_FEATURES].copy()
    if active_windows.empty:
        raise ValueError("No active behavioral windows are available for training.")

    for feature in ML_FEATURES:
        converted = pd.to_numeric(active_windows[feature], errors="coerce")
        invalid_value = active_windows[feature].notna() & converted.isna()
        if invalid_value.any():
            raise ValueError(f"Feature '{feature}' contains non-numeric values.")
        active_windows[feature] = converted

    return active_windows


def build_pipeline() -> Pipeline:
    """Build the single reusable preprocessing and anomaly-model pipeline."""
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "isolation_forest",
                IsolationForest(
                    n_estimators=N_ESTIMATORS,
                    contamination="auto",
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def train_and_save(
    dataset_path: Path | str = DATASET_PATH,
    model_path: Path | str = MODEL_PATH,
) -> tuple[Pipeline, pd.DataFrame]:
    """Train on active windows and save the complete reusable pipeline."""
    training_data = load_active_training_data(dataset_path)
    pipeline = build_pipeline()
    pipeline.fit(training_data)

    artifact_path = Path(model_path)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, artifact_path)
    return pipeline, training_data


def main() -> None:
    """Run training and a basic artifact reload/prediction validation."""
    project_root = Path(__file__).resolve().parents[2]
    dataset_path = project_root / DATASET_PATH
    model_path = project_root / MODEL_PATH

    pipeline, training_data = train_and_save(dataset_path, model_path)
    reloaded_pipeline = joblib.load(model_path)
    predictions = reloaded_pipeline.predict(training_data)
    raw_scores = reloaded_pipeline.score_samples(training_data)

    print("=" * 50)
    print("Adaptive Continuous Authentication")
    print("Model Training")
    print("=" * 50)
    print(f"\nDataset:\n{DATASET_PATH}")
    print(f"\nActive training windows: {len(training_data)}")
    print("\nFeatures:")
    for feature in ML_FEATURES:
        print(f"- {feature}")
    print("\nModel:\nIsolationForest")
    print("Configuration:")
    print(f"- n_estimators: {N_ESTIMATORS}")
    print("- contamination: auto")
    print(f"- random_state: {RANDOM_STATE}")
    print(f"\nArtifact:\n{MODEL_PATH}")
    print("\nReload validation: passed (loaded pipeline produced predictions).")
    print("\nTechnical outputs for active training windows:")
    for index, prediction, score in zip(training_data.index, predictions, raw_scores):
        print(f"- window index {index}: prediction={prediction}, raw_score={score:.6f}")
    print("\nLimitation: six active windows are insufficient for meaningful")
    print("authentication-performance evaluation. No performance metrics were calculated.")
    print("\nTraining complete.")
    print("=" * 50)


if __name__ == "__main__":
    main()
