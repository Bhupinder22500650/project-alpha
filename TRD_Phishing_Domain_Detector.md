# Technical Requirements Document
## AI-Powered Phishing Domain Detector

**Companion to:** PRD_Phishing_Domain_Detector.md
**Status:** Draft v1

---

## 1. Architecture Overview

Four-layer pipeline, each layer decoupled from the next so a change in one doesn't break the others:

```
[NRD / CT Log Sources]
        |
        v
[1. Data Ingestion Layer]  --schedule: every 10-15 min--
        |
        v
[2. Feature Extraction Layer]  (lexical, WHOIS, hosting)
        |
        v
[3. Machine Learning Layer]  (tree classifier + lexical/embedding similarity + SHAP)
        |
        v
[4. Presentation Layer]  (FastAPI -> React dashboard, alerts out)
```

---

## 2. Technology Stack

| Component | Technology | Why |
|---|---|---|
| Language | Python 3.11+ | Best ecosystem for ML + web backends |
| ML framework | scikit-learn, XGBoost, LightGBM | Standard, strong performers on structured/tabular phishing features |
| Baseline model | Logistic Regression | Cheap sanity-check baseline before comparing tree models |
| Brand-impersonation detection (MVP) | Lexical similarity (Levenshtein distance, homoglyph checks) | Cheap, fast, catches obvious cases like `paypa1.com` without needing a transformer pipeline |
| Brand-impersonation detection (stretch) | `sentence-transformers` (e.g. `all-MiniLM-L6-v2`) | Catches semantic/visual similarity the lexical layer misses, added only if timeline allows |
| Explainability | SHAP | Standard for tree-model feature attribution |
| Backend API | FastAPI + Uvicorn | Async-friendly, fast to build REST endpoints |
| Scheduler | APScheduler | Runs the polling job inside the same process, no extra infrastructure needed |
| Caching | Redis | Caches WHOIS/hosting lookups, directly supports the rate-limit and fallback requirements |
| Retry/backoff | `tenacity` | Handles transient failures from third-party WHOIS/hosting APIs |
| Config management | `pydantic-settings` | Keeps API keys and environment config out of source code |
| Database | PostgreSQL | Stores domains, scores, features, alert history |
| Vector similarity (if embeddings are added) | `pgvector` extension | Keeps embeddings in the same database rather than standing up a separate vector store |
| Frontend | React.js + Chart.js | Dashboard UI and trend visualisation |
| Data processing | Pandas, NumPy, spaCy/NLTK | Cleaning and lexical feature extraction |
| Notifications | SMTP (`smtplib`) or a Slack webhook | Pushes high-risk alerts out instead of relying on someone watching the dashboard |
| Containerization | Docker + docker-compose | One-command environment so the system is actually deployable by someone else |
| Testing | pytest | Unit and integration tests |
| Dev tools | VS Code, Git & GitHub, Postman | Standard team tooling |

**Note on scope:** the sentence-transformer/embedding layer is the single highest-effort, highest-risk piece of this stack relative to its payoff. Build the lexical similarity checks first as the MVP; only add embeddings in Phase 4 if the core pipeline is stable.

---

## 3. Data Sources

| Source | Purpose |
|---|---|
| PhishTank, OpenPhish | Historical labeled phishing domains for training/evaluation |
| Cisco Umbrella, Tranco | Legitimate domain lists for negative examples |
| crt.sh (Certificate Transparency logs) | Live discovery of newly registered/certified domains |
| Public NRD feeds | Additional live domain discovery, covering domains not yet certified |
| WHOIS lookups | Registration metadata (registrar, privacy protection, registration age) |
| Hosting/IP reputation, ASN, SSL data | Hosting metadata features |

---

## 4. Feature Extraction

**Lexical features:** domain length, character entropy, digit ratio, hyphen count, brand keyword matches, Levenshtein distance to a known brand list, homoglyph substitution detection (e.g. `1` for `l`, `0` for `o`).

