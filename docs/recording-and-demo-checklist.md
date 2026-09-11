# Recording and presentation checklist — Anjali (U02)

## What is ready

The dashboard connects to the existing keyboard feature extractor and trained model. Desktop recording is a separate command that saves CSV files for dataset collection. Typing in the dashboard does **not** save the S01/S02 training sessions.

On this Mac, the virtual environment is `.venv/` in the repository root, not `code/venv/`. The collector dependency has been installed there. No recording is started by installation or by opening the dashboard.

## 1. Prepare the terminal

From this Mac:

```sh
cd /Users/anjali/Desktop/ucs503_project
```

If using another checkout, pull the latest committed changes there first. The setup commands from the repository root are:

```sh
.venv/bin/python -m pip install -r requirements-ui.txt
.venv/bin/python -m pip install -r code/requirements-collector.txt
```

Using the interpreter directly means activation is optional. If you do activate it, use `source .venv/bin/activate` from the repository root or `source ../.venv/bin/activate` from `code/`.

The broader `code/requirements.txt` contains the teammate's full development environment, including Windows-specific packages; it is not needed for this Mac recording/demo setup.

## 2. Verify macOS keyboard permission before the real sessions

The terminal application used to run the desktop collector may need permission to monitor keyboard input. Follow the macOS permission prompt for that application and restart it if requested. The [pynput macOS documentation](https://pynput.readthedocs.io/en/latest/limitations.html#macos) explains the accessibility requirement. Do not use `sudo` as a shortcut.

Do a short throwaway recording first, using a name that is not S01/S02/S03:

```sh
.venv/bin/python code/collectors/keyboard_logger.py --user U02 --session TEST01
```

Type a harmless sentence in a text editor for about 15 seconds, then press **Esc**. Confirm the CSV contains events. If the command reports that TEST01 already exists, use TEST02. The collector now refuses to overwrite existing sessions and always writes under `code/data/`, whichever directory launches it.

The native collector listens to keyboard events across applications until Esc. It records timestamp, elapsed milliseconds, press/release, HMAC key ID, and character/special category. Hold and flight times are calculated later by the feature extractor. HMAC IDs are deterministic with the same local secret; they are not fresh random values for every keystroke. Plaintext key labels and typed text are not written to CSV.

## 3. Record U02 sessions

Run one command at a time from the repository root:

```sh
.venv/bin/python code/collectors/keyboard_logger.py --user U02 --session S01
```

Type naturally for **3–5 minutes**, then press **Esc**. Take a one-minute break.

```sh
.venv/bin/python code/collectors/keyboard_logger.py --user U02 --session S02
```

Repeat for 3–5 minutes. If there is time, record S03 the same way. Use a text editor, assignment notes, or a typing exercise. Keep a normal pace; do not deliberately manufacture anomalies in the baseline sessions.

From inside `code/`, the equivalent command is:

```sh
../.venv/bin/python collectors/keyboard_logger.py --user U02 --session S01
```

## 4. Check and package the files

From the repository root, inspect counts and duration without displaying event contents:

```sh
.venv/bin/python - <<'PY'
import csv
import re
from pathlib import Path

for folder in ('S01', 'S02', 'S03'):
    path = Path('code/data/raw/own/U02') / folder / 'keyboard.csv'
    if not path.exists():
        print(f'{folder}: not recorded')
        continue
    with path.open(newline='') as handle:
        reader = csv.DictReader(handle)
        assert set(reader.fieldnames or []) == {'timestamp', 'elapsed_ms', 'event', 'key_id', 'key_type'}
        rows = list(reader)
    assert rows, f'{folder}: no events — check permissions before continuing'
    assert all(re.fullmatch(r'[0-9a-f]{64}', row['key_id']) for row in rows)
    assert all(row['event'] in ('press', 'release') for row in rows)
    presses = sum(row['event'] == 'press' for row in rows)
    duration = max(float(row['elapsed_ms']) for row in rows) / 1000
    print(f'{folder}: {len(rows)} events, {presses} presses, {duration:.1f}s elapsed, hash format valid')
PY
```

Then zip just the intended recorded CSV files using Finder and share them privately with Yatharth. Exclude the throwaway TEST sessions. Keep `code/data/key_hash_secret.bin` on this computer and retain the same secret across your sessions.

Raw CSVs and the secret are already ignored by Git. There is no need to force-add them to GitHub.

Recording new CSVs does not automatically retrain the model or update dashboard replay. The current feature-extraction script's command-line entry point is hardcoded to U01/S02. Let Yatharth extract and evaluate the new U02 sessions deliberately, keeping the existing model and replay dataset available until the replacement has been verified.

## 5. Presentation rehearsal

From the repository root:

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python code/main.py
```

Open http://127.0.0.1:5000 and sign in with `anjali` / `password123`.

1. Explain the problem: a successful login does not establish who continues using the session.
2. Run **Replay recorded session**. Say that recorded 10-second windows are played back faster for presentation, with actual model inference.
3. Point to the gauge, timing measurements, history, and decision log. The implemented bands are ≥70 allow, 40–<70 verify, and <40 restrict.
4. Click **Start monitoring** and type in the dashboard area for 20–30 seconds. Explain that it sends anonymized timing events every 10 seconds.
5. Stop typing for one full window. Show that idle time holds the previous score.
6. Click **Stop session**. Explain that re-authentication and locking are engine recommendations; enforcement is not implemented.

Do not promise that every second person's typing will trigger rejection. The existing saved model is a small prototype trained on six active windows. Multi-user accuracy claims need the new recordings and a separate evaluation.

## Remaining hands-on work

- Verify input permission in the exact terminal application you will use.
- Record and check two or three U02 sessions, then share the CSVs privately.
- Agree on any requested UI wording/layout refinements and rehearse the entire demo on the presentation laptop.
