# JOURNAL 1 — YATHARTH
# Engineering Work Journal — Yatharth Kansal

## Week 1: Project Setup and Privacy-Preserving Keyboard Data Collection
**Student Name:** Yatharth Kansal  
**Roll Number:** `1024030456`  
**Role:** Machine Learning Pipeline, Biometric Feature Engineering & Trust Scoring Engine Lead  
**Project:** Adaptive Continuous Authentication (ACA)  
**Supervisor:** Prof. Asif  

### Order of Work

---

## Error:
## Week 1: High-Precision Monotonic Event Logging & Hardware-Level Keystroke Interception

During the initial development of the Adaptive Continuous Authentication system, the main challenge was establishing a keyboard-data collection mechanism that could capture the timing information required for behavioral authentication **without storing plaintext keystrokes**.
### 1. Problem Addressed
In behavioral keystroke biometrics, individual typing rhythms depend on microsecond-level timing differences. Conventional Python timing implementations using `time.time()` or wall-clock epoch timers suffer from clock skew, NTP synchronizations, and operating system sleep-state adjustments. Furthermore, standard keyboard listeners log plaintext characters, creating serious privacy vulnerabilities. The challenge was building an OS-level keyboard collector that captures microsecond-precise timings while completely anonymizing physical keys.

A conventional keyboard logger would store the actual keys typed by the user, which would introduce unnecessary privacy and security risks.
### 2. Technical Context & Investigation
Keystroke biometrics requires tracking two fundamental hardware events for every key: `press` (keydown) and `release` (keyup). We investigated low-level event interception using the cross-platform `pynput` library. To prevent timing anomalies, we replaced wall-clock time with `time.perf_counter()`, a high-resolution monotonic timer with sub-microsecond precision unaffected by system clock shifts.

---
### 3. Key Observations & Design Decisions
- **Behavior over Content:** Continuous authentication requires knowing *how* a person types (timing intervals, cadence, duration), not *what* words they type.
- **Client-Side Pseudonymization:** To prevent keylogging, each physical key code is hashed using HMAC-SHA256 with an ephemeral 32-byte secret key (`key_hash_secret.bin`). The raw alphanumeric value is discarded immediately.

## Relevant Context
### 4. Implementation Details
Developed `code/collectors/keyboard_logger.py`:
- Configured `pynput.keyboard.Listener` to capture asynchronous `on_press` and `on_release` callbacks.
- Computed elapsed time in milliseconds: `elapsed_ms = (time.perf_counter() - session_start) * 1000`.
- Categorized keys into `character` (letters/numbers) and `special` (modifiers/navigation).
- Persisted events into structured CSV records (`timestamp`, `elapsed_ms`, `event`, `key_id`, `key_type`).

The project requires keyboard behavioral information such as:
### 5. Outcome & Verification
Successfully collected baseline session `U01/S01` and `U01/S02`. Confirmed that timestamps monotonically increase with zero negative deltas and verified that raw characters are completely absent from the CSV output.

- Key press events
- Key release events
- Event timestamps
- Key-to-event association

However, the system does not need to know the actual text entered by the user.

Therefore, the collection mechanism was designed around **privacy-preserving pseudonymous key identification**.

The implemented flow is:

```text
Keyboard Event
      ↓
pynput Listener
      ↓
Press / Release + Timestamp
      ↓
HMAC-SHA256
      +
32-byte Local Secret
      ↓
Pseudonymous Key Identifier
      ↓
Local Data Storage
```

---

## Key Observation
## Week 2: Keystroke Biometric Mathematics & 10-Second Sliding Window Feature Engineering

The important observation was that the authentication system is interested in **how a person types**, rather than **what a person types**.
### 1. Problem Addressed
Raw event streams consisting of thousands of discrete `press` and `release` rows cannot be directly ingested by machine learning algorithms. The challenge was designing a robust mathematical feature extractor that groups irregular, asynchronous keystrokes into fixed temporal windows and extracts descriptive behavioral biometric statistics.

Therefore, the key itself can be represented using a pseudonymous identifier while retaining the timing information needed for behavioral analysis.
### 2. Technical Context & Investigation
We investigated sliding vs. fixed temporal windowing techniques. A fixed 10-second temporal slice ($10,000\text{ ms}$) was selected as the optimal trade-off between user friction (rapid anomaly detection) and statistical stability (capturing sufficient keystrokes to establish cadence). 

