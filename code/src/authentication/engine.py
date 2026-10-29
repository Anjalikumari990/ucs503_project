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
from src.models.predict import load_model, predict
from src.scoring.trust_score import compute_trust_score

# Inactive window policy constants
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
    """Evaluate a single 10-second behavioral window through model, scoring, and policy."""
    if isinstance(window_data, pd.DataFrame):
        if len(window_data) != 1:
            raise ValueError(f"Expected a single-row DataFrame, got {len(window_data)} rows.")
        data_dict = window_data.iloc[0].to_dict()
    elif isinstance(window_data, pd.Series):
        data_dict = window_data.to_dict()
    elif isinstance(window_data, dict):
        data_dict = window_data
    else:
        raise TypeError(f"window_data must be dict, Series, or 1-row DataFrame, got {type(window_data).__name__}.")

    # Resolve activity status
    if is_active is None:
        raw_active = data_dict.get("is_active", True)
        is_active = raw_active.strip().lower() == "true" if isinstance(raw_active, str) else bool(raw_active)

    # Inactive windows represent natural pause/reading periods; hold state without penalty
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

    # Evaluate active window through anomaly model and compute continuous trust
    inference = predict(data_dict, model=model)
    pred = inference["prediction"]
    score = inference["anomaly_score"]

    trust = compute_trust_score(score, score_low=score_low, score_high=score_high)
    decision = determine_authentication_decision(
        trust,
        trusted_threshold=trusted_threshold,
        verify_threshold=verify_threshold,
    )

    return {
        "is_active": True,
        "prediction": pred,
        "anomaly_score": score,
        "trust_score": trust,
        "status": decision["status"],
        "decision": decision["decision"],
        "reason": None,
    }


class AuthenticationEngine:
    """Stateful continuous authentication session manager maintaining trust score history."""

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
        """Process incoming 10-second window, preserving state on idle windows."""
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
            payload = dict(res)
        else:
            payload = {
                "is_active": False,
                "prediction": None,
                "anomaly_score": None,
                "trust_score": self.last_trust_score,
                "status": self.current_status,
                "decision": self.current_decision,
                "reason": REASON_INACTIVE,
            }

        self.history.append(payload)
        return payload
