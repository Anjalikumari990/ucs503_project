# Engineering Work Journal — Yatharth Kansal

**Student Name:** Yatharth Kansal  
**Roll Number:** `1024030456`  
**Role:** Machine Learning Pipeline, Biometric Feature Engineering & Trust Scoring Engine Lead  
**Project:** Adaptive Continuous Authentication (ACA)  
**Supervisor:** Prof. Asif (Dr. Jeelani Asif)  
**Course:** UCS503P: Software Engineering Project, TIET Patiala  

> [!TIP]
> **Consolidated PDF:** The complete team journals for all 4 weeks are available in a single executive document:  
> 📄 **[Download Consolidated Engineering Journals PDF](../../Consolidated_Engineering_Journals.pdf)**

---

## Weekly Engineering Logs

### Week 1: High-Precision Monotonic Event Logging & Privacy-Preserving Collection
- **Implementation & Context:** Engineered the low-level event interception collector ([`keyboard_logger.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/collectors/keyboard_logger.py)) using `pynput`, replacing standard wall-clock timers with sub-microsecond monotonic timing (`time.perf_counter()`).
- **Privacy Architecture:** Implemented client-side HMAC-SHA256 pseudonymization with an ephemeral 32-byte secret (`key_hash_secret.bin`), discarding raw alphanumeric characters immediately to eliminate keylogger liabilities.
- **Outcome & Verification:** Successfully recorded baseline sessions (`U01/S01`, `U01/S02`), validating monotonically increasing timestamps with zero negative deltas and 100% absence of plaintext keystrokes.

---

### Week 2: Keystroke Biometric Mathematics & 10-Second Sliding Window Feature Engineering
- **Biometric Mathematics:** Formulated keystroke biometric metrics: dwell/hold time ($T_{\text{hold}} = t_{\text{release}} - t_{\text{press}}$) and character flight time ($T_{\text{flight}} = t_{\text{press}}(k_{n+1}) - t_{\text{release}}(k_n)$) with n-key rollover support.
- **Window Aggregation:** Engineered 10-second temporal sliding windows in [`keystroke_features.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/src/features/keystroke_features.py), extracting 5 core features: typing rate (`characters_per_second`), mean hold (`mean_hold_ms`), hold jitter (`std_hold_ms`), mean flight (`mean_flight_ms`), and pause count (`pause_count`).
- **Activity Gating:** Enforced an active typing threshold (`is_active = character_count >= 5`) to prevent idle pauses from skewing behavioral biometric distributions.

---

### Week 3: Scikit-Learn Machine Learning Pipeline & One-Class Isolation Forest Model
- **Problem Formulation:** Formulated continuous authentication as an unsupervised one-class anomaly detection task, eliminating reliance on non-existent adversary training data.
- **Pipeline Architecture:** Constructed an encapsulated Scikit-Learn `Pipeline` ([`train_model.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/src/models/train_model.py)) integrating median missing-value imputation, standard feature scaling, and an Isolation Forest ensemble (100 estimators).
- **Inference Module:** Serialized the baseline model to `code/models/anomaly_model.pkl` and implemented a low-latency inference module ([`predict.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/src/models/predict.py)) executing predictions in under 0.8 ms.

---

### Week 4: Continuous Trust-Scoring Engine, Anomaly Mapping & Multi-Tempo Diagnosis
- **Continuous Trust Mapping:** Derived a clipped linear score mapping translating raw decision function outputs $[-0.10, +0.10]$ into an intuitive 0–100% continuous trust score in [`trust_score.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/src/scoring/trust_score.py).
- **Security Policy Engine:** Implemented the 3-tier security policy engine in [`decision.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/src/authentication/decision.py): `TRUSTED` ($\ge 70\% \implies \texttt{ALLOW}$), `VERIFY` ($40\text{--}69\% \implies \texttt{PROMPT\_REAUTH}$), and `REJECT` ($<40\% \implies \texttt{LOCK\_SESSION}$).
- **Empirical Diagnostics:** Diagnosed scoring variations between slow-tempo training data and fluent live typing, mathematically validating model behavior and defining multi-tempo calibration steps.

---

## Core Deliverables & Verified Artifacts
- **Data Collection:** [`code/collectors/keyboard_logger.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/collectors/keyboard_logger.py)
- **Feature Extraction:** [`code/src/features/keystroke_features.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/src/features/keystroke_features.py)
- **Model Training & Inference:** [`code/src/models/train_model.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/src/models/train_model.py), [`code/src/models/predict.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/src/models/predict.py)
- **Scoring & Decision Core:** [`code/src/scoring/trust_score.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/src/scoring/trust_score.py), [`code/src/authentication/decision.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/src/authentication/decision.py), [`code/src/authentication/engine.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/src/authentication/engine.py)
- **Trained Model Artifact:** `code/models/anomaly_model.pkl`