For example:
### 3. Key Observations & Design Decisions
- **Asymmetric Key Pairing:** Users often press a second key before releasing the first (rollover/n-key rollover). A simple sequential stack fails; keys must be tracked in a dictionary by their hashed `key_id` to compute exact dwell times.
- **Flight Time Definition:** Flight time is measured specifically character-to-character: from the release of character key $k_n$ to the press of subsequent character key $k_{n+1}$.

```text
Actual Key
    ↓
HMAC-SHA256 + Secret
    ↓
Pseudonymous Identifier
```
### 4. Implementation Details
Authored `code/src/features/keystroke_features.py`:
- **Dwell (Hold) Time:** Maintained an active keys map and computed $T_{\text{hold}} = t_{\text{release}} - t_{\text{press}}$.
- **Flight Time:** Tracked the last released character timestamp and computed $T_{\text{flight}} = t_{\text{press}}(k_{n+1}) - t_{\text{release}}(k_n)$.
- **Window Aggregation (`create_behavior_windows`):** Sliced the session into 10-second behavioral windows and computed 5 core features:
  1. `characters_per_second` ($N_{\text{chars}} / 10.0$)
  2. `mean_hold_ms`
  3. `std_hold_ms` (motor consistency jitter)
  4. `mean_flight_ms`
  5. `pause_count` (frequency of flight times $>500\text{ ms}$)
- Added active window gating: `is_active = (character_count >= 5)`.

This allows related key events to be associated without intentionally storing plaintext key values.
### 5. Outcome & Verification
Processed raw session `U01/S02` into `code/data/processed/keyboard_window_features.csv`, yielding 6 active 10-second windows and 1 idle window. Unit tests verified that hold times and flight times remain non-negative under all typing conditions.

---

## Solution
## Week 3: Scikit-Learn Machine Learning Pipeline & One-Class Isolation Forest Architecture

A keyboard listener was implemented using `pynput`.
### 1. Problem Addressed
Traditional binary classifiers (Random Forests, Logistic Regression, SVMs) require labeled training data for both legitimate users (Class 0) and adversaries (Class 1). In production continuous authentication, future imposter typing data is fundamentally unavailable. Furthermore, sparse behavioral windows occasionally produce missing values (e.g. windows with no pauses), which break traditional ML estimators.

The listener captures keyboard press and release events and records their timing information.
### 2. Technical Context & Investigation
We formulated the authentication task as an **Unsupervised Anomaly Detection / One-Class Classification** problem. We evaluated One-Class SVM, Local Outlier Factor (LOF), and Isolation Forest. **Isolation Forest** was selected because it partitions anomalies with shorter path lengths in randomized trees, exhibits linear time complexity $\mathcal{O}(n)$, runs inference in $<1\text{ ms}$, and avoids complex kernel distance calculations.

A locally generated **32-byte secret** is used with **HMAC-SHA256** to generate pseudonymous identifiers.
### 3. Key Observations & Design Decisions
- **Encapsulated Pipeline:** Feature normalization, missing value imputation, and inference must be bundled into a single deployable object to eliminate training-serving skew.
- **Median Imputation:** Missing standard deviations or timing metrics must be imputed using median values rather than zero or mean to preserve robustness against extreme hesitation outliers.

The collected event information is then written into:
### 4. Implementation Details
Authored `code/src/models/train_model.py` and `code/src/models/config.py`:
- Defined the shared feature contract: `ML_FEATURES = ['characters_per_second', 'mean_hold_ms', 'std_hold_ms', 'mean_flight_ms', 'pause_count']`.
- Constructed an integrated Scikit-Learn `Pipeline`:
  ```python
  Pipeline([
      ('imputer', SimpleImputer(strategy='median')),
      ('scaler', StandardScaler()),
      ('isolation_forest', IsolationForest(
          n_estimators=100,
          contamination='auto',
          random_state=42
      ))
  ])
  ```
- Built `train_and_save()` to fit on legitimate active windows and serialize the pipeline to `code/models/anomaly_model.pkl` via `joblib`.
- Created an inference API wrapper in `code/src/models/predict.py`.

```text
keyboard.csv
```
### 5. Outcome & Verification
Successfully trained the model pipeline on baseline windows. Verified that the serialized model artifact loads cleanly, ingests raw feature dictionaries, and executes prediction calls in $<0.8\text{ ms}$.

The basic collection pipeline is therefore:

```text
pynput
   ↓
Keyboard Press / Release
   ↓
Timestamp
   ↓
HMAC-SHA256 Key Identifier
   ↓
keyboard.csv
```

