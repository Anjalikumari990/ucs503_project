# JOURNAL — Anjali Kumari
# Engineering Work Journal — Anjali Kumari

## Week 1: Keystroke Feature Extraction and Behavioral Window Design
**Student Name:** Anjali Kumari  
**Roll Number:** `1024030457`  
**Role:** Frontend Dashboard, Flask REST API & Real-Time System Integration Lead  
**Project:** Adaptive Continuous Authentication (ACA)  
**Supervisor:** Prof. Asif  

### Order of Work

---

## Error:
## Week 1: Flask Application Architecture, Session Security & State Isolation

After establishing the keyboard-event collection pipeline, the next challenge was determining how the collected events could be converted into meaningful **behavioral biometric information**.
### 1. Problem Addressed
A continuous authentication system requires a web server to receive streaming batches of telemetry, evaluate risk, and return dynamic scores without leaking data between concurrent user sessions. Using global variables would create race conditions and session hijacking vulnerabilities. The challenge was architecting an asynchronous-safe, multi-tenant Flask backend with hardened security headers and CSRF protection.

Raw press/release events alone are not directly useful for continuous authentication.
### 2. Technical Context & Investigation
We analyzed state management strategies in Flask. Because the prototype evaluates real-time sessions locally, an in-memory session cache bounded by a thread-safe `RLock()` was chosen. To prevent cross-site request forgery (CSRF) on streaming endpoints, an explicit custom header (`X-CSRF-Token`) validated via constant-time string comparison (`secrets.compare_digest`) was mandated.

The system needs to transform the events into measurable characteristics that describe the user's typing behavior.
### 3. Key Observations & Design Decisions
- **Session Bounding:** Unbounded history arrays cause memory exhaustion. Each active dashboard session is capped at a rolling buffer of 120 windows and automatically expired after 1 hour of inactivity.
- **Defensive API Guards:** Every `/api/*` route is gated behind `is_authenticated()` checks. Unauthenticated requests are immediately rejected with HTTP 401.

---
### 4. Implementation Details
Developed `code/main.py` and `code/auth.py`:
- Built an `OrderedDict` state store protected by `threading.RLock()`:
  ```python
  states = OrderedDict()
  state_lock = RLock()
  ```
- Configured secure cookie attributes: `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE='Strict'`, and `MAX_CONTENT_LENGTH=512_000`.
- Built authentication endpoints (`/login`, `/logout`, `/dashboard`) and REST APIs:
  - `POST /api/start`: Resets rolling session history and initializes monitoring mode (`live` or `replay`).
  - `GET /api/state`: Restores the active session score timeline on page refresh.
  - `POST /api/window`: Evaluates incoming 10-second keystroke payloads.

## Relevant Context
### 5. Outcome & Verification
Tested session isolation with automated mock clients. Verified that unauthorized API calls are blocked with HTTP 401, invalid CSRF tokens return HTTP 403, and multiple client sessions maintain isolated score histories.

The purpose of the project is not to identify the content being typed.

Instead, the system needs to measure characteristics such as:

- How long keys are held
- How quickly consecutive characters are typed
- Typing rate
- Pausing behavior
- Statistical variation in typing patterns

Therefore, the raw keyboard events need to be converted into behavioral features.

The processing flow is:

```text
Raw Keyboard Events
        ↓
Event Pairing
        ↓
Hold / Flight-Time Calculation
        ↓
Feature Extraction
        ↓
10-Second Behavioral Window
        ↓
Behavioral Feature Vector
```

---

## Key Observation
## Week 2: Backend Integration Adapter & Inactive Window Policy Enforcement

A single keystroke does not provide enough information to reliably describe a person's typing behavior.
### 1. Problem Addressed
The core machine learning pipeline expects structured numerical feature vectors. Incoming JSON payloads from the client contain raw, variable-length event batches. Furthermore, users frequently pause typing to read, think, or attend to a notification. In a naïve continuous auth system, zero typing would produce missing features or an immediate false lockout. The challenge was building an intelligent adapter that bridges web payloads with the ML pipeline while implementing an idle leniency policy.

A sequence of keyboard events provides considerably more useful information.
### 2. Technical Context & Investigation
We investigated how to handle idle gaps in behavioral biometrics. If a user types 1 or 2 keys in a 10-second window, the sample size is statistically inadequate to compute reliable standard deviations or cadence. Rather than assigning a zero score or crashing the Scikit-Learn pipeline, the system must recognize insufficient activity and preserve the user's prior trust state.

For example:
### 3. Key Observations & Design Decisions
- **The Inactive Policy:** A window is active only if $N_{\text{characters}} \ge 5$. If active, it passes to the Isolation Forest. If inactive ($<5$ characters), the engine maintains the previous trust score and status without penalty, setting decision to `HOLD`.
- **Extractor Boundary Padding:** Keystroke timings require a terminal boundary event to complete the final window calculation.

