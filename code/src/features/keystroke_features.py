import os
from pathlib import Path
import numpy as np
import pandas as pd

REQUIRED_COLUMNS = {
    "timestamp",
    "elapsed_ms",
    "event",
    "key_id",
    "key_type",
}


def load_keyboard_data(file_path):
    """Load and sort raw keystroke CSV ensuring chronological order."""
    df = pd.read_csv(file_path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    return df.sort_values("elapsed_ms").reset_index(drop=True)


def calculate_key_timings(df):
    """
    Calculate dwell (hold) time per key and character-to-character flight times.
    
    Hold time: t_release - t_press for each key press/release pair.
    Flight time: t_press(k_{n+1}) - t_release(k_n) between consecutive characters.
    """
    active_keys = {}
    hold_records = []

    # Calculate hold/dwell times with rollover support
    for _, row in df.iterrows():
        key_id = row["key_id"]
        event = row["event"]
        elapsed = row["elapsed_ms"]
        key_type = row["key_type"]

        if event == "press":
            active_keys[key_id] = {
                "press_time": elapsed,
                "key_type": key_type,
            }
        elif event == "release":
            if key_id not in active_keys:
                continue

            press_info = active_keys.pop(key_id)
            hold_time = elapsed - press_info["press_time"]

            # Filter out corrupt/negative timing anomalies
            if hold_time >= 0:
                hold_records.append({
                    "press_time": press_info["press_time"],
                    "release_time": elapsed,
                    "hold_time_ms": hold_time,
                    "key_type": press_info["key_type"],
                })

    hold_df = pd.DataFrame(hold_records)

    # Calculate flight times between consecutive character releases and presses
    character_events = df[df["key_type"] == "character"].sort_values("elapsed_ms")
    last_char_release = None
    flight_records = []

    for _, row in character_events.iterrows():
        event = row["event"]
        elapsed = row["elapsed_ms"]

        if event == "release":
            last_char_release = elapsed
        elif event == "press" and last_char_release is not None:
            flight_time = elapsed - last_char_release
            if flight_time >= 0:
                flight_records.append({
                    "press_time": elapsed,
                    "flight_time_ms": flight_time,
                })

    flight_df = pd.DataFrame(flight_records)
    return hold_df, flight_df


def create_behavior_windows(df, hold_df, flight_df, window_size_ms=10000):
    """Slice a session into fixed-size temporal windows and compute summary statistics."""
    if len(df) == 0:
        return pd.DataFrame()

    session_end = df["elapsed_ms"].max()
    window_records = []
    window_start = 0

    while window_start < session_end:
        window_end = window_start + window_size_ms

        # Filter events and timings belonging to this window
        window_events = df[(df["elapsed_ms"] >= window_start) & (df["elapsed_ms"] < window_end)]
        window_holds = hold_df[(hold_df["press_time"] >= window_start) & (hold_df["press_time"] < window_end)] if not hold_df.empty else pd.DataFrame()
        window_flights = flight_df[(flight_df["press_time"] >= window_start) & (flight_df["press_time"] < window_end)] if not flight_df.empty else pd.DataFrame()

        press_count = int(window_events["event"].eq("press").sum())
        release_count = int(window_events["event"].eq("release").sum())

        # Hold time distribution statistics
        if not window_holds.empty:
            mean_hold = float(window_holds["hold_time_ms"].mean())
            std_hold = float(window_holds["hold_time_ms"].std()) if len(window_holds) > 1 else 0.0
            median_hold = float(window_holds["hold_time_ms"].median())
        else:
            mean_hold = np.nan
            std_hold = np.nan
            median_hold = np.nan

        # Flight time distribution statistics
        if not window_flights.empty:
            mean_flight = float(window_flights["flight_time_ms"].mean())
            std_flight = float(window_flights["flight_time_ms"].std()) if len(window_flights) > 1 else 0.0
            median_flight = float(window_flights["flight_time_ms"].median())
        else:
            mean_flight = np.nan
            std_flight = np.nan
            median_flight = np.nan

        # Typing cadence and character throughput
        char_presses = window_events[(window_events["event"] == "press") & (window_events["key_type"] == "character")]
        char_count = len(char_presses)
        chars_per_sec = char_count / (window_size_ms / 1000.0)

        # Hesitation / long pause detection (> 500 ms)
        pause_count = int((window_flights["flight_time_ms"] > 500).sum()) if not window_flights.empty else 0

        # Active typing threshold: windows with < 5 chars are flagged inactive
        is_active = char_count >= 5

        window_records.append({
            "window_start_ms": window_start,
            "window_end_ms": window_end,
            "is_active": is_active,
            "press_count": press_count,
            "release_count": release_count,
            "character_count": char_count,
            "characters_per_second": chars_per_sec,
            "mean_hold_ms": mean_hold,
            "std_hold_ms": std_hold,
            "median_hold_ms": median_hold,
            "mean_flight_ms": mean_flight,
            "std_flight_ms": std_flight,
            "median_flight_ms": median_flight,
            "pause_count": pause_count,
        })
        window_start = window_end

    return pd.DataFrame(window_records)


def main():
    input_file = "data/raw/own/U01/S02/keyboard.csv"
    output_dir = "data/processed"
    output_file = os.path.join(output_dir, "keyboard_window_features.csv")

    os.makedirs(output_dir, exist_ok=True)
    print(f"Loading raw keystroke data from: {input_file}")
    df = load_keyboard_data(input_file)
    print(f"Total events loaded: {len(df)}")

    hold_df, flight_df = calculate_key_timings(df)
    print(f"Hold observations: {len(hold_df)} | Flight observations: {len(flight_df)}")

    print("Generating 10-second behavioral windows...")
    window_df = create_behavior_windows(df, hold_df, flight_df)
    window_df.to_csv(output_file, index=False)

    print("\n" + "=" * 50)
    print(f"Feature extraction complete. Windows generated: {len(window_df)}")
    print(f"Output saved to: {output_file}")
    print("=" * 50)


if __name__ == "__main__":
    main()
