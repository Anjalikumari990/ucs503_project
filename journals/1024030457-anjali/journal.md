# Engineering Work Journal — Anjali Kumari

**Student Name:** Anjali Kumari  
**Roll Number:** `1024030457`  
**Role:** Frontend Dashboard, Flask REST API Gateway & Real-Time Client Event Streaming Lead  
**Project:** Adaptive Continuous Authentication (ACA)  
**Supervisor:** Prof. Asif (Dr. Jeelani Asif)  
**Course:** UCS503P: Software Engineering Project, TIET Patiala  

> [!TIP]
> **Consolidated PDF:** The complete team journals for all 4 weeks are available in a single executive document:  
> 📄 **[Download Consolidated Engineering Journals PDF](../../Consolidated_Engineering_Journals.pdf)**

---

## Weekly Engineering Logs

### Week 1: Flask Application Architecture, Session Security & State Isolation
- **Backend Architecture:** Architected the multi-session Flask application ([`main.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/main.py)) with an in-memory session cache bounded by a thread-safe `threading.RLock()` to prevent race conditions.
- **Enterprise Security Controls:** Configured strict web security: HTTP-only cookies, SameSite restrictions, request payload caps (512 KB), and custom `X-CSRF-Token` validation.
- **REST Endpoints:** Built authenticated API routes (`/api/start`, `/api/state`, `/api/window`) in [`auth.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/auth.py), ensuring unauthenticated requests are rejected with HTTP 401.

---

### Week 2: Backend Integration Adapter & Inactive Window Policy Enforcement
- **Pipeline Integration:** Constructed [`engine_adapter.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/engine_adapter.py) to ingest variable-length client JSON event batches and map them into ML-ready pandas DataFrames.
- **Inactive Window Policy:** Implemented the idle leniency policy: if a window contains fewer than 5 characters, the system preserves prior trust status without penalty, setting decision to `HOLD`.
- **Latency Optimization:** Integrated LRU model caching (`@lru_cache`) to avoid repeated disk reads of `anomaly_model.pkl`, sustaining sub-millisecond evaluation cycles.

---

### Week 3: In-Browser Client Keystroke Capture Engine & Web Crypto HMAC Hashing
- **Client-Side Cryptography:** Engineered client-side event interception in [`dashboard.js`](file:///c:/Users/2206y/adaptive-continuous-auth/code/static/dashboard.js) using the W3C Web Crypto API (`crypto.subtle`) for in-browser HMAC-SHA256 signing.
- **Zero-Plaintext Guarantee:** Enforced strict zero-plaintext transmission across the network: only 64-character hexadecimal hashes and microsecond timing deltas are transmitted.
- **Browser Synchronization:** Integrated the Web Locks API (`navigator.locks`) for single-tab session ownership and bound `visibilitychange` listeners to pause monitoring during tab switches.

---

### Week 4: Dark-Mode SOC Web Dashboard & Dynamic SVG Data Visualization
- **SOC Interface Design:** Designed a responsive dark-mode Security Operations Center dashboard ([`dashboard.html`](file:///c:/Users/2206y/adaptive-continuous-auth/code/templates/dashboard.html), [`style.css`](file:///c:/Users/2206y/adaptive-continuous-auth/code/static/style.css)) without external CDN or heavy charting dependencies.
- **Dynamic Vector Visualizations:** Built custom inline SVG components: a real-time radial continuous trust gauge and a 40-window rolling score history line chart with visual threshold zones.
- **Biometric Telemetry & Replay:** Implemented live telemetry cards (CPS, dwell time, dwell jitter, flight time) and an accelerated Replay Mode controller streaming pre-recorded sessions at 1 window/sec.

---

## Core Deliverables & Verified Artifacts
- **Server Application & Gateway:** [`code/main.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/main.py), [`code/auth.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/auth.py)
- **Engine Adapter:** [`code/engine_adapter.py`](file:///c:/Users/2206y/adaptive-continuous-auth/code/engine_adapter.py)
- **Client Capture Engine:** [`code/static/dashboard.js`](file:///c:/Users/2206y/adaptive-continuous-auth/code/static/dashboard.js)
- **Styling & SOC Dashboard:** [`code/static/style.css`](file:///c:/Users/2206y/adaptive-continuous-auth/code/static/style.css), [`code/templates/dashboard.html`](file:///c:/Users/2206y/adaptive-continuous-auth/code/templates/dashboard.html), [`code/templates/login.html`](file:///c:/Users/2206y/adaptive-continuous-auth/code/templates/login.html)
