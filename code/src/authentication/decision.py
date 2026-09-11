"""Authentication decision module.

Translates normalized trust scores (0-100) into discrete authentication
statuses (TRUSTED, VERIFY, REJECT) and system actions (ALLOW, PROMPT_REAUTH,
LOCK_SESSION) using centralized, configurable thresholds.

Decision Hierarchy:
-------------------
trust_score >= TRUSTED_THRESHOLD (70.0) -> status="TRUSTED", decision="ALLOW"
trust_score >= VERIFY_THRESHOLD  (40.0) -> status="VERIFY",  decision="PROMPT_REAUTH"
trust_score <  VERIFY_THRESHOLD  (40.0) -> status="REJECT",  decision="LOCK_SESSION"
"""

from math import isfinite
from typing import Any

DEFAULT_TRUSTED_THRESHOLD: float = 70.0
DEFAULT_VERIFY_THRESHOLD: float = 40.0

# Supported discrete states and decisions
STATUS_TRUSTED = "TRUSTED"
STATUS_VERIFY = "VERIFY"
STATUS_REJECT = "REJECT"

DECISION_ALLOW = "ALLOW"
DECISION_PROMPT_REAUTH = "PROMPT_REAUTH"
DECISION_LOCK_SESSION = "LOCK_SESSION"


def determine_authentication_decision(
    trust_score: float | int,
    trusted_threshold: float = DEFAULT_TRUSTED_THRESHOLD,
    verify_threshold: float = DEFAULT_VERIFY_THRESHOLD,
) -> dict[str, str]:
    """Map a trust score to an authentication status and corresponding system decision.

    Parameters
    ----------
    trust_score : float or int
        Trust score in the range [0.0, 100.0].
    trusted_threshold : float, default=70.0
        Minimum trust score required for the TRUSTED state.
    verify_threshold : float, default=40.0
        Minimum trust score required for the VERIFY state before falling to REJECT.

    Returns
    -------
    dict[str, str]
        {
            "status": "TRUSTED" | "VERIFY" | "REJECT",
            "decision": "ALLOW" | "PROMPT_REAUTH" | "LOCK_SESSION",
        }

    Raises
    ------
    TypeError
        If trust_score is not numeric.
    ValueError
        If trust_score is outside [0.0, 100.0], not finite, or if
        trusted_threshold <= verify_threshold.
    """
    if not isinstance(trust_score, (int, float)):
        raise TypeError(
            f"trust_score must be a numeric value, got {type(trust_score).__name__}."
        )

    score_val = float(trust_score)
    if not isfinite(score_val):
        raise ValueError(f"trust_score must be finite, got {trust_score!r}.")

    if not (0.0 <= score_val <= 100.0):
        raise ValueError(
            f"trust_score must be within the range [0.0, 100.0], got {score_val}."
        )

    if trusted_threshold <= verify_threshold:
        raise ValueError(
            f"trusted_threshold ({trusted_threshold}) must be strictly greater than "
            f"verify_threshold ({verify_threshold})."
        )

    if score_val >= trusted_threshold:
        return {
            "status": STATUS_TRUSTED,
            "decision": DECISION_ALLOW,
        }
    elif score_val >= verify_threshold:
        return {
            "status": STATUS_VERIFY,
            "decision": DECISION_PROMPT_REAUTH,
        }
    else:
        return {
            "status": STATUS_REJECT,
            "decision": DECISION_LOCK_SESSION,
        }


def main() -> None:
    """Run verification checks on decision boundaries."""
    print("=" * 60)
    print("Adaptive Continuous Authentication - Stage 2C Decision Logic")
    print("=" * 60)
    print(f"\nConfigured Thresholds:")
    print(f"- TRUSTED_THRESHOLD: >= {DEFAULT_TRUSTED_THRESHOLD} -> {STATUS_TRUSTED} ({DECISION_ALLOW})")
    print(f"- VERIFY_THRESHOLD:  >= {DEFAULT_VERIFY_THRESHOLD} -> {STATUS_VERIFY} ({DECISION_PROMPT_REAUTH})")
    print(f"- Below VERIFY:      <  {DEFAULT_VERIFY_THRESHOLD} -> {STATUS_REJECT} ({DECISION_LOCK_SESSION})")

    test_cases = [
        (100.00, "Maximum possible trust score"),
        (85.50,  "High trust score (active inlier)"),
        (70.00,  "Exact TRUSTED threshold boundary"),
        (69.99,  "Just below TRUSTED threshold"),
        (55.00,  "Mid-range trust score (borderline)"),
        (40.00,  "Exact VERIFY threshold boundary"),
        (39.99,  "Just below VERIFY threshold"),
        (15.00,  "Low trust score (suspicious anomaly)"),
        (0.00,   "Minimum possible trust score"),
    ]

    print("\n[1] Boundary Value Evaluation:")
    print(f"    {'Trust':<10} {'Status':<12} {'Decision':<18} {'Note'}")
    print("    " + "-" * 55)
    for score, note in test_cases:
        res = determine_authentication_decision(score)
        print(f"    {score:<10.2f} {res['status']:<12} {res['decision']:<18} {note}")

    print("\n" + "=" * 60)
    print("Stage 2C Verification Complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()

