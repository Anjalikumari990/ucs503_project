# JOURNAL — Anjali Kumari

## Week 1: Keystroke Feature Extraction and Behavioral Window Design

### Order of Work

---

## Error:

After establishing the keyboard-event collection pipeline, the next challenge was determining how the collected events could be converted into meaningful **behavioral biometric information**.

Raw press/release events alone are not directly useful for continuous authentication.

The system needs to transform the events into measurable characteristics that describe the user's typing behavior.

---

## Relevant Context

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

A single keystroke does not provide enough information to reliably describe a person's typing behavior.

A sequence of keyboard events provides considerably more useful information.

For example:

```text
Key Press
   ↓
Key Release
   ↓
Hold Time

Character A Release
   ↓
Character B Press
   ↓
Flight Time
```

By combining several timing measurements into a fixed time window, the system can create a more representative behavioral sample.

---

## Solution

A feature-extraction pipeline was designed to transform the collected keyboard events into behavioral features.

The main features include:

### Hold Time

The time between a key's press and release:

```text
Press ───────────── Release
          ↓
       Hold Time
```

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

Different users can have different typing rhythms.

For example, one user may:

```text
Hold keys longer
Type at a slower rate
Pause frequently
```

while another user may:

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