```text
Key Press
   ↓
Key Release
   ↓
Hold Time
### 4. Implementation Details
Developed `code/engine_adapter.py`:
- **Payload Validation & Extraction (`keyboard_features`):** Ingests raw client event dictionaries, constructs a pandas DataFrame, executes `calculate_key_timings()`, and injects a boundary marker (`elapsed_ms=9999.999`) to ensure `create_behavior_windows()` generates an exact 10-second slice.
- **Engine Evaluation (`evaluate`):**
  ```python
  def evaluate(features, previous=None):
      result = evaluate_window(features, model=model())
      if not result['is_active'] and previous and previous['trust_score'] is not None:
          for key in ('trust_score', 'status', 'decision'):
              result[key] = previous[key]
      return dict(result, metrics=metrics)
  ```
- Cached model loading using `@lru_cache(maxsize=1)` to avoid reading `anomaly_model.pkl` from disk on every 10-second request.

Character A Release
   ↓
Character B Press
   ↓
Flight Time
```
### 5. Outcome & Verification
Verified that sending an empty event list (`[]`) returns `is_active=False` and holds the previous trust score without error. Verified that sparse events do not cause server-side unhandled exceptions.

By combining several timing measurements into a fixed time window, the system can create a more representative behavioral sample.

---

## Solution
## Week 3: In-Browser Client Keystroke Capture Engine & Web Crypto HMAC Hashing

A feature-extraction pipeline was designed to transform the collected keyboard events into behavioral features.
### 1. Problem Addressed
Continuous authentication requires capturing keystroke timings inside the web browser. However, transmitting actual typed characters to a backend server introduces severe privacy, compliance (GDPR/DPDP), and keylogging liabilities. Furthermore, if a user opens the dashboard in two browser tabs simultaneously, both tabs would stream conflicting keystroke batches into the same session.

The main features include:
### 2. Technical Context & Investigation
We investigated client-side cryptography and modern browser synchronization APIs. We leveraged the W3C **Web Crypto API** (`window.crypto.subtle`) for high-speed hardware-accelerated cryptographic signing directly inside the browser sandbox, and the **Web Locks API** (`navigator.locks`) for single-writer concurrency control across tabs.

### Hold Time
### 3. Key Observations & Design Decisions
- **Zero-Plaintext Streaming:** Before any key event is stored in the client batch, its `event.code` is signed with an ephemeral HMAC-SHA256 key generated at session start. The server only receives 64-character hex hashes and relative microsecond timings.
- **Single Active Tab Guard:** The Web Locks API acquires an exclusive lock (`aca-keyboard-session`). If a user opens a second tab, capture is blocked until the first tab releases the lock.

The time between a key's press and release:
### 4. Implementation Details
Authored the client-side event controller in `code/static/dashboard.js`:
- **Ephemeral HMAC Key Setup:**
  ```javascript
  signingKey = await crypto.subtle.generateKey(
      {name: 'HMAC', hash: 'SHA-256'}, false, ['sign']
  );
  ```
- **Event Interception (`record`):** Attached `keydown` and `keyup` handlers to the monitored typing area. Filtered `event.repeat` and IME composition events. Hashed key codes asynchronously using `crypto.subtle.sign()` and mapped keys to `character` vs `special`.
- **Sliding 10-Second Batching (`tick`):** Managed a high-resolution timer (`performance.now() - origin`). Once elapsed time reaches $10,000\text{ ms}$, the event batch is dispatched to `POST /api/window` using `fetch()` with an `AbortController` timeout.
- **Tab Visibility Pause:** Integrated `document.addEventListener('visibilitychange')` to automatically pause monitoring and discard partial windows when the user switches browser tabs.

```text
Press ───────────── Release
          ↓
       Hold Time
```
### 5. Outcome & Verification
Inspected browser network request payloads via DevTools; confirmed that only 64-character hashes, elapsed milliseconds, and event strings are transmitted. Verified that multi-tab lock contention prevents dual-stream session corruption.

### Character Flight Time

The interval between the release of one character and the press of the next character:

```text
Release A ───────── Press B
             ↓
        Flight Time
```

Additional features include:

- Character count
- Characters per second
- Mean hold time
- Median hold time
- Standard deviation of hold time
- Mean flight time
- Median flight time
- Standard deviation of flight time
- Pause count

---

## Because
## Week 4: Dark-Mode SOC Web Dashboard & Dynamic SVG Data Visualization

Different users can have different typing rhythms.
### 1. Problem Addressed
Security operations center (SOC) operators and evaluators need to visualize continuous trust scores, behavioral cadence, and security policies dynamically. Standard charting libraries (Chart.js, D3.js) introduce heavy external dependencies, CDN vulnerabilities, and render lag. The challenge was building an ultra-fast, zero-dependency, responsive dark-mode dashboard utilizing native SVG vector rendering.

