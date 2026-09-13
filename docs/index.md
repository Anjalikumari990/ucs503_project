![Tiet Logo](assets/tiet-logo.svg){ .tiet-logo }

**UCS503P: Software Engineering Project**  
**Thapar Institute of Engineering and Technology, Patiala**

# Adaptive Continuous Authentication & Account-Takeover Detection

**Supervised by**: Prof. Asif (Dr. Jeelani Asif)  
**Authors**:
- **Yatharth Kansal** (`1024030456`) `<ykansal_be24@thapar.edu>`
- **Anjali Kumari** (`1024030457`) `<akumari_be24@thapar.edu>`
- **Ridhi Batra** (`1024030464`) `<rbatra_be24@thapar.edu>`

---

## 📌 Executive Summary

Modern enterprise security is vulnerable to post-authentication compromises:
1. **Unattended workstation takeovers:** Physically accessible unlocked systems.
2. **Session hijacking:** Stolen active bearer tokens or cookies bypass login credentials.
3. **Static perimeter blindspots:** Lack of mid-session identity verification.

**Adaptive Continuous Authentication (ACA)** delivers a **Zero-Trust behavioral intelligence layer** that continuously monitors user keystroke dynamics (dwell time, flight duration, typing cadence, and hesitation frequencies) across 10-second sliding behavioral windows. 

ACA computes a dynamic **Trust Score (0–100%)** using an unsupervised **Isolation Forest** pipeline and executes automated policy responses: transparent access (`ALLOW`), step-up re-authentication (`PROMPT_REAUTH`), or immediate session restriction (`LOCK_SESSION`).

---

## 🏗️ Architectural Flow

```
[Keystroke Events] ──▶ [HMAC-SHA256 Anonymizer] ──▶ [10s Window Extractor]
                                                             │
                                                             ▼
[Security Dashboard] ◀── [Policy Engine] ◀── [Trust Scorer] ◀── [Isolation Forest]
```

### Privacy Guarantee
Actual alphanumeric keystroke content is **never recorded or transmitted**. Client-side HMAC-SHA256 pseudonymization ensures zero-plaintext persistence.

---

## 📊 Engineering Diagrams & Specifications

- **Level 0 & 1 Data Flow Diagram (DFD):** [View Diagram](Diagrams/DFD%20level%200%20and%201.jpg)
- **Level 2 Data Flow Diagram (DFD):** [View Diagram](Diagrams/DFD_Level_2_ACA.jpg)
- **UML Use Case Diagram:** [View Diagram](Diagrams/usecase_Diagram.jpg)
- **Database ER Diagram:** [View PDF](Diagrams/ACA_ER_Diagram.pdf)
- **Swimlane Activity Diagram:** [View PDF](Diagrams/ACA_Swimlane.pdf)
- **Master Gantt Schedule:** [View PDF](ACA_Gantt_Chart.pdf)

---

## 🚀 Quick Navigation

- [Project Selection Criteria](criteria-for-project-selection.md)
- [Recording & Demonstration Checklist](recording-and-demo-checklist.md)
- [Project Repository on GitHub](https://github.com/Anjalikumari990/ucs503_project)
