# Product Requirements Document
## AI-Powered Phishing Domain Detector

**Client:** Maryam Var Naseri
**Team:** Mahul Patel, Kartar Singh Johal, Bhupinder Singh
**Programme:** WelTec Capstone Project
**Status:** Draft v1

---

## 1. Overview

Phishing domains are usually only flagged after they've already been used to steal credentials or deliver malware. This product flips that model: it watches domain registration activity as it happens, scores each new domain for risk, and puts that score in front of an analyst before the domain gets used maliciously.

The deliverable is a working prototype, not a production security platform. It needs to prove the detection approach works and be handed over cleanly, not run at internet scale.

---

## 2. Problem Statement

- Phishing domains often live for less than 24 hours before takedown, so traditional blacklists catch them too late.
- Newly Registered Domains (NRDs) have no history, so they slip past reputation-based filters.
- Security teams need a way to assess risk at the moment of registration, not after an incident.

---

## 3. Goals

1. Detect newly registered domains in near real time from public sources.
2. Score each domain 0–100 for phishing risk, with a clear reason for the score.
3. Give analysts a live dashboard to review, filter, and export high-risk domains.
4. Prove the approach works well enough to be credible as a real security tool, not just a class project.

---

## 4. Users

| User | What they need from the product |
|---|---|
| Security analyst (primary) | Live queue of scored domains, filters, export, explanation per score |
| Client (Maryam) | Confidence the tool catches real phishing domains without burying her team in false positives |
| Academic panel | Evidence of a sound technical approach, honest evaluation, and working demo |

---

## 5. Functional Requirements

| ID | Requirement |
|---|---|
| FR1 | System ingests newly registered domains from Certificate Transparency logs and public NRD feeds on a scheduled poll (10–15 min). |
| FR2 | System deduplicates incoming domains and caches WHOIS/hosting lookups to avoid redundant API calls. |
| FR3 | System extracts lexical features (entropy, digit ratio, length, keyword matches), WHOIS metadata, and hosting metadata (IP reputation, ASN, SSL details) for each domain. |
| FR4 | System flags likely brand-impersonation domains (e.g. `paypa1.com`) using lexical similarity checks in the MVP, with semantic embedding similarity as a stretch enhancement if time allows. |
| FR5 | System produces a 0–100 risk score per domain with a ranked list of the top contributing factors. |
| FR6 | Dashboard displays domains in a live queue, filterable by risk level, registration date, and flagged features. |
| FR7 | Analysts can export a list of high-risk domains for escalation. |
| FR8 | System sends a notification (email or webhook) when a domain crosses the high-risk threshold, so review doesn't depend on someone watching the dashboard. |
| FR9 | System keeps a historical record of scored domains for trend review. |

---

## 6. Non-Functional Requirements

- **Latency:** a domain should have a score visible on the dashboard within 60 seconds of ingestion under normal conditions.
- **Resilience:** if a live data source (WHOIS, hosting lookup) is temporarily unavailable, the system falls back to the most recent cached result rather than failing silently.
- **Privacy:** only publicly available domain and registration data is used. No personal user data is collected or stored.
- **Maintainability:** the system should be deployable by a junior engineer from documentation alone, using containerized services.
- **Explainability:** every score must be accompanied by a human-readable explanation, not just a number.

---

## 7. Success Metrics

| Metric | Target |
|---|---|
| Precision | > 90% |
| Recall | > 85% |
| ROC-AUC | > 0.95 |
| False Positive Rate | < 2% at deployment threshold |
| Dashboard latency | Score visible within 60s of ingestion |
| Client acceptance | Confirmed during UAT |

Note: hitting all four model metrics simultaneously is a stretch goal, not a guarantee. The evaluation report should show the actual trade-off curve and justify the chosen threshold honestly rather than claim a perfect result.

---

## 8. Out of Scope

- Automatically blocking or taking down malicious domains.
- Integration with an existing SIEM platform.
- A mobile application.
- Legal or compliance advisory work.
- Production-grade streaming infrastructure (a scheduled poll is sufficient for the prototype).

---

## 9. Assumptions & Constraints

- 12-week academic timeline with a 2–3 person team working part-time around other commitments.
- Only free/public data sources are used (PhishTank, OpenPhish, Cisco Umbrella, Tranco, crt.sh).
- No budget for paid WHOIS/hosting APIs beyond free tiers, so caching and rate-limit handling matter.
- The semantic-similarity (NLP embedding) layer is treated as an enhancement, not a hard requirement, given the timeline.

---

## 10. Risks

See the risk register in the project plan document for the full list and mitigations. The two risks most likely to affect product scope are the fixed semester timeline and third-party API rate limits.
