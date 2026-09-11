"""Trust score mapping module for keystroke anomaly detection.

This module provides a deterministic, bounded mapping from raw Isolation Forest
decision scores to an intuitive Trust Score between 0 and 100.

Important Design Principles:
---------------------------
1. Higher IsolationForest decision_function() means more normal/inlier behavior.
   Lower decision_function() means more anomalous/outlier behavior.
2. Scikit-learn's Isolation Forest decision boundary is at 0.0.
   - Positive scores (> 0.0) indicate inliers (normal behavior).
   - Negative scores (< 0.0) indicate outliers (anomalous behavior).
3. We do NOT pretend this is a calibrated probability or statistical confidence.
   It is a prototype policy mapping using a bounded linear interpolation between
   configurable prototype thresholds.
4. Using default boundaries [-0.10, +0.10]:
   - score <= -0.10 maps to trust = 0.0 (strong anomaly / low trust)
   - score ==  0.00 maps to trust = 50.0 (neutral boundary)
   - score >= +0.10 maps to trust = 100.0 (strong inlier / high trust)
"""

from math import isfinite
from typing import Any

# Configurable prototype thresholds for score mapping.
# These represent baseline bounds, not universal statistical constants.
DEFAULT_ANOMALY_SCORE_LOW: float = -0.10
DEFAULT_ANOMALY_SCORE_HIGH: float = 0.10


def compute_trust_score(
    anomaly_score: float | int,
    score_low: float = DEFAULT_ANOMALY_SCORE_LOW,
    score_high: float = DEFAULT_ANOMALY_SCORE_HIGH,
    decimals: int = 2,
) -> float:
    """Map a raw anomaly score to a normalized trust score between 0.0 and 100.0.

    Uses a deterministic clipped linear interpolation:
        trust = 100.0 * (anomaly_score - score_low) / (score_high - score_low)
        clipped to [0.0, 100.0]

    Parameters
    ----------
    anomaly_score : float or int
        The raw decision_function() score from the Isolation Forest model.
    score_low : float, default=-0.10
        The anomaly score boundary at or below which trust becomes 0.0.
    score_high : float, default=0.10
        The anomaly score boundary at or above which trust becomes 100.0.
    decimals : int, default=2
        Number of decimal places for rounding the returned trust score.

    Returns
    -------
    float
        Trust score in the range [0.0, 100.0].

    Raises
    ------
    TypeError
        If anomaly_score is not a numeric type.
    ValueError
        If anomaly_score is not finite (NaN or inf), or if score_high <= score_low.
    """
    if not isinstance(anomaly_score, (int, float)):
        raise TypeError(
            f"anomaly_score must be a numeric value, got {type(anomaly_score).__name__}."
        )

    score_val = float(anomaly_score)
    if not isfinite(score_val):
        raise ValueError(f"anomaly_score must be finite, got {anomaly_score!r}.")

    if score_high <= score_low:
        raise ValueError(
            f"score_high ({score_high}) must be strictly greater than score_low ({score_low})."
        )

    # Linear interpolation
    raw_normalized = (score_val - score_low) / (score_high - score_low)
    scaled = raw_normalized * 100.0

    # Bounded clipping [0.0, 100.0]
    clipped = max(0.0, min(100.0, scaled))

    return round(clipped, decimals)


def main() -> None:
    """Run Stage 2B verification on real data and boundary test cases."""
    from pathlib import Path
    import pandas as pd
    from src.models.config import DATASET_PATH, ML_FEATURES, MODEL_PATH
    from src.models.predict import load_model, predict

    project_root = Path(__file__).resolve().parents[2]
    dataset_path = project_root / DATASET_PATH
    model_path = project_root / MODEL_PATH

    print("=" * 65)
    print("Adaptive Continuous Authentication - Stage 2B Trust Score Engine")
    print("=" * 65)
    print(f"\nConfiguration:")
    print(f"- DEFAULT_ANOMALY_SCORE_LOW:  {DEFAULT_ANOMALY_SCORE_LOW}")
    print(f"- DEFAULT_ANOMALY_SCORE_HIGH: {DEFAULT_ANOMALY_SCORE_HIGH}")
    print(f"- Neutral decision boundary (0.0) -> Trust Score: {compute_trust_score(0.0)}")

    # 1. Synthetic Boundary Tests
    print("\n[1] Boundary & Edge-Case Verification:")
    test_cases = [
        (-0.25, "Far below LOW (extreme anomaly)"),
        (-0.10, "Exact LOW threshold"),
        (-0.05, "Negative anomaly score"),
        (0.00, "Neutral boundary (decision=0.0)"),
        (0.05, "Positive normal score"),
        (0.10, "Exact HIGH threshold"),
        (0.20, "Far above HIGH (extreme inlier)"),
    ]
    for score, description in test_cases:
        trust = compute_trust_score(score)
        print(f"    score={score:+.2f} -> trust={trust:6.2f}  ({description})")

    # 2. Evaluation on Real Active Windows
    print(f"\n[2] Evaluating Real S02 Windows from: {dataset_path.relative_to(project_root)}")
    pipeline = load_model(model_path)
    windows = pd.read_csv(dataset_path)

    active_mask = windows["is_active"].astype(str).str.strip().str.lower().eq("true")
    active_windows = windows.loc[active_mask]

    print(f"    Found {len(active_windows)} active windows.")
    print(f"    {'Window Start':<14} {'Pred':<6} {'Anomaly Score':<16} {'Trust Score':<12}")
    print("    " + "-" * 50)

    for _, row in active_windows.iterrows():
        start_ms = int(row["window_start_ms"])
        features = {col: row[col] for col in ML_FEATURES}
        inference_res = predict(features, model=pipeline)
        pred = inference_res["prediction"]
        score = inference_res["anomaly_score"]
        trust = compute_trust_score(score)
        print(f"    {start_ms:<14} {pred:<6} {score:<16.6f} {trust:<12.2f}")

    print("\n" + "=" * 65)
    print("Stage 2B Verification Complete.")
    print("Note: Trust Score is a prototype policy mapping, not a calibrated probability.")
    print("Decision logic (Stage 2C) will map trust scores to authentication actions.")
    print("=" * 65)


if __name__ == "__main__":
    main()

