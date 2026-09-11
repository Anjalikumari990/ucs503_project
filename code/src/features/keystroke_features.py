import os
import pandas as pd
import numpy as np


REQUIRED_COLUMNS = {
    "timestamp",
    "elapsed_ms",
    "event",
    "key_id",
    "key_type"
}


def load_keyboard_data(file_path):
    """Load and validate raw keyboard data."""

    df = pd.read_csv(file_path)

    missing = REQUIRED_COLUMNS - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    # Make sure events are in chronological order
    df = df.sort_values("elapsed_ms").reset_index(drop=True)

    return df


def calculate_key_timings(df):
    """
    Calculate hold time and character-to-character
    flight time.

    Hold time:
        release - press

    Flight time:
        next character press - previous character release
    """

    # ------------------------------------------------
    # 1. HOLD TIMES
    # ------------------------------------------------

    active_keys = {}

    hold_records = []

    for _, row in df.iterrows():

        key_id = row["key_id"]
        event = row["event"]
        elapsed = row["elapsed_ms"]
        key_type = row["key_type"]

        if event == "press":

            # Store the most recent press.
            active_keys[key_id] = {
                "press_time": elapsed,
                "key_type": key_type
            }

        elif event == "release":

            if key_id not in active_keys:
                continue

            press_info = active_keys.pop(key_id)

            hold_time = (
                elapsed - press_info["press_time"]
            )

            # Ignore impossible/invalid timings
            if hold_time < 0:
                continue

            hold_records.append({
                "press_time": press_info["press_time"],
                "release_time": elapsed,
                "hold_time_ms": hold_time,
                "key_type": press_info["key_type"]
            })

    hold_df = pd.DataFrame(hold_records)

    # ------------------------------------------------
    # 2. FLIGHT TIMES
    # ------------------------------------------------

    character_events = df[
        df["key_type"] == "character"
    ].copy()

    character_events = character_events.sort_values(
        "elapsed_ms"
    )

    last_character_release = None

    flight_records = []

    for _, row in character_events.iterrows():

        event = row["event"]
        elapsed = row["elapsed_ms"]

        if event == "release":

            last_character_release = elapsed

        elif event == "press":

            if last_character_release is not None:

                flight_time = (
                    elapsed - last_character_release
                )

                if flight_time >= 0:

                    flight_records.append({
                        "press_time": elapsed,
                        "flight_time_ms": flight_time
                    })

    flight_df = pd.DataFrame(flight_records)

    return hold_df, flight_df


def create_behavior_windows(
    df,
    hold_df,
    flight_df,
    window_size_ms=10000
):
    """
    Convert a session into fixed-size behavioral windows.

    Default window size = 10 seconds.
    """

    if len(df) == 0:
        return pd.DataFrame()

    session_end = df["elapsed_ms"].max()

    window_records = []

    window_start = 0

    while window_start < session_end:

        window_end = (
            window_start + window_size_ms
        )

        # -----------------------------
        # Events in this window
        # -----------------------------

        window_events = df[
            (df["elapsed_ms"] >= window_start)
            &
            (df["elapsed_ms"] < window_end)
        ]

        # -----------------------------
        # Hold times in this window
        # -----------------------------

        window_holds = hold_df[
            (hold_df["press_time"] >= window_start)
            &
            (hold_df["press_time"] < window_end)
        ]

        # -----------------------------
        # Flight times in this window
        # -----------------------------

        window_flights = flight_df[
            (flight_df["press_time"] >= window_start)
            &
            (flight_df["press_time"] < window_end)
        ]

        # -----------------------------
        # Basic counts
        # -----------------------------

        press_count = (
            window_events["event"]
            .eq("press")
            .sum()
        )

        release_count = (
            window_events["event"]
            .eq("release")
            .sum()
        )

        # -----------------------------
        # Hold-time statistics
        # -----------------------------

        if len(window_holds) > 0:

            mean_hold = (
                window_holds["hold_time_ms"].mean()
            )

            std_hold = (
                window_holds["hold_time_ms"].std()
            )

            median_hold = (
                window_holds["hold_time_ms"].median()
            )

        else:

            mean_hold = np.nan
            std_hold = np.nan
            median_hold = np.nan

        # -----------------------------
        # Flight-time statistics
        # -----------------------------

        if len(window_flights) > 0:

            mean_flight = (
                window_flights["flight_time_ms"].mean()
            )

            std_flight = (
                window_flights["flight_time_ms"].std()
            )

            median_flight = (
                window_flights["flight_time_ms"].median()
            )

        else:

            mean_flight = np.nan
            std_flight = np.nan
            median_flight = np.nan

        # -----------------------------
        # Typing activity
        # -----------------------------

        # Character presses in this window
        character_presses = window_events[
            (window_events["event"] == "press")
            &
            (window_events["key_type"] == "character")
        ]

        character_count = len(character_presses)

        # 10 seconds -> characters per second
        characters_per_second = (
            character_count / (window_size_ms / 1000)
        )

        # -----------------------------
        # Pause detection
        # -----------------------------

        long_pauses = window_flights[
            window_flights["flight_time_ms"] > 500
        ]

        pause_count = len(long_pauses)

        # -----------------------------
        # Save window
        # -----------------------------

        # A window needs enough typing activity
        # before we treat it as a behavioral sample.

        minimum_characters = 5

        is_active = (
            character_count >= minimum_characters
        )

        window_records.append({

            "window_start_ms": window_start,

            "window_end_ms": window_end,

            "is_active": is_active,

            "press_count": press_count,

            "release_count": release_count,

            "character_count": character_count,

            "characters_per_second":
                characters_per_second,

            "mean_hold_ms": mean_hold,

            "std_hold_ms": std_hold,

            "median_hold_ms": median_hold,

            "mean_flight_ms": mean_flight,

            "std_flight_ms": std_flight,

            "median_flight_ms": median_flight,

            "pause_count": pause_count
        })
        window_start = window_end

    return pd.DataFrame(window_records)


def main():

    input_file = (
        "data/raw/own/U01/S02/keyboard.csv"
    )

    output_dir = "data/processed"

    output_file = os.path.join(
        output_dir,
        "keyboard_window_features.csv"
    )

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    print("Loading keyboard data...")

    df = load_keyboard_data(input_file)

    print(
        f"Raw events: {len(df)}"
    )

    print("Calculating key timings...")

    hold_df, flight_df = calculate_key_timings(df)

    print(
        f"Hold observations: {len(hold_df)}"
    )

    print(
        f"Flight observations: {len(flight_df)}"
    )

    print("Creating 10-second behavioral windows...")

    window_df = create_behavior_windows(
        df,
        hold_df,
        flight_df
    )

    window_df.to_csv(
        output_file,
        index=False
    )

    print()
    print("=" * 60)
    print("Feature extraction complete")
    print("=" * 60)

    print()
    print(
        f"Behavioral windows: {len(window_df)}"
    )

    print()
    print("Features:")
    print(window_df.columns.tolist())

    print()
    print("Sample:")
    print(
        window_df.head().to_string(
            index=False
        )
    )

    print()
    print(
        f"Saved to: {output_file}"
    )


if __name__ == "__main__":
    main()