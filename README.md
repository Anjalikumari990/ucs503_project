# Adaptive Continuous Authentication

UCS503 project by **Anjali Kumari and Yatharth Kansal**, Thapar Institute of Engineering and Technology.

A keyboard-only authentication prototype with a Flask dashboard connected to the existing keystroke feature extractor, saved Isolation Forest pipeline, trust scorer, and decision engine. The UI follows the supplied dark navy / emerald dashboard reference.

## Run the dashboard

Use Python 3.12 or newer. From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-ui.txt
.venv/bin/python code/main.py
```

Open **http://127.0.0.1:5000**. On Windows, use `.venv\Scripts\python` in place of `.venv/bin/python`.

Prototype credentials: **anjali / password123**.

For Anjali's U02 desktop recordings and presentation rehearsal, follow the
[recording and demo checklist](docs/recording-and-demo-checklist.md). The collector
uses `code/requirements-collector.txt` and saves CSVs separately from the dashboard.

If port 5000 is occupied, run `PORT=5050 .venv/bin/python code/main.py` and open port 5050 instead.

## Present the project

1. Sign in. The dashboard starts without fabricated measurements or a preset trust score.
2. Select **Replay recorded session** to evaluate the seven windows already committed in `code/data/processed/keyboard_window_features.csv`. Playback is accelerated to one recorded window per second; chart timestamps represent the original 10-second windows. The saved model produces reject, verify, and trusted decisions. The final idle window preserves the previous trust score.
3. Select **Start monitoring**, then type naturally in the keyboard activity area. Every 10 seconds, the actual backend extracts keyboard features and returns a score. A window needs at least five character presses to be active.
4. Watch typing cadence, mean hold time, hold-time standard deviation, flight time, pauses, the trust graph, and the recent decision log update.
5. **Stop session** ends capture and discards the unfinished window. Switching tabs also pauses capture. Starting again begins a new timeline. Signing out clears the dashboard session.

Monitoring is limited to the typing area. No mouse, app usage, or background keyboard monitoring is added. The browser creates a temporary HMAC-SHA256 key and sends only hashed key IDs, event types, key categories, and relative timings. Typed text is never transmitted or persisted. Repeats and composition events are excluded. Live timings use complete observations available within each window; a key held across a window boundary may not contribute a hold-time observation. The existing desktop collector remains available separately and is not started by the web UI.

## Backend integration

- `code/main.py`: existing prototype login plus authenticated dashboard API endpoints; bounded, in-memory per-session history.
- `code/engine_adapter.py`: a thin adapter around the existing `calculate_key_timings`, `create_behavior_windows`, and `evaluate_window` functions. It handles empty timing frames and preserves trust on idle windows.
- `code/templates/` and `code/static/`: responsive sign-in and dashboard UI, keyboard timing capture, SVG gauge and history, and accessible status/error feedback. No external frontend libraries, CDNs, fonts, or build step are needed.
- `code/collectors/`, `code/src/`, `code/models/`, and `code/data/`: teammate's original keyboard pipeline, model, and recorded dataset. The web app now lives alongside these existing backend components.

The displayed response thresholds follow the implemented backend: **trust ≥ 70: allow**, **40 ≤ trust < 70: prompt re-authentication**, **trust < 40: recommend locking**. These differ from the earlier four-band proposal. The interface reports the actual engine's recommendations; it does not claim to perform MFA or enforce session locking.

The model was trained on only six active recorded windows. Scores are a prototype policy mapping, not identity probabilities or measured accuracy. The demo login does not enroll or train a personal baseline. History is temporary, isolated per browser session, capped at 120 windows, and expires after one hour of inactivity or a server restart. The local dashboard uses one server process; it is intended for the course demonstration.

## Validation

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Integration tests compare all recorded replay outputs against the existing stateful authentication engine and check live feature calculations, sparse/idle windows, session isolation, authentication, input validation, explicit engine failures, and logout.

The UI was also exercised in Chrome with actual typing, recorded replay, stop/restart, refresh, sign-out, and layouts from 320px to 1440px. Browser checks confirmed that transmitted events contain HMAC identifiers and timing fields, with no text content.

The separate `code/requirements.txt` is the teammate's broader development environment; `requirements-ui.txt` contains the minimal dashboard/model runtime and matches the saved model's scikit-learn version.
