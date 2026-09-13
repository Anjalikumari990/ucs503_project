# Engineering Work Journal
# Engineering Work Journal — Ridhi Batra

**Student Name:** Ridhi Batra  
**Roll Number:** `1024030464`  
**Role:** Testing, Quality Assurance & Formal Documentation Lead  
**Role:** Testing, Quality Assurance, Privacy Architecture & Formal Documentation Lead  
**Project:** Adaptive Continuous Authentication (ACA)  
**Supervisor:** Prof. Asif  

---

## Weekly Progress Summary
## Week 1: Threat Modeling, Zero-Trust Access Analysis & Course Proposal

### Weeks 1–2: Project Conception & Threat Modeling
- Participated in initial project selection and problem formulation discussions.
- Researched post-authentication threat vectors (unattended workstation hijacking, token replay).
- Formulated test scenarios and edge cases for evaluation.
### 1. Problem Addressed
Traditional authentication models verify user identity exclusively at login, creating a blindspot where unattended workstations, stolen cookies, or physical takeovers operate with perpetual trust. The challenge was formally defining the threat landscape, articulating why point-in-time perimeter authentication fails, and establishing rigorous, measurable software engineering objectives for the UCS503P Capstone proposal.

### Weeks 3–4: Security Validation & Collector Protocols
- Reviewed client-side HMAC-SHA256 pseudonymization design to verify zero plaintext keystroke persistence.
- Formulated testing boundaries for path traversal and data sanitization.
- Documented data recording checklists for pilot users.
### 2. Technical Context & Investigation
We performed threat modeling across post-authentication attack vectors:
- **Physical Workstation Takeover:** An unlocked terminal is exploited when an authorized employee steps away.
- **Session Token Exfiltration:** Stolen session tokens bypass login-time Multi-Factor Authentication (MFA).
- **Behavioral Imposter Dynamics:** An adversary possessing credentials still exhibits divergent neuromuscular motor patterns (dwell and flight intervals) compared to the genuine user.

### Weeks 5–6: Test Automation & API Verification
- Developed the automated integration test suite (`test_collector.py` and `test_dashboard.py`).
- Verified 100% pass rate across CSRF protection, session isolation, replay determinism, and idle window policies.
- Validated state isolation across multiple browser tabs using Web Locks API.
### 3. Key Observations & Design Decisions
- **Continuous Evaluation:** Security must transition from a static binary state (trusted vs untrusted) to a continuous probability curve.
- **Measurable Benchmarks:** Defined formal metrics for evaluation: Detection Latency (time to flag an imposter), False Positive Rate (FPR), Inactive Window Leniency, and Service Reliability.

### Week 7: Mid-Semester Deliverables & Diagrams
- Co-authored the Mid-Semester Prototype Evaluation Report in LaTeX (`Adaptive_Continuous_Auth_Report_Prototype.tex`).
- Structured formal Software Engineering diagrams (DFD Levels 0-2, Use Case, ER Schema, Swimlane Activity).
- Prepared the master automated Gantt schedule in Excel.
### 4. Implementation Details
- Authored the project proposal document in LaTeX (`project-proposal/main.tex` and compiled `main.pdf`).
- Formulated the problem statement, technical scope, and engineering roadmap conforming to the course syllabus.
- Drafted the initial evaluation criteria document (`docs/criteria-for-project-selection.md`).

### 5. Outcome & Verification
Presented and submitted the formal project proposal to Prof. Asif; received project approval and established the software engineering milestone schedule.

---

## Week 2: Privacy Architecture Auditing & Data Pipeline Hardening

