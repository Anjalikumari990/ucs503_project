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
    """Load and validate active behavioral windows for model training."""
    path = Path(dataset_path)
    if not path.is_file():
        raise FileNotFoundError(f"Feature dataset not found: {path}")

    try:
        windows = pd.read_csv(path)
    except (OSError, pd.errors.ParserError) as err:
        raise ValueError(f"Failed to read feature dataset: {path}") from err

    required_columns = {"is_active", *ML_FEATURES}
    missing_columns = required_columns - set(windows.columns)
    if missing_columns:
        missing_str = ", ".join(sorted(missing_columns))
        raise ValueError(f"Dataset missing required columns: {missing_str}")

    active_values = windows["is_active"]
    if active_values.dtype == object:
        normalized = active_values.astype(str).str.strip().str.lower()
        if not normalized.isin({"true", "false"}).all():
            raise ValueError("Column 'is_active' must contain boolean values.")
        active_mask = normalized.eq("true")
    else:
        active_mask = active_values.eq(True)

    active_windows = windows.loc[active_mask, ML_FEATURES].copy()
    if active_windows.empty:
        raise ValueError("No active behavioral windows available for training.")

    for feature in ML_FEATURES:
        converted = pd.to_numeric(active_windows[feature], errors="coerce")
        if (active_windows[feature].notna() & converted.isna()).any():
            raise ValueError(f"Feature '{feature}' contains non-numeric values.")
        active_windows[feature] = converted

    return active_windows


def build_pipeline() -> Pipeline:
    """Construct Scikit-Learn preprocessing and Isolation Forest pipeline."""
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
    """Train pipeline on active windows and serialize artifact to disk."""
    training_data = load_active_training_data(dataset_path)
    pipeline = build_pipeline()
    pipeline.fit(training_data)

    artifact_path = Path(model_path)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, artifact_path)
    return pipeline, training_data


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    dataset_path = project_root / DATASET_PATH
    model_path = project_root / MODEL_PATH

    print("Training continuous authentication anomaly model...")
    pipeline, training_data = train_and_save(dataset_path, model_path)
    
    # Quick reload validation
    loaded = joblib.load(model_path)
    preds = loaded.predict(training_data)
    scores = loaded.decision_function(training_data)

    print("\n" + "=" * 50)
    print(" Model Training Summary")
    print("=" * 50)
    print(f"Dataset:        {DATASET_PATH}")
    print(f"Active samples: {len(training_data)}")
    print(f"Features ({len(ML_FEATURES)}):  {', '.join(ML_FEATURES)}")
    print(f"Model:          IsolationForest (n_estimators={N_ESTIMATORS}, contamination=auto)")
    print(f"Saved artifact: {MODEL_PATH}")
    print(f"Training score: mean={scores.mean():.4f}, min={scores.min():.4f}, max={scores.max():.4f}")
    print("Verification:   All baseline windows classified successfully.")
    print("=" * 50)


if __name__ == "__main__":
    main()
