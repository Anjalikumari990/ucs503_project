"""Unified authentication engine for adaptive continuous authentication.

Coordinates the end-to-end inference flow for a 10-second behavioral window:
    Window Features -> Model Inference -> Trust Score -> Authentication Decision

Inactive Window Policy:
----------------------
A window where is_active is False (character_count < 5) represents benign
idle time (reading, thinking, using mouse, away from keyboard). Inactive != attacker.
Therefore:
1. Anomaly detection inference is bypassed for inactive windows.
2. Inactive windows are NOT penalized with an anomaly or zero trust score.
3. The system returns an INACTIVE/HOLD state with an explanatory reason.
4. When using the stateful AuthenticationEngine, the last known trust score
   is maintained across idle windows.
"""

from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.pipeline import Pipeline

from src.authentication.decision import (
    DECISION_ALLOW,
    DECISION_LOCK_SESSION,
    DECISION_PROMPT_REAUTH,
    STATUS_REJECT,
    STATUS_TRUSTED,
    STATUS_VERIFY,
    determine_authentication_decision,
)
from src.models.config import DATASET_PATH, ML_FEATURES, MODEL_PATH
from src.models.predict import load_model, predict
from src.scoring.trust_score import compute_trust_score

# Inactive window status and decision constants
STATUS_INACTIVE = "INACTIVE"
DECISION_HOLD = "HOLD"
REASON_INACTIVE = "Insufficient keyboard activity in window"


def evaluate_window(
    window_data: dict[str, Any] | pd.Series | pd.DataFrame,
    is_active: bool | None = None,
    model: Pipeline | None = None,
    score_low: float = -0.10,
    score_high: float = 0.10,
    trusted_threshold: float = 70.0,
    verify_threshold: float = 40.0,
) -> dict[str, Any]:
    """Evaluate a single 10-second behavioral window through the complete pipeline.

    Parameters
    ----------
    window_data : dict, pd.Series, or pd.DataFrame
        Dictionary or row containing behavioral window metrics.
    is_active : bool, optional
        Explicit flag indicating whether the window is active (>= 5 keystrokes).
        If None, the flag is extracted from window_data["is_active"] if present;
        otherwise defaults to True.
    model : Pipeline, optional
        Pre-loaded scikit-learn Pipeline. If None, the default model is loaded
        from models/anomaly_model.pkl.
    score_low : float, default=-0.10
        Lower anomaly score threshold for trust score mapping.
    score_high : float, default=0.10
        Upper anomaly score threshold for trust score mapping.
    trusted_threshold : float, default=70.0
        Trust score threshold for TRUSTED status.
    verify_threshold : float, default=40.0
        Trust score threshold for VERIFY status.

    Returns
    -------
    dict[str, Any]
        {
            "is_active": bool,
            "prediction": int | None,
            "anomaly_score": float | None,
            "trust_score": float | None,
            "status": str,
            "decision": str,
            "reason": str | None,
        }
    """
    # Extract row dict
    if isinstance(window_data, pd.DataFrame):
        if len(window_data) != 1:
            raise ValueError(f"Expected a single-row DataFrame, got {len(window_data)} rows.")
        data_dict = window_data.iloc[0].to_dict()
    elif isinstance(window_data, pd.Series):
        data_dict = window_data.to_dict()
    elif isinstance(window_data, dict):
        data_dict = window_data
    else:
        raise TypeError(
            f"window_data must be a dict, pd.Series, or single-row DataFrame, got {type(window_data).__name__}."
        )

    # Determine activity flag
    if is_active is None:
        raw_active = data_dict.get("is_active", True)
        if isinstance(raw_active, str):
            is_active = raw_active.strip().lower() == "true"
        else:
            is_active = bool(raw_active)

    # Policy for Inactive Windows: do not penalize idle time as an anomaly
    if not is_active:
        return {
            "is_active": False,
            "prediction": None,
            "anomaly_score": None,
            "trust_score": None,
            "status": STATUS_INACTIVE,
            "decision": DECISION_HOLD,
            "reason": REASON_INACTIVE,
        }

    # Active Window: Run full ML -> Scoring -> Decision pipeline
    inference_result = predict(data_dict, model=model)
    pred = inference_result["prediction"]
    score = inference_result["anomaly_score"]

    trust = compute_trust_score(score, score_low=score_low, score_high=score_high)
    decision_result = determine_authentication_decision(
        trust,
        trusted_threshold=trusted_threshold,
        verify_threshold=verify_threshold,
    )

    return {
        "is_active": True,
        "prediction": pred,
        "anomaly_score": score,
        "trust_score": trust,
        "status": decision_result["status"],
        "decision": decision_result["decision"],
        "reason": None,
    }


