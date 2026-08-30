# JOURNAL 1 — YATHARTH

## Week 1: Project Setup and Privacy-Preserving Keyboard Data Collection

### Order of Work

---

## Error:

During the initial development of the Adaptive Continuous Authentication system, the main challenge was establishing a keyboard-data collection mechanism that could capture the timing information required for behavioral authentication **without storing plaintext keystrokes**.

A conventional keyboard logger would store the actual keys typed by the user, which would introduce unnecessary privacy and security risks.

---

## Relevant Context

The project requires keyboard behavioral information such as:

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

The important observation was that the authentication system is interested in **how a person types**, rather than **what a person types**.

Therefore, the key itself can be represented using a pseudonymous identifier while retaining the timing information needed for behavioral analysis.

For example:

```text
Actual Key
    ↓
HMAC-SHA256 + Secret
    ↓
Pseudonymous Identifier
```

This allows related key events to be associated without intentionally storing plaintext key values.

---

## Solution

A keyboard listener was implemented using `pynput`.

The listener captures keyboard press and release events and records their timing information.

A locally generated **32-byte secret** is used with **HMAC-SHA256** to generate pseudonymous identifiers.

The collected event information is then written into:

```text
keyboard.csv
```

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

HMAC-SHA256 provides a deterministic pseudonymous representation when the same secret is used, allowing the system to associate events while avoiding direct plaintext key storage.

The secret is kept locally and is not intended to be exposed through the public Git repository.

This approach also supports the project's privacy-preserving objective.

---

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
