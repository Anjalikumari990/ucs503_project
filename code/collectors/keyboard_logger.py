import csv
import os
import argparse
import hashlib
import hmac
import secrets
import time
from datetime import datetime, timezone

from pynput import keyboard


SECRET_FILE = os.path.join(
    "data",
    "key_hash_secret.bin"
)


def get_or_create_secret():

    os.makedirs("data", exist_ok=True)

    if os.path.exists(SECRET_FILE):

        with open(SECRET_FILE, "rb") as file:
            return file.read()

    secret = secrets.token_bytes(32)

    with open(SECRET_FILE, "wb") as file:
        file.write(secret)

    return secret


def get_key_identifier(key, secret):

    """
    Creates a stable, privacy-preserving identifier
    for a keyboard key.

    The actual key value is never written to the CSV.
    """

    key_representation = repr(key).encode("utf-8")

    return hmac.new(
        secret,
        key_representation,
        hashlib.sha256
    ).hexdigest()


def get_key_type(key):

    if isinstance(key, keyboard.KeyCode):
        return "character"

    return "special"


def main():

    parser = argparse.ArgumentParser(
        description="Keyboard behavioral data collector"
    )

    parser.add_argument(
        "--user",
        required=True
    )

    parser.add_argument(
        "--session",
        required=True
    )

    args = parser.parse_args()

    output_dir = os.path.join(
        "data",
        "raw",
        "own",
        args.user,
        args.session
    )

    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(
        output_dir,
        "keyboard.csv"
    )

    secret = get_or_create_secret()

    session_start = time.perf_counter()

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "timestamp",
            "elapsed_ms",
            "event",
            "key_id",
            "key_type"
        ])

        print()
        print("=" * 55)
        print(" Adaptive Continuous Authentication")
        print("=" * 55)
        print()
        print(f"User:    {args.user}")
        print(f"Session: {args.session}")
        print()
        print("Recording keyboard behavior...")
        print()
        print("Privacy mode:")
        print("- Actual key values are NOT stored")
        print("- Keys are represented by hashed identifiers")
        print()
        print("Use your computer normally.")
        print("Press ESC to stop.")
        print()

        def record_event(event, key):

            now = time.perf_counter()

            elapsed_ms = (now - session_start) * 1000

            timestamp = datetime.now(
                timezone.utc
            ).isoformat(
                timespec="milliseconds"
            )

            writer.writerow([
                timestamp,
                round(elapsed_ms, 3),
                event,
                get_key_identifier(key, secret),
                get_key_type(key)
            ])

            file.flush()

        def on_press(key):

            # ESC is the control key used to stop recording.
            # We don't include it in the behavioral dataset.
            if key == keyboard.Key.esc:
                return False

            record_event("press", key)

        def on_release(key):

            if key == keyboard.Key.esc:
                return

            record_event("release", key)

        with keyboard.Listener(
            on_press=on_press,
            on_release=on_release
        ) as listener:

            listener.join()

    print()
    print("=" * 55)
    print("Session complete.")
    print(f"Saved to: {output_file}")
    print("=" * 55)


if __name__ == "__main__":
    main()