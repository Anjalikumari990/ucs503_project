import argparse
import csv
import hashlib
import hmac
import os
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path

from pynput import keyboard

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SECRET_FILE = os.path.join(DATA_DIR, "key_hash_secret.bin")


def get_or_create_secret():
    """Load or generate a local 32-byte secret for pseudonymous key hashing."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(SECRET_FILE):
        with open(SECRET_FILE, "rb") as f:
            return f.read()

    secret = secrets.token_bytes(32)
    with open(SECRET_FILE, "wb") as f:
        f.write(secret)
    return secret


def get_key_identifier(key, secret):
    """Compute HMAC-SHA256 digest of key representation so raw chars aren't saved."""
    key_rep = repr(key).encode("utf-8")
    return hmac.new(secret, key_rep, hashlib.sha256).hexdigest()


def get_key_type(key):
    """Classify keystroke into character vs special key."""
    return "character" if isinstance(key, keyboard.KeyCode) else "special"


def main():
    parser = argparse.ArgumentParser(description="Continuous authentication keystroke collector")
    parser.add_argument("--user", required=True, help="User identifier (e.g., U01)")
    parser.add_argument("--session", required=True, help="Session identifier (e.g., S01)")
    args = parser.parse_args()

    for name, value in (("user", args.user), ("session", args.session)):
        if not value or not all(c.isascii() and (c.isalnum() or c in "-_") for c in value):
            parser.error(f"--{name} must contain only letters, numbers, hyphens, or underscores")

    output_dir = os.path.join(DATA_DIR, "raw", "own", args.user, args.session)
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "keyboard.csv")

    if os.path.exists(output_file):
        parser.error(f"Session already exists: {output_file}. Choose a new --session to preserve it.")

    secret = get_or_create_secret()
    session_start = time.perf_counter()

    with open(output_file, "x", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "elapsed_ms", "event", "key_id", "key_type"])

        print("\n" + "=" * 50)
        print(" Adaptive Continuous Authentication - Keystroke Collector")
        print("=" * 50)
        print(f"User:     {args.user}")
        print(f"Session:  {args.session}")
        print("Status:   Recording... (Press ESC to stop)")
        print("Privacy:  Keys are hashed with HMAC-SHA256 (no plaintext stored)\n")

        def record_event(event_type, key):
            now = time.perf_counter()
            elapsed_ms = (now - session_start) * 1000.0
            timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
            writer.writerow([
                timestamp,
                round(elapsed_ms, 3),
                event_type,
                get_key_identifier(key, secret),
                get_key_type(key),
            ])
            f.flush()

        def on_press(key):
            if key == keyboard.Key.esc:
                return False
            record_event("press", key)

        def on_release(key):
            if key == keyboard.Key.esc:
                return
            record_event("release", key)

        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()

    print("\n" + "=" * 50)
    print(f"Recording complete. Saved to: {output_file}")
    print("=" * 50)


if __name__ == "__main__":
    main()
