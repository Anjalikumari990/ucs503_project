# Consolidated Engineering Work Journals — UCS503P

**Project Title:** Adaptive Continuous Authentication (ACA)  
**Course:** UCS503P: Software Engineering Project  
**Department:** Computer Science and Engineering Department (CSED)  
**Institution:** Thapar Institute of Engineering and Technology (TIET), Patiala  
**Faculty Supervisor:** Prof. Asif (Dr. Jeelani Asif)  
**Evaluation Stage:** Working Prototype Milestone (September 2026)  
**Repository:** [github.com/Anjalikumari990/ucs503_project](https://github.com/Anjalikumari990/ucs503_project)  

---

## 📄 Executive Consolidated Document
The entire engineering team's weekly logs across all 4 weeks have been synthesized into a single, publication-grade executive PDF complete with verification benchmarks and supervisor review sign-off:

👉 **[Download Consolidated Engineering Work Journals (PDF)](Consolidated_Engineering_Journals.pdf)**

---

## Team Roster & Engineering Ownership

| Student Name | Roll Number | Primary Engineering Domain & Core Module Ownership | Weekly Journal Link |
| :--- | :--- | :--- | :--- |
| **Yatharth Kansal** | `1024030456` | Machine Learning Pipeline, Biometric Feature Extraction & Trust Scoring Engine Lead | [View Journal](1024030456-yatharth/journal.md) |
| **Anjali Kumari** | `1024030457` | Frontend Dashboard, Flask REST API Gateway & Real-Time Client Event Streaming Lead | [View Journal](1024030457-anjali/journal.md) |
| **Ridhi Batra** | `1024030464` | Automated Testing Suite, Privacy Architecture Auditing & Formal IEEE/UML Documentation Lead | [View Journal](1024030464-ridhi/journal.md) |

---

## Summary of 4-Week Engineering Sprints

### Week 1: Foundation, Privacy Interception & Threat Modeling
- **Yatharth:** Engineered `keyboard_logger.py` using `pynput` with monotonic timing (`time.perf_counter()`), HMAC-SHA256 pseudonymization, and zero plaintext logging.
- **Anjali:** Built the multi-session Flask application (`main.py`) with thread-safe `RLock()` caching, HTTP-only cookies, SameSite restrictions, and `X-CSRF-Token` headers.
- **Ridhi:** Formulated the threat model (unattended terminals, token exfiltration), quantitative engineering benchmarks, and authored the formal course proposal in LaTeX.

### Week 2: Feature Engineering, Adapter Pipeline & Privacy Audits
- **Yatharth:** Formulated dwell ($t_{\text{rel}} - t_{\text{press}}$) and flight timing mathematics with n-key rollover; designed 10-second sliding windows with 5 biometric features.
- **Anjali:** Built `engine_adapter.py` bridging client JSON batches with pandas DataFrames, implementing the Inactive Window Policy (`HOLD` score on $<5$ characters).
- **Ridhi:** Audited privacy under GDPR/DPDP 2023 principles, implemented regex path traversal sanitization on CLI arguments, and drafted operational checklists.

### Week 3: Anomaly ML Pipeline, Web Crypto Capture & Test Suite
- **Yatharth:** Formulated unsupervised continuous auth using Scikit-Learn `Pipeline` (median imputation, scaling, Isolation Forest), serializing to `anomaly_model.pkl` ($<0.8\text{ ms}$ inference).
- **Anjali:** Developed browser keystroke capture (`dashboard.js`) using Web Crypto API (`crypto.subtle`) for in-browser HMAC hashing and Web Locks API for tab ownership.
- **Ridhi:** Engineered comprehensive automated test suites (`test_collector.py`, `test_dashboard.py`) with headless mocking, achieving 100% pass rate (11/11 tests).

### Week 4: Trust Scoring, Dark-Mode SOC Dashboard & Prototype Deliverables
- **Yatharth:** Derived continuous trust score mapping ($0\text{--}100\%$), built the 3-tier policy engine (`ALLOW`, `PROMPT_REAUTH`, `LOCK_SESSION`), and diagnosed multi-tempo typing dynamics.
- **Anjali:** Built the responsive dark-mode SOC dashboard (`dashboard.html`, `style.css`) with native SVG radial gauge, 40-window rolling line chart, and accelerated Replay Mode.
- **Ridhi:** Modeled formal IEEE/UML diagrams (DFD Levels 0–2, Use Case, ER Schema, Swimlane), automated Master Gantt schedule (`ACA_Gantt_Chart.xlsx`), and co-authored LaTeX prototype report.