---

## Because
## Week 4: Continuous Trust-Scoring Mathematical Mapping & Speed-Baseline Empirical Diagnosis

HMAC-SHA256 provides a deterministic pseudonymous representation when the same secret is used, allowing the system to associate events while avoiding direct plaintext key storage.
### 1. Problem Addressed
The raw `decision_function()` of Isolation Forest outputs unbounded decision values approximately in $[-0.10, +0.10]$. Security operators and web dashboards cannot easily interpret abstract negative floats. Furthermore, initial live monitoring tests showed unexpectedly low trust scores (~48%) even when typing consistently. The challenge was deriving a normalized continuous trust metric (0–100%) and mathematically diagnosing the root cause of the live scoring behavior.

The secret is kept locally and is not intended to be exposed through the public Git repository.
### 2. Technical Context & Investigation
We analyzed the empirical distribution of the training data (`U01/S02`) against live typing:
- **`U01/S02` Training Distribution (6 windows):** Speed was $0.5 - 2.6\text{ chars/sec}$ (~6–25 WPM), dwell was $99 - 124\text{ ms}$, flight was $265 - 1156\text{ ms}$, and pause count was $1 - 6$.
- **Live Fluent Typing:** Speed was $3.5 - 5.5\text{ chars/sec}$ (~45–65 WPM), dwell was $50 - 75\text{ ms}$, flight was $80 - 150\text{ ms}$, and pause count was $0$.
Because the 100 isolation trees were fitted to only 6 slow-tempo windows, normal fluent typing landed $>2.5$ standard deviations away in feature space, triggering outlier classifications.

This approach also supports the project's privacy-preserving objective.
### 3. Key Observations & Design Decisions
- **Mathematical Validation:** When we fed slow, deliberate typing (Speed 1.8, Dwell 105ms, Flight 350ms, Pauses 3) into the model, it scored $+0.0960$ ($98.0\%$ Trust, `TRUSTED`). This proved the mathematical anomaly engine was functioning with 100% accuracy, but was overfitted to a narrow slow-tempo enrollment.
- **Continuous Trust Mapping:** A clipped linear mapping maps $s \in [-0.10, +0.10]$ to $[0, 100]$:
  $$\text{Trust Score} = \text{clip}\left(50.0 + \frac{s}{0.10} \times 50.0, \; 0.0, \; 100.0\right)$$

---
### 4. Implementation Details
- Authored `code/src/scoring/trust_score.py`: Implemented linear score conversion, guaranteeing that neutral decision boundary ($s=0.0$) maps exactly to $50.0\%$.
- Authored `code/src/authentication/decision.py`: Formulated a 3-tier policy engine:
  - $\text{Score} \ge 70.0 \to \text{TRUSTED} \implies \texttt{ALLOW}$
  - $40.0 \le \text{Score} < 70.0 \to \text{VERIFY} \implies \texttt{PROMPT\_REAUTH}$
  - $\text{Score} < 40.0 \to \text{REJECT} \implies \texttt{LOCK\_SESSION}$
- Integrated end-to-end evaluation logic in `code/src/authentication/engine.py`.

## Development Setup

The project development environment was established using a Python virtual environment.

The required project dependencies were installed and the project structure was organized so that keyboard collection and later processing could be developed as separate components.

---

## Version Control

Git was initialized for the project and the initial implementation was committed.

The project was then connected to GitHub and pushed to the remote repository.

The major commands used included:

```text
git init
git status
git branch -M main
git add .
git commit
git remote add origin
git push -u origin main
```

A `.gitignore` was also configured so that sensitive/generated data and the virtual environment were not unnecessarily committed to the repository.

---

## Outcome

At the end of this stage, the project had:

- Working Python development environment
- Keyboard event listener
- Press/release event capture
- Timestamp collection
- HMAC-SHA256 pseudonymous key identification
- Local 32-byte secret
- CSV event storage
- Git repository
- GitHub repository
- Initial privacy protection for collected behavioral data

The completed collection foundation can now provide data to the feature-engineering stage.
### 5. Outcome & Verification
Tested the unified engine across synthetic and recorded data. Validated that slow baseline typing produces `ALLOW` (98%), while imposter or out-of-distribution typing immediately drops into `VERIFY` (48%) or `REJECT` (25%). Formulated the operational requirement to collect multi-tempo sessions ($S03, S04$) for broad baseline coverage.