### 1. Problem Addressed
Continuous biometric tracking poses severe privacy risks if raw keystrokes are recorded, violating user trust and data privacy regulations (e.g., GDPR and India's DPDP Act 2023). Additionally, collecting data through command-line parameters presents security risks such as path traversal attacks. The challenge was auditing the data collection pipeline and implementing strict security hardening.

### 2. Technical Context & Investigation
We conducted a formal security audit of `keyboard_logger.py` and the client-side event processing pipeline. We investigated whether key timing records could be reverse-engineered into plaintext words and analyzed input parameters for directory escape vulnerabilities.

### 3. Key Observations & Design Decisions
- **Non-Invertible Key IDs:** Individual key representations must be salted and hashed with HMAC-SHA256. Without the ephemeral secret key, key hashes cannot be inverted, preventing keystroke reconstruction.
- **Path Traversal Sanitization:** User and session arguments passed to scripts must be restricted strictly to alphanumeric characters and hyphens to prevent path manipulation (e.g. `../../etc/passwd`).

### 4. Implementation Details
- Conducted code-level privacy audits verifying that `key.char` and `key.name` are never written to disk in `keyboard_logger.py`.
- Enforced strict regex input validation on CLI arguments:
  ```python
  if not all(c.isascii() and (c.isalnum() or c in "-_") for c in value):
      parser.error("--user and --session must contain only alphanumeric characters, hyphens, or underscores")
  ```
- Developed operational checklists and privacy protocols for pilot data recording (`docs/recording-and-demo-checklist.md`).

### 5. Outcome & Verification
Verified through string analysis that zero plaintext text exists in CSV files. Confirmed that malicious path arguments like `--user ../../` are rejected with clean exit codes.

---

## Week 3: Automated Integration Test Suite Engineering & Boundary Verification

### 1. Problem Addressed
The continuous authentication architecture combines low-level hardware listeners, feature extractors, a machine learning pipeline, and web REST APIs. Edge cases—such as zero keystrokes, out-of-order events, invalid CSRF tokens, or engine failures—could crash the system during live demonstrations. The challenge was building an automated, comprehensive test suite covering all critical pathways.

### 2. Technical Context & Investigation
We used Python's built-in `unittest` framework and Flask's `test_client()` to construct mock integration and unit tests that execute rapidly without spawning live hardware listeners or requiring external dependencies.

### 3. Key Observations & Design Decisions
- **Mocking Hardware Listeners:** `pynput` listener tests must use stub namespaces to allow headless execution on continuous integration (CI) servers without a physical display.
- **Stateful Engine Verification:** Replay mode must be mathematically verified against the underlying `AuthenticationEngine` to ensure deterministic decision outputs.

### 4. Implementation Details
Developed two comprehensive test suites in `code/tests/`:
- **`test_collector.py` (Collector Security & Integrity):**
  - `test_data_location_is_independent_of_working_directory`: Verifies relative path integrity regardless of execution directory.
  - `test_existing_session_is_preserved`: Ensures existing recordings are never overwritten accidentally.
  - `test_identifiers_cannot_escape_data_directory`: Validates path traversal sanitization.
  - `test_secret_is_reused_and_hashes_do_not_store_key_labels`: Verifies HMAC secret persistence and zero plaintext leakage.
- **`test_dashboard.py` (API, State Machine & Engine Integration):**
  - `test_authentication_and_csrf`: Validates 401 unauthenticated and 403 invalid CSRF blocking.
  - `test_logout_clears_state`: Confirms complete session state cleanup on user sign-out.
  - `test_invalid_input_and_session_isolation`: Verifies that malformed timing payloads return 400 Bad Request.
  - `test_sparse_and_unmatched_events_do_not_crash_extractor`: Confirms edge-case resilience for sparse windows.
  - `test_live_metrics_and_idle_windows`: Verifies the Inactive Window Policy (score held on idle).
  - `test_replay_matches_stateful_engine_and_holds_idle_trust`: Compares replay output against the stateful ML engine.
  - `test_engine_failure_is_explicit`: Validates clean 503 error handling during model unavailability.

### 5. Outcome & Verification
Executed the complete test suite: **11 / 11 tests passed with 100% success in 0.63 seconds**. Verified that all boundary conditions and security protections function flawlessly.

---

## Week 4: Formal Software Engineering Diagrams, Performance Benchmarking & Prototype Report

### 1. Problem Addressed
Software engineering evaluation in UCS503P requires rigorous, publication-grade architectural artifacts (DFDs, UML diagrams, ER schema, Gantt schedule) alongside measured empirical benchmarks for the Mid-Semester Prototype Evaluation Report. The challenge was modeling the multi-layered system using formal software engineering notations and quantifying system performance under load.

### 2. Technical Context & Investigation
We formulated architectural models conforming to IEEE and UML 2.5 standards, capturing the data flows, actor relationships, relational database structures, and concurrent activity threads. We benchmarked system execution times using Python high-resolution timing profilers.

### 3. Key Observations & Design Decisions
- **Multi-Level DFD Decomposition:** A single DFD cannot adequately express both high-level SOC admin boundaries and low-level ML pipeline transformations. A 3-level decomposition (Level 0 Context, Level 1 Process Decomposition, Level 2 ML Pipeline Sub-process) is required.
- **Automated Project Schedule:** Project tracking requires an automated Gantt chart in Excel with dynamic progress calculations and milestone tracking.

### 4. Implementation Details
- **Designed Formal Engineering Diagrams (`docs/Diagrams/`):**
  1. `DFD level 0 and 1.jpg`: Level 0 Context Diagram and Level 1 Detailed Process Decomposition.
  2. `DFD_Level_2_ACA.jpg`: Level 2 Sub-Process Decomposition covering ML feature extraction, trust scoring, and policy dispatch.
  3. `usecase_Diagram.jpg`: UML Use Case diagram with Actors (*Legitimate User*, *Potential Impostor*, *Administrator*) and `<<include>>` / `<<extend>>` relationships.
  4. `ACA_ER_Diagram.pdf`: Relational database schema with keys and cardinalities across `USER`, `SESSION`, `BEHAVIORAL_WINDOW`, `FEATURE_VECTOR`, and `POLICY_DECISION`.
  5. `ACA_Swimlane.pdf`: 3-partition UML Activity / Swimlane diagram across *Client Layer*, *API Gateway*, and *ML Core*.
- **Authored Automated Master Gantt Schedule:** Created `docs/ACA_Gantt_Chart.xlsx` (23 tasks, 5 phases, formulas, conditional formatting) and exported `docs/ACA_Gantt_Chart.pdf`.
- **Benchmarked Prototype Metrics:**
  - Model inference latency: $0.42 - 0.88\text{ ms}$ (Target: $\le 5.0\text{ ms}$)
  - API roundtrip latency: $12.3 - 24.1\text{ ms}$ (Target: $\le 50.0\text{ ms}$)
  - Client HMAC hashing cost: $0.08\text{ ms / key}$ (Target: $\le 1.0\text{ ms}$)
  - Memory consumption: $38.4\text{ MB}$ (Target: $\le 100\text{ MB}$)
- **Co-Authored Mid-Semester Prototype Report:** Written in formal academic LaTeX (`project-report-prototype-stage/Adaptive_Continuous_Auth_Report_Prototype.tex` and compiled `.pdf`).

### 5. Outcome & Verification
Delivered the complete formal software engineering documentation suite and compiled prototype report, fully aligned with the course evaluation rubric. Verified that prototype performance metrics surpass all target specifications.
