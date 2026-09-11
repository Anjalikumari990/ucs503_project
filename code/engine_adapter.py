"""Web adapter for the existing keyboard feature and authentication pipeline."""
from functools import lru_cache
from pathlib import Path
import math
import sys

import pandas as pd

CODE_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE_ROOT))

from src.authentication.engine import evaluate_window
from src.features.keystroke_features import calculate_key_timings, create_behavior_windows
from src.models.predict import load_model


@lru_cache(maxsize=1)
def model():
    return load_model()


def recorded_windows():
    return pd.read_csv(CODE_ROOT / 'data/processed/keyboard_window_features.csv')


def keyboard_features(events):
    """Use the team's extractor; normalize empty timing frames for idle windows."""
    if not events:
        return dict(is_active=False, characters_per_second=0, mean_hold_ms=None,
                    std_hold_ms=None, mean_flight_ms=None, pause_count=0, character_count=0)
    frame = pd.DataFrame(events).sort_values('elapsed_ms', kind='stable')
    holds, flights = calculate_key_timings(frame)
    if holds.empty:
        holds = pd.DataFrame(columns=['press_time', 'hold_time_ms'])
    if flights.empty:
        flights = pd.DataFrame(columns=['press_time', 'flight_time_ms'])
    # Ensure the extractor produces one complete 10-second window.
    marker = dict(elapsed_ms=9999.999, event='boundary', key_id='', key_type='special')
    frame = pd.concat([frame, pd.DataFrame([marker])], ignore_index=True)
    return create_behavior_windows(frame, holds, flights).iloc[0].to_dict()


def evaluate(features, previous=None):
    result = evaluate_window(features, model=model())
    # Follow AuthenticationEngine's idle policy without inventing an initial score.
    if not result['is_active'] and previous and previous['trust_score'] is not None:
        for key in ('trust_score', 'status', 'decision'):
            result[key] = previous[key]
    metrics = {}
    for name in ('characters_per_second', 'mean_hold_ms', 'std_hold_ms',
                 'mean_flight_ms', 'pause_count', 'character_count'):
        value = features.get(name)
        metrics[name] = float(value) if value is not None and math.isfinite(float(value)) else None
    return dict(result, metrics=metrics)
