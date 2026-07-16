# Project Plan — A to Z
## AI-Powered Phishing Domain Detector

**Client:** Maryam Var Naseri
**Team:** Mahul Patel, Kartar Singh Johal, Bhupinder Singh
**Duration:** 12 weeks
**Companion documents:** PRD_Phishing_Domain_Detector.md, TRD_Phishing_Domain_Detector.md

---

## 1. Team & Roles

| Name | Area |
|---|---|
| Mahul Patel | To confirm with team — suggest owning data pipeline / ML model development |
| Kartar Singh Johal | To confirm with team — suggest owning backend API / dashboard |
| Bhupinder Singh | Project Personnel, Client Details, Communication Plan, Conflict of Interest Statement, RACI Assessment Matrix, Appendix C requirements |
| Maryam Var Naseri | Client — sign-off on requirements, UAT |

Fill in the two "to confirm" rows once the team has actually split ownership — don't leave it ambiguous past week 1, it causes overlap later.

---

## 2. Phase-by-Phase Plan

### Phase 1 — Research & Setup (Weeks 1–2)
- Finalize and sign off the project plan with the client and supervisor.
- Set up shared repo, project board, and dev environments.
- Pull down historical datasets: PhishTank, OpenPhish, Cisco Umbrella, Tranco.
- Literature review on phishing detection approaches and NRD-based detection.
- Confirm Docker-based dev environment works for all team members.

**Deliverable:** signed-off plan, working repo, datasets acquired.

### Phase 2 — Data & Features (Weeks 3–4)
- Build the ingestion pipeline against crt.sh and public NRD feeds.
- Implement deduplication and Redis caching for WHOIS/hosting lookups.
- Build lexical feature extraction (entropy, digit ratio, keyword match, Levenshtein distance, homoglyph checks).
- Build WHOIS and hosting metadata extraction.
- Label and clean the training dataset.

**Deliverable:** working data pipeline producing a clean, labeled feature table.

### Phase 3 — ML Development (Weeks 5–7)
- Train and cross-validate baseline (Logistic Regression), Random Forest, XGBoost, LightGBM.
- Apply class weighting/resampling for imbalance.
- Select the best-performing model and document the comparison.
- Implement SHAP explainability on top of the chosen model.
- Threshold tuning against validation data.
- Write the first draft of the evaluation report.
- **Stretch (only if ahead of schedule):** add sentence-transformer embedding similarity as a second impersonation-detection signal.

**Deliverable:** trained model, evaluation report draft, chosen operating threshold.

### Phase 4 — System Build (Weeks 8–9)
- Build the FastAPI backend and database schema.
- Wire APScheduler to run the ingestion pipeline on schedule.
- Build the React dashboard: live queue, filters, export.
- Implement alert notification (email/webhook) on threshold breach.
- Integration testing across ingestion → scoring → dashboard.

**Deliverable:** end-to-end working system, deployable via Docker Compose.

### Phase 5 — Testing & Refinement (Weeks 10–11)
- Full end-to-end testing, including failure-mode testing (source down, cache fallback).
- Client UAT session with Maryam.
- Performance tuning (confirm 60-second scoring latency under normal load).
- Finalize documentation: technical report, user guide, deployment runbook.

**Deliverable:** client-accepted system, complete documentation set.

### Phase 6 — Handover (Week 12)
- Final report and presentation to client and academic panel.
- Code handover, including deployment runbook walkthrough.
- Retrospective: what worked, what would be done differently.

**Deliverable:** final submission, client handover complete.

---

## 3. Milestones

| Week | Milestone |
|---|---|
| 2 | Plan signed off, datasets in hand |
| 4 | Ingestion + feature pipeline working |
| 7 | Model selected, threshold set, SHAP working |
| 9 | Full system working end to end |
| 11 | Client UAT passed |
| 12 | Final handover complete |

---

## 4. Risk Register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Limited/unreliable phishing dataset | Medium | Use multiple known datasets (PhishTank, OpenPhish); document data limitations transparently in the final report |
| Model can't adapt to evolving phishing techniques | Medium | Use recent domains in training data; test against adversarial examples; document known limitations |
| Ingestion errors between ML model, API, and dashboard | Medium | Build and test each component independently before integration; use defined API contracts between layers |
| Scope creep from client changes mid-project | Medium | Route changes through a formal change log with supervisor approval before implementation |
| Fixed semester timeline | High | Prioritize core functionality first; keep a backlog of add-ons (like embedding similarity) that only get built if time allows; build buffer time into Phase 3 |
| WHOIS/hosting API rate limits | High | Redis caching, `tenacity` retry/backoff, fallback to cached data if a live source is down |
| False positives flagging legitimate domains | Low | Human review required before any action is taken; classification threshold set conservatively; monitor and report false positive rate throughout testing |
| Embedding/NLP layer takes longer than expected | Medium | Treated as a stretch goal, not core scope — lexical similarity checks cover the MVP requirement on their own |

---

## 5. Communication Plan

- Weekly internal team stand-up to track task progress against the phase plan.
- Regular check-ins with the client at the end of each phase (minimum), plus ad hoc updates if scope or timeline risk changes.
- Any client-requested change goes through a change log and needs supervisor sign-off before work starts on it.

---

## 6. Definition of Done

- Model hits its target metrics or the trade-offs are clearly documented and justified.
- Dashboard is usable by someone outside the team without a walkthrough.
- System deploys via Docker Compose on a clean machine without manual fixes.
- Documentation lets a junior engineer maintain the system without asking the team directly.
- Client has signed off during UAT.
