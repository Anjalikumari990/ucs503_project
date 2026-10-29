from math import isfinite

DEFAULT_TRUSTED_THRESHOLD: float = 70.0
DEFAULT_VERIFY_THRESHOLD: float = 40.0

# Supported discrete states and system actions
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
    """
    Map a 0-100 continuous trust score to a security state and system action.
    
    Score >= 70.0 -> TRUSTED / ALLOW
    40.0 <= Score < 70.0 -> VERIFY / PROMPT_REAUTH
    Score < 40.0 -> REJECT / LOCK_SESSION
    """
    if not isinstance(trust_score, (int, float)):
        raise TypeError(f"trust_score must be numeric, got {type(trust_score).__name__}.")

    score_val = float(trust_score)
    if not isfinite(score_val):
        raise ValueError(f"trust_score must be finite, got {trust_score!r}.")

    if not (0.0 <= score_val <= 100.0):
        raise ValueError(f"trust_score must be between 0.0 and 100.0, got {score_val}.")

    if trusted_threshold <= verify_threshold:
        raise ValueError(
            f"trusted_threshold ({trusted_threshold}) must be strictly greater than "
            f"verify_threshold ({verify_threshold})."
        )

    if score_val >= trusted_threshold:
        return {"status": STATUS_TRUSTED, "decision": DECISION_ALLOW}
    elif score_val >= verify_threshold:
        return {"status": STATUS_VERIFY, "decision": DECISION_PROMPT_REAUTH}
    else:
        return {"status": STATUS_REJECT, "decision": DECISION_LOCK_SESSION}


def main() -> None:
    assert determine_authentication_decision(85.0)["decision"] == DECISION_ALLOW
    assert determine_authentication_decision(55.0)["decision"] == DECISION_PROMPT_REAUTH
    assert determine_authentication_decision(25.0)["decision"] == DECISION_LOCK_SESSION
    print("Authentication decision checks passed.")


if __name__ == "__main__":
    main()
