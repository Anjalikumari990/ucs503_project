# Engineering Work Journal — Ridhi Batra

**Student Name:** Ridhi Batra  
**Roll Number:** `1024030464`  
**Role:** Automated Testing Suite, Privacy Architecture Auditing & Formal IEEE/UML Documentation Lead  
**Project:** Adaptive Continuous Authentication (ACA)  
**Supervisor:** Prof. Asif (Dr. Jeelani Asif)  
**Course:** UCS503P: Software Engineering Project, TIET Patiala  

> [!TIP]
> **Consolidated PDF:** The complete team journals for all 4 weeks are available in a single executive document:  
> 📄 **[Download Consolidated Engineering Journals PDF](../../Consolidated_Engineering_Journals.pdf)**

---

## Weekly Engineering Logs

### Week 1: Threat Modeling, Zero-Trust Access Analysis & Course Proposal
- **Threat Landscape Analysis:** Formulated the post-authentication threat model analyzing workstation abandonment, session token exfiltration, and physiological imposter differences.
- **Measurable Benchmarks:** Defined quantitative Capstone engineering benchmarks: detection latency ($\le 5.0\text{s}$), false positive rate ($\le 5.0\%$), inactive leniency, and API overhead.
- **Formal Project Proposal:** Authored and compiled the formal UCS503P project proposal in LaTeX (`project-proposal/main.tex`), securing project approval from supervisor Prof. Asif.

---

### Week 2: Privacy Architecture Auditing & Data Pipeline Hardening
- **Compliance & Privacy Audit:** Conducted strict privacy audits under GDPR and India DPDP Act 2023 principles, verifying mathematical non-invertibility of client-side key hashes.
- **Path Traversal Sanitization:** Hardened command-line collector scripts against directory escape vulnerabilities using strict alphanumeric regex validation on user and session parameters.
- **Operational Protocols:** Drafted standardized operational protocols and recording checklists ([`recording-and-demo-checklist.md`](file:///c:/Users/2206y/adaptive-continuous-auth/docs/recording-and-demo-checklist.md)) for repeatable data collection.

---

### Week 3: Automated Integration Test Suite Engineering & Boundary Verification
- **Automated Test Engineering:** Engineered comprehensive test suites in `code/tests/` ([`test_collector.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/tests/test_collector.py) and [`test_dashboard.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/tests/test_dashboard.py)) using Python `unittest` and Flask mock test clients.
- **Boundary Verification:** Implemented headless listener mocking and boundary verifications for CSRF rejection, session isolation, malformed JSON handling, and inactive window preservation.
- **Outcome & Verification:** Achieved a 100% test pass rate across all 11 unit and integration test cases in 0.63 seconds, validating total system stability and error paths.

---

### Week 4: Formal Software Engineering Diagrams, Performance Benchmarking & Prototype Report
- **Software Engineering Modeling:** Developed publication-grade engineering models conforming to IEEE/UML standards: DFD Levels 0–2, UML Use Case diagram, Relational ER schema, and UML Swimlane Activity diagram.
- **Master Gantt Schedule:** Engineered the Master Gantt schedule ([`ACA_Gantt_Chart.xlsx`](file:///c:/Users/2206y/adaptive-continuous-auth/docs/ACA_Gantt_Chart.xlsx) and PDF) across 23 tasks and 5 phases with dynamic progress formulas.
- **Benchmarking & Report:** Benchmarked prototype runtime metrics ($<0.88\text{ ms}$ inference, $<25\text{ ms}$ API roundtrip, $38.4\text{ MB}$ RAM) and co-authored the Prototype Evaluation Report in LaTeX.

---

## Core Deliverables & Verified Artifacts
- **Automated Test Suites:** [`code/tests/test_collector.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/tests/test_collector.py), [`code/tests/test_dashboard.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/tests/test_dashboard.py)
- **Engineering Diagrams:** `docs/Diagrams/DFD level 0 and 1.jpg`, `docs/Diagrams/DFD_Level_2_ACA.jpg`, `docs/Diagrams/usecase_Diagram.jpg`, `docs/Diagrams/ACA_ER_Diagram.pdf`, `docs/Diagrams/ACA_Swimlane.pdf`
- **Master Gantt Schedule:** `docs/ACA_Gantt_Chart.xlsx`, `docs/ACA_Gantt_Chart.pdf`, `docs/ACA_Gantt_Chart.png`
- **Academic Reports:** `project-proposal/main.tex`, `project-report-prototype-stage/Adaptive_Continuous_Auth_Report_Prototype.tex`