For example, one user may:
### 2. Technical Context & Investigation
We designed a clean, slate-navy cyber-security dashboard with an emerald/amber/crimson state palette conforming to the project proposal. To avoid third-party script bloat, we implemented custom inline SVG mathematics for radial gauge arcs and rolling line charts.

```text
Hold keys longer
Type at a slower rate
Pause frequently
```
### 3. Key Observations & Design Decisions
- **Dynamic Radial Arc:** An SVG circle with `stroke-dasharray="score 100"` dynamically animates the continuous trust score from 0 to 100 with zero canvas rendering overhead.
- **Deterministic Replay Mode:** For project evaluation, evaluators should not have to type for 10 minutes to see lockout policies. An accelerated Replay Mode streams pre-recorded baseline and anomalous windows at 1 window per second.

while another user may:
### 4. Implementation Details
Built `code/templates/dashboard.html` and `code/static/style.css`:
- **Radial Trust Gauge:** Constructed an SVG circular gauge dynamically colored based on status: Green (`TRUSTED`), Amber (`VERIFY`), Red (`REJECT`), or Slate (`INACTIVE`).
- **Rolling Score History Graph:** Created an SVG vector polyline rendering the most recent 40 evaluated windows with gradient fill, grid markings, and horizontal threshold guides at 70% (Trusted) and 40% (Verify).
- **Biometric Telemetry Cards:** Displayed live metrics: typing cadence (CPS), dwell time (ms), dwell jitter ($\sigma$), flight time (ms), and pause frequency.
- **Policy Decision Banner:** Formatted dynamic policy recommendations (`ALLOW`, `PROMPT_REAUTH`, `LOCK_SESSION`).
- **Accelerated Replay Controller:** Connected `POST /api/start {mode: 'replay'}` to stream pre-recorded windows from `code/data/processed/keyboard_window_features.csv`.

```text
Use shorter hold times
Type faster
Pause less frequently
```

These differences can potentially form a behavioral signature that can later be used by an anomaly-detection model.

---

# Behavioral Windowing

To make the behavioral information suitable for continuous authentication, the extracted events were grouped into **10-second windows**.

The structure is:

```text
0s ───────────── 10s
      Window 1

10s ──────────── 20s
      Window 2

20s ──────────── 30s
      Window 3
```

Each window represents one behavioral observation.

This allows the future authentication system to repeatedly evaluate the user's behavior instead of performing authentication only once at login.

---

# Activity Detection

A problem occurs when a user is not actively typing.

A window containing very little keyboard activity should not automatically be considered suspicious.

Therefore, an activity condition was introduced:

```text
Character Count ≥ 5
        ↓
   Active Window
```

If:

```text
Character Count < 5
```

the window is treated as inactive/low activity.

This prevents inactivity from being incorrectly interpreted as an authentication failure.

---

# Long-Pause Detection

Pause behavior was also included as a behavioral feature.

The current project parameter identifies a long pause when:

```text
Flight Time > 500 ms
```

The number of such pauses can then contribute to the behavioral feature vector.

This value is currently a project parameter and can later be evaluated/tuned using the final dataset.

---

# Validation

The complete preprocessing pipeline was tested using collected keyboard-event data.

The observed processing result was:

```text
276 Raw Keyboard Events
          ↓
138 Hold-Time Observations
          ↓
100 Flight-Time Observations
          ↓
7 Behavioral Windows
```

The final low-activity window contained:

```text
1 character
```

and was therefore correctly identified as inactive.

---

# Key Observation

The validation demonstrated that the raw keyboard events could successfully be transformed into structured behavioral information.

The complete process can therefore be represented as:

```text
Raw Events
    ↓
Hold / Flight Measurements
    ↓
Behavioral Features
    ↓
10-Second Windows
    ↓
Activity Detection
    ↓
ML-Ready Behavioral Data
```

The **276 → 138 → 100 → 7** values represent the validation sample and should **not** be presented as the final machine-learning dataset size.

---

# Next Stage

The next stage of the project is to expand the data collection to multiple users/sessions and use the resulting behavioral feature vectors to develop:

```text
User Behavioral Baseline
          ↓
Anomaly Detection
          ↓
Anomaly Score
          ↓
Dynamic Trust Score
          ↓
Adaptive Authentication Decision
```

This will transform the current keyboard feature-extraction pipeline into the complete **Adaptive Continuous Authentication** system.
### 5. Outcome & Verification
Tested the interface across viewport widths from 320px to 2560px. Verified smooth 60fps gauge animations, accurate SVG timeline plotting, instant visual state updates across trust transitions, and seamless replay execution.