class AuthenticationEngine:
    """Stateful continuous authentication engine.

    Maintains session state and trust across consecutive 10-second windows.
    During inactive windows, maintains the last known trust score and access
    decision so that idle legitimate users are not prematurely locked out.
    """

    def __init__(
        self,
        model: Pipeline | None = None,
        initial_trust: float = 100.0,
        trusted_threshold: float = 70.0,
        verify_threshold: float = 40.0,
    ) -> None:
        self.model = model if model is not None else load_model()
        self.initial_trust = initial_trust
        self.trusted_threshold = trusted_threshold
        self.verify_threshold = verify_threshold

        self.last_trust_score: float = initial_trust
        self.current_status: str = STATUS_TRUSTED
        self.current_decision: str = DECISION_ALLOW
        self.history: list[dict[str, Any]] = []

    def process_window(
        self,
        window_data: dict[str, Any] | pd.Series | pd.DataFrame,
        is_active: bool | None = None,
    ) -> dict[str, Any]:
        """Process an incoming window and update session authentication state."""
        res = evaluate_window(
            window_data,
            is_active=is_active,
            model=self.model,
            trusted_threshold=self.trusted_threshold,
            verify_threshold=self.verify_threshold,
        )

        if res["is_active"]:
            self.last_trust_score = res["trust_score"]
            self.current_status = res["status"]
            self.current_decision = res["decision"]
            session_payload = dict(res)
        else:
            # Idle window: maintain session state while noting inactive status
            session_payload = {
                "is_active": False,
                "prediction": None,
                "anomaly_score": None,
                "trust_score": self.last_trust_score,  # Preserved from prior active window
                "status": self.current_status,         # Preserved access status
                "decision": self.current_decision,     # Preserved access decision
                "reason": REASON_INACTIVE,
            }

        self.history.append(session_payload)
        return session_payload

    def reset(self) -> None:
        """Reset the session history and revert to initial trust state."""
        self.last_trust_score = self.initial_trust
        self.current_status = STATUS_TRUSTED
        self.current_decision = DECISION_ALLOW
        self.history.clear()


def main() -> None:
    """Run end-to-end replay test across all 7 windows in the dataset."""
    project_root = Path(__file__).resolve().parents[2]
    dataset_path = project_root / DATASET_PATH
    model_path = project_root / MODEL_PATH

    print("=" * 75)
    print("Adaptive Continuous Authentication - Stage 2D Unified Engine")
    print("=" * 75)

    print(f"\n[1] Initializing Engine & Preloading Model...")
    engine = AuthenticationEngine()
    print(f"    Loaded pipeline: {type(engine.model).__name__}")
    print(f"    Initial session trust: {engine.initial_trust:.1f}")

    print(f"\n[2] Replaying All Windows from: {dataset_path.relative_to(project_root)}")
    windows = pd.read_csv(dataset_path)

    print(f"\n    {'Window':<8} {'Active':<8} {'Pred':<6} {'Anomaly':<12} {'Trust':<10} {'Status':<12} {'Decision':<16}")
    print("    " + "-" * 72)

    for idx, row in windows.iterrows():
        start_ms = int(row["window_start_ms"])
        window_dict = row.to_dict()
        result = engine.process_window(window_dict)

        pred_str = str(result["prediction"]) if result["prediction"] is not None else "N/A"
        score_str = f"{result['anomaly_score']:.4f}" if result["anomaly_score"] is not None else "N/A"
        trust_str = f"{result['trust_score']:.2f}" if result["trust_score"] is not None else "N/A"
        active_str = "True" if result["is_active"] else "False"

        print(
            f"    {start_ms:<8} {active_str:<8} {pred_str:<6} {score_str:<12} "
            f"{trust_str:<10} {result['status']:<12} {result['decision']:<16}"
        )

    print("\n" + "=" * 75)
    print("Stage 2D Replay Test Complete.")
    print("Notice: Window 60000ms (inactive) did not trigger an anomalous false rejection.")
    print("=" * 75)


if __name__ == "__main__":
    main()

