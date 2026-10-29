from math import isfinite

# Default score boundaries for Isolation Forest decision function mapping
DEFAULT_ANOMALY_SCORE_LOW: float = -0.10
DEFAULT_ANOMALY_SCORE_HIGH: float = 0.10


def compute_trust_score(
    anomaly_score: float | int,
    score_low: float = DEFAULT_ANOMALY_SCORE_LOW,
    score_high: float = DEFAULT_ANOMALY_SCORE_HIGH,
    decimals: int = 2,
) -> float:
    """
    Map raw Isolation Forest decision score to a 0.0 - 100.0 continuous trust score.
    
    Uses linear interpolation clamped between score_low (0.0 trust) and score_high (100.0 trust).
    """
    if not isinstance(anomaly_score, (int, float)):
        raise TypeError(f"anomaly_score must be numeric, got {type(anomaly_score).__name__}.")

    score_val = float(anomaly_score)
    if not isfinite(score_val):
        raise ValueError(f"anomaly_score must be finite, got {anomaly_score!r}.")

    if score_high <= score_low:
        raise ValueError(f"score_high ({score_high}) must be greater than score_low ({score_low}).")

    normalized = (score_val - score_low) / (score_high - score_low) * 100.0
    clipped = max(0.0, min(100.0, normalized))
    return round(clipped, decimals)


def main() -> None:
    # Quick sanity checks across key score boundaries
    assert compute_trust_score(0.10) == 100.0
    assert compute_trust_score(0.00) == 50.0
    assert compute_trust_score(-0.10) == 0.0
    assert compute_trust_score(0.20) == 100.0
    assert compute_trust_score(-0.25) == 0.0
    print("Trust score mapping checks passed.")


if __name__ == "__main__":
    main()