**WHOIS features:** registrar reputation, registration age, privacy/proxy protection flag, registrant country (where available).

**Hosting features:** IP reputation score, ASN reputation, SSL certificate issuer and age, hosting provider category.

All features are cached in Redis keyed by domain, with a TTL, so repeated lookups within the cache window don't hit external APIs again.

---

## 5. Machine Learning Approach

- **Baseline:** Logistic Regression, for a sanity-check floor.
- **Candidates:** Random Forest, XGBoost, LightGBM — all compared under identical 5-fold cross-validation on an 80:20 train/validation split.
- **Class imbalance:** class weighting and resampling, since legitimate domains vastly outnumber confirmed phishing domains in the training data.
- **Threshold selection:** instead of a default 0.5 cutoff, test thresholds against validation data and pick the one that keeps false positives under 2% while maximizing recall. Document the chosen threshold and the trade-off curve in the evaluation report.
- **Metrics tracked:** precision, recall, F1, ROC-AUC, confusion matrix.
- **Explainability:** SHAP values computed per prediction, surfaced as the top 5 contributing factors per domain.
- **Adversarial check:** test the final model against deliberately disguised domains (e.g. `paypa1.com`) to document where it holds up and where it doesn't.

---

## 6. API Design (indicative)

| Endpoint | Method | Purpose |
|---|---|---|
| `/domains` | GET | List scored domains, filterable by risk level, date, flags |
| `/domains/{id}` | GET | Get full detail + SHAP explanation for one domain |
| `/domains/export` | GET | Export high-risk domains (CSV/JSON) |
| `/alerts/config` | GET/POST | View/update alert threshold and notification target |
| `/health` | GET | Health check for ingestion pipeline and cache status |

---

## 7. Database Schema (indicative)

- `domains` — domain name, first seen, source, status
- `features` — domain_id, lexical/WHOIS/hosting feature values, extracted_at
- `scores` — domain_id, risk_score, model_version, top_factors (JSON), scored_at
- `alerts` — domain_id, threshold_crossed_at, notified (bool), notification_channel
- `whois_cache` / `hosting_cache` — cached lookup results with TTL, backing the Redis cache for durability

---

## 8. Caching & Rate-Limit Strategy

- All WHOIS and hosting lookups go through Redis first; only cache misses hit the external API.
- `tenacity` handles retries with exponential backoff on transient failures.
- If a live source is down, the pipeline falls back to the most recent cached result for that domain so the dashboard keeps producing scores under partial data conditions, per the client requirement.

---

## 9. Deployment

Docker Compose services:
- `api` (FastAPI + APScheduler)
- `frontend` (React build served separately or via the API)
- `db` (PostgreSQL, with `pgvector` extension if embeddings are added)
- `cache` (Redis)

One `docker-compose up` should bring up a working environment for demo/handover, matching the "junior engineer can deploy without extra guidance" requirement.

---

## 10. Testing Strategy

- Unit tests (pytest) for feature extraction functions and scoring logic.
- Integration tests for the ingestion → feature extraction → scoring pipeline end to end.
- Model evaluation report as a separate deliverable, covering all metrics and the threshold decision.
- Manual UAT session with the client against real/sample domains.

---

## 11. Security & Privacy

- Only publicly available data is processed; no personal user data is collected or stored.
- API keys and credentials are managed via `pydantic-settings` / environment variables, never committed to source control.
- Cached data is retained only for the duration of the project and handled per data protection basics — no long-term storage of raw WHOIS data beyond what's needed for scoring.

---

## 12. Known Limitations (to state upfront, not discover late)

- This is a prototype-scale system: scheduled polling, not a production streaming pipeline.
- The embedding-based brand-similarity layer is a stretch goal, not guaranteed in the final build.
- No SIEM integration or automatic blocking — every flagged domain requires human review before action.
