from functools import lru_cache
from pathlib import Path
import math
import sys
import pandas as pd

CODE_ROOT = Path(__file__).resolve().parent
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from src.authentication.engine import evaluate_window
from src.features.keystroke_features import calculate_key_timings, create_behavior_windows
from src.models.predict import load_model


@lru_cache(maxsize=1)
def model():
    """Cache loaded model pipeline to prevent redundant disk I/O on streaming requests."""
    return load_model()


def recorded_windows():
    """Load benchmark processed windows for replay evaluation mode."""
    return pd.read_csv(CODE_ROOT / "data/processed/keyboard_window_features.csv")


def keyboard_features(events):
    """Transform streaming client keydown/keyup events into a 10-second window feature vector."""
    if not events:
        return {
            "is_active": False,
            "characters_per_second": 0.0,
            "mean_hold_ms": None,
            "std_hold_ms": None,
            "mean_flight_ms": None,
            "pause_count": 0,
            "character_count": 0,
        }

    frame = pd.DataFrame(events).sort_values("elapsed_ms", kind="stable")
    holds, flights = calculate_key_timings(frame)

    if holds.empty:
        holds = pd.DataFrame(columns=["press_time", "hold_time_ms"])
    if flights.empty:
        flights = pd.DataFrame(columns=["press_time", "flight_time_ms"])

    # Inject boundary marker to guarantee full 10-second slice alignment
    marker = {"elapsed_ms": 9999.999, "event": "boundary", "key_id": "", "key_type": "special"}
    frame = pd.concat([frame, pd.DataFrame([marker])], ignore_index=True)

    window_df = create_behavior_windows(frame, holds, flights)
    return window_df.iloc[0].to_dict()


def evaluate(features, previous=None):
    """Evaluate window features through pipeline and maintain prior score on idle windows."""
    result = evaluate_window(features, model=model())

    if not result["is_active"] and previous and previous["trust_score"] is not None:
        for key in ("trust_score", "status", "decision"):
            result[key] = previous[key]

    metrics = {}
    for name in (
        "characters_per_second",
        "mean_hold_ms",
        "std_hold_ms",
        "mean_flight_ms",
        "pause_count",
        "character_count",
    ):
        val = features.get(name)
        metrics[name] = float(val) if val is not None and math.isfinite(float(val)) else None

    return dict(result, metrics=metrics)
