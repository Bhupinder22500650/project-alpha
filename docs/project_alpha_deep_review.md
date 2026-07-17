# Project Alpha — Deep Technical Review

**Project:** AI-Powered Phishing Domain Detector  
**Review date:** 16 July 2026  
**Review type:** Source review, clean build, linting, unit tests, API integration tests, ML model loading/scoring, database-flow simulation, security scan, and React behaviour test.

## Overall verdict

**The project is not fully working end to end.** It is a useful prototype and some important pieces work, but several critical flows are broken:

- A fresh Docker setup does not create the required database schema or users.
- The Alembic migration is not a valid fresh-database migration.
- Login succeeds at API level but the frontend remains on the login page until refresh.
- The browser extension cannot call the protected analysis endpoint.
- The frontend and backend disagree about analysis-response and alert-review data.
- No alert records are created by the scoring pipeline.
- Stage 2 enrichment is not safely handling RDAP date values or task failures.
- The ZIP includes platform-specific dependencies and a broken lockfile.

This should currently be described as a **partially working prototype**, not a finished phishing-detection product.

---

## What was tested

1. Extracted and reviewed the complete ZIP structure.
2. Read the React frontend, FastAPI backend, Celery tasks, SQLAlchemy models, Alembic migration, Chrome extension, Docker configuration, ML training code, and tests.
3. Ran the original frontend build and lint commands.
4. Removed copied dependencies in the temporary review copy and performed a clean `npm install`.
5. Ran a clean production frontend build and linter.
6. Compiled all Python source files.
7. Ran the backend feature tests.
8. Loaded both saved ML models and generated sample risk scores.
9. Started the FastAPI app against a fresh test database.
10. Tested authentication and protected API requests.
11. Simulated Stage 1 and Stage 2 domain-processing tasks.
12. Tested the frontend login behaviour with React Testing Library/Vitest.
13. Ran Ruff and Bandit static scans.
14. Generated the Alembic SQL to inspect fresh-database migration order.

### Environment limitations

- Docker was not available in the review environment, so I could not execute the actual Docker Compose stack.
- Chromium was installed, but local-site browser automation was blocked by the environment's administrator policy. React behaviour was therefore tested through jsdom/Vitest instead.
- The Python vulnerability audit could not contact PyPI because external DNS resolution was blocked. Frontend `npm audit` completed after clean dependency installation and reported zero known vulnerabilities for that newly resolved dependency set.

---

# Critical issues

## 1. Fresh installation does not create the database or users

**Severity: Critical**

The README tells the user to run:

```bash
docker-compose up --build
```

However, Docker Compose does not run:

- `alembic upgrade head`
- `Base.metadata.create_all(...)`
- the user seed script

The FastAPI startup also does not create tables. In a fresh database test:

- `GET /` returned `200`.
- `GET /health` returned `200` even though Redis was unavailable.
- `POST /api/v1/auth/login` returned `500 Internal Server Error` because the `users` table did not exist.

### Required fix

Add a proper startup/migration process, for example:

1. Run `alembic upgrade head` before the API starts.
2. Create the initial admin through an explicit, non-destructive setup command.
3. Do not depend on a manual script that users may not know exists.

---

## 2. The Alembic migration cannot build a fresh database

**Severity: Critical**

The only migration has `down_revision = None`, so it represents the first migration. However, its generated SQL only creates:

- `users`
- `alerts`
- `domain_enrichments`

It references or alters these tables without creating them:

- `domains`
- `features`
- `scores`

It also creates foreign keys to `domains` before a `domains` table exists.

### Evidence from generated SQL

```text
CREATE TABLE users
CREATE TABLE alerts                 -- references domains
CREATE TABLE domain_enrichments     -- references domains
ALTER TABLE domains ...
ALTER TABLE features ...
ALTER TABLE scores ...
```

### Required fix

Delete and regenerate a true initial migration from an empty database, containing all six tables and all indexes/foreign keys in the correct order.

---

## 3. The supplied frontend dependencies and lockfile are broken

**Severity: Critical for setup/distribution**

The original ZIP contains:

- **12,553** `frontend/node_modules` entries
- **3,817** `backend/.venv` entries
- macOS-specific native packages such as `lightningcss-darwin-arm64`
- eight `.DS_Store` files

The original frontend build failed with missing Linux native bindings for Rolldown and Oxlint. The committed/supplied `package-lock.json` is also out of sync with `package.json`, so `npm ci` fails.

After deleting `node_modules` and running a clean `npm install` in the temporary review copy:

- Production build: **passed**
- Frontend lint: **passed with 3 warnings**
- `npm audit`: **0 vulnerabilities** for the newly resolved set

There is also no `.dockerignore`. The frontend Dockerfile runs `npm install` and then `COPY . .`, which can copy the host's macOS `node_modules` over Linux dependencies inside the image.

### Required fix

- Remove `frontend/node_modules` from the project ZIP/repository.
- Remove `backend/.venv`.
- Add `.dockerignore` files.
- Regenerate and commit a synchronized lockfile.
- Use `npm ci` in the frontend Dockerfile.

Suggested frontend `.dockerignore`:

```text
node_modules
dist
.git
.DS_Store
*.log
```

Suggested backend `.dockerignore`:

```text
.venv
__pycache__
.pytest_cache
.git
.DS_Store
celerybeat-schedule
```

---

## 4. Successful login does not immediately show the dashboard

**Severity: High**

`App.jsx` reads the token directly from `localStorage`:

```jsx
const token = localStorage.getItem('token')
```

After login, `Login.jsx` stores the token and calls `navigate('/')`, but the parent `App` component does not keep token state and does not re-render from the localStorage change.

A React behaviour test confirmed:

- token was saved successfully;
- URL changed to `/`;
- **Live Domain Feed was not rendered**.

The user must refresh the page before seeing the dashboard.

### Required fix

Keep authentication in React state/context. Example approach:

```jsx
const [token, setToken] = useState(() => localStorage.getItem('token'))
```

Pass an `onLogin(token)` callback to `Login`, update state, and use protected routes.

---

## 5. Chrome extension requests always fail authentication

**Severity: High**

The extension posts to:

```text
POST /api/v1/domains/analyze
```

but sends only `Content-Type`; it does not send an `Authorization: Bearer ...` header.

The backend protects this endpoint with `get_current_active_user`. An unauthenticated integration request returned:

```text
401 Not authenticated
```

Therefore the extension cannot submit any visited domain in its current form.

### Required fix

Choose one safe design:

- Add an extension login/token-storage flow and send the bearer token; or
- Create a separate authenticated ingestion endpoint using an extension-specific API key; or
- Use a local native companion/service with restricted access.

Do not simply make the current endpoint public because it triggers DNS/certificate/network activity.

---

## 6. Alert confirmation and dismissal are not functional

**Severity: Critical feature failure**

There are three separate problems.

### A. Alerts are never created

The domain-processing pipeline creates:

- `Domain`
- `Feature`
- `Score`
- `DomainEnrichment`

It never creates an `Alert`. Integration testing confirmed `alerts = 0` after Stage 1.

### B. Frontend hardcodes alert ID 1

Both buttons in `DomainDetail.jsx` call:

```text
/api/v1/alerts/1/review
```

This is unrelated to the displayed domain.

### C. Confirm button sends an invalid enum

The frontend sends:

```json
{"status": "confirmed_phishing"}
```

The backend accepts:

```text
confirmed_suspicious
```

The actual API response was:

```text
422 Unprocessable Entity
```

Using the correct enum still returned `404 Alert not found` because no alert existed.

### Required fix

- Create an alert when a score crosses a configurable threshold.
- Return `alert_id` in list/detail API responses.
- Use the real `alert_id` in the frontend.
- Share status constants/types between backend and frontend.
- Catch button errors and show an inline success/error state instead of an unhandled Axios rejection.

---

## 7. Analyze endpoint response does not match the dashboard

**Severity: High**

Backend response:

```json
{
  "message": "Domain queued for analysis",
  "domain_id": 1
}
```

Dashboard code expects properties such as:

- `res.data.id`
- `res.data.domain_name`
- `res.data.risk_score`
- `res.data.created_at`

It immediately prepends the incomplete response to the domain table. This can render an empty/broken row until polling replaces it.

### Required fix

Either:

- return a complete domain object with a `pending` status; or
- do not insert the response into the scored-domain list, and show a separate queued/pending state.

---

## 8. Stage 2 enrichment is fragile and can leave domains stuck forever

**Severity: High**

The RDAP service returns date strings such as:

```text
2026-07-01T00:00:00Z
```

These strings are assigned directly to SQLAlchemy `DateTime` columns. The integration test failed with:

```text
SQLite DateTime type only accepts Python datetime and date objects as input
```

PostgreSQL may sometimes cast ISO strings, but relying on database-specific implicit casting is unsafe. The values should be parsed into timezone-aware `datetime` objects before persistence.

The task also has no robust exception handling. After the failure, the domain remained:

```text
enriching
```

Other reliability problems:

- no `try/except/finally` around the task;
- no rollback on failure;
- session may remain open on early return or exception;
- no `enrichment_failed` update when a service/database/model operation fails;
- no retry policy or time limit;
- duplicate Feature/Score/Enrichment rows are possible if a task is retried.

### Required fix

- Parse RDAP dates explicitly.
- Wrap tasks in `try/except/finally`.
- Roll back failed transactions.
- Set `ProcessingState.enrichment_failed` on failure.
- Add safe Celery retries and time limits.
- Add unique constraints on `domain_id` for one-to-one tables or use upserts.

---

## 9. Health endpoint reports HTTP 200 for an unhealthy system

**Severity: High for operations**

When Redis was unavailable, `/health` returned HTTP 200 with an error string inside JSON. It does not check:

- PostgreSQL
- Celery worker availability
- model loading status
- migration status

This can cause Docker, monitoring, or deployment systems to mark a broken application as healthy.

### Required fix

- Return `503 Service Unavailable` when a required dependency is unavailable.
- Add database and model checks.
- Create separate liveness and readiness endpoints.

---

## 10. User-supplied domain values are not safely validated

**Severity: High security concern**

The endpoint accepts almost any string and later uses it for:

- DNS resolution
- certificate connection to port 443
- external RDAP lookup

There is no strong validation against:

- IP addresses
- localhost/internal hostnames
- private/reserved network targets
- ports
- invalid labels
- extremely long input
- Unicode/IDN ambiguity

This creates a possible server-side request/network probing risk for authenticated users and becomes worse if the extension endpoint is made public.

### Required fix

- Normalize with a dedicated domain-validation function.
- Reject schemes, credentials, ports, paths, IP addresses, private/reserved names, and malformed labels.
- Convert IDNs consistently with IDNA/punycode.
- Add strict length limits.
- Resolve addresses and reject private, loopback, link-local, multicast, and reserved ranges before connecting.

---

# Other important issues

## Tests are currently broken or outdated

### Feature unit tests

Both tests failed. They expect domain length `6` for `google.com` and `g00gle.com`, while the implementation returns the full hostname length `10`.

The typosquatting test also expects `keyword_match == True` for `g00gle`, but exact substring matching does not recognise it as `google`.

The team must decide whether `length` means:

- registered label length (`google` = 6), or
- complete hostname length (`google.com` = 10).

Then implementation, training data, models, and tests must all use the same definition.

### Live test

`test_live.py` expects a nested `score` object, but `/domains` returns a flat `risk_score`. It also compares a 0–100 score against `0.6`, which is the wrong scale.

There are no meaningful tests for:

- authentication failures and expiry;
- API input validation;
- database migrations;
- Celery failure/retry behaviour;
- alert creation/review;
- frontend login/logout;
- extension authentication;
- end-to-end domain processing.

---

## Seed script is destructive

`backend/scripts/seed_user.py` runs:

```python
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
```

Running it deletes all domains, scores, alerts, and users. A seed-user command should never erase the complete database.

---

## Hardcoded credentials and secret

The project includes:

- hardcoded JWT secret;
- default admin password `admin123`;
- default analyst password `analyst123`;
- default PostgreSQL password `phishing_pass`;
- database and Redis ports exposed to the host.

These are acceptable only for a clearly isolated local demo. They must not be used in a shared, hosted, or assessed production-like system.

Use environment variables, require initial-password setup, and rotate any secret that has been committed/shared.

---

## CORS configuration is too broad

The API uses:

```python
allow_origins=["*"]
allow_credentials=True
```

Restrict allowed origins to the actual frontend and extension origins. Wildcard origin plus credentials is also problematic for browser CORS behaviour.

---

## Ingestion is not truly near-real-time or general-purpose

The scheduled ingestion request is hardcoded to:

```text
https://crt.sh/?q=paypal&output=json
```

This is a search for certificates containing `paypal`, not a general feed of newly registered domains. It can include historical records and does not prove domain registration time.

Additional issues:

- certificate `name_value` may contain multiple newline-separated names;
- only the first arbitrary 50 set entries are used;
- fallback data is synthetic but appears in the same production feed;
- no ingestion cursor/deduplication strategy beyond database domain uniqueness;
- no rate-limit/backoff policy.

The product description should be adjusted unless a real certificate-transparency stream or suitable domain feed is implemented.

---

## ML evaluation is not sufficient for a real security claim

The saved models load and Stage 1 produced sensible-looking sample outputs:

- `google.com` → approximately `2.29`
- `g00gle.com` → approximately `90.35`
- `paypal-update-login.xyz` → `100`

However, the models are trained entirely on generated synthetic data based on a very small list of brands and hand-created patterns. High test scores on this dataset would mainly show that the model learned the data-generation rules.

Before calling it an AI phishing detector, the project needs:

- real labelled phishing-domain data;
- real benign-domain data;
- time-based or campaign-based holdout evaluation;
- precision, recall, F1, false-positive rate, PR-AUC, and threshold analysis;
- reproducible dataset/version documentation;
- model calibration and drift monitoring;
- tests against unseen brands and attack patterns.

---

## DNS enrichment is incomplete

The data model and ML model include MX and NS features, but `dns_service.py` only implements A-record lookup. MX and NS remain fixed at defaults.

This means the enriched model receives misleading feature values for every domain.

---

## Model loading can stop the entire API

`load_models()` does not handle corrupted, missing-dependency, or incompatible pickle errors. Because it runs during application startup, one bad model file can prevent the API from starting.

Log a clear error and decide whether to:

- fail readiness safely; or
- start in an explicit degraded heuristic mode.

Never silently present fallback scores as equivalent to trained-model results.

---

## Authentication and route handling need improvement

- Detail route is not protected in React; it attempts a request with `Bearer null` instead of redirecting to login.
- A 401 from the API does not automatically clear the token and redirect.
- JWT is stored in localStorage, increasing exposure if an XSS vulnerability is introduced.
- No login rate limiting or account lockout exists.
- No user-active/disabled field exists.
- No role checks protect admin-only operations.

---

## Frontend error handling and accessibility

- Dashboard silently becomes an empty table when loading fails.
- Confirm/Dismiss requests have no `try/catch`.
- Login has no submitting/disabled state, allowing repeated requests.
- Form labels are not explicitly linked to input IDs.
- Action link is visually hidden with opacity until hover, which is poor for touch users and discoverability.
- The table does not have a clear horizontal-overflow wrapper for small screens.
- Native `alert()` is used rather than accessible inline feedback/toasts.

---

# Static-analysis results

## Frontend

- Clean production build: **Passed**
- Oxlint: **0 errors, 3 warnings**
  - unused login catch parameter;
  - two unused icon imports.

## Backend

- Python compile: **Passed**
- Ruff: **19 findings**
  - unused imports;
  - duplicate import/redefinition;
  - imports in the middle of `main.py`;
  - formatting/style issues;
  - test-code issues.
- Bandit: **14 low-severity findings**
  - hardcoded JWT secret;
  - swallowed exceptions;
  - use of non-cryptographic randomness in demo/training generation.

No medium or high Bandit finding was reported, but Bandit does not detect the larger architecture and workflow failures described above.

---

# Confirmed working parts

The following parts worked under controlled tests:

- React frontend builds successfully after clean dependency installation.
- FastAPI application imports and starts when dependencies are available.
- Root endpoint works.
- Login endpoint works after tables and a user are created.
- JWT-protected endpoint rejects missing authentication with 401.
- SQLAlchemy models can create a test schema using `Base.metadata.create_all`.
- Lexical feature extraction runs.
- Both saved model files load in a compatible-enough environment.
- Stage 1 scoring and database persistence work in the controlled test.
- `g00gle.com` received a high Stage 1 risk score of `90.35`.
- Domain list/detail API logic works for already-scored records.
- CSV export implementation is structurally simple and likely functional after database setup.

---

# Recommended repair order

## Phase 1 — Make the application start reliably

1. Remove copied `node_modules`, `.venv`, macOS metadata, and Celery schedule files.
2. Add `.dockerignore` files.
3. Regenerate `package-lock.json`; use `npm ci`.
4. Replace the current Alembic history with a valid initial migration.
5. Add an API startup command that runs migrations.
6. Replace the destructive seed script with a safe initial-user command.
7. Add real Docker health checks and startup ordering.

## Phase 2 — Repair core user flows

1. Add React auth state/context and protected routes.
2. Fix analyze response shape and queued/pending UI.
3. Create alerts from scores.
4. Return and use the correct `alert_id`.
5. Align alert status values.
6. Add proper frontend error handling.
7. Add extension authentication.

## Phase 3 — Make background processing reliable

1. Parse RDAP dates.
2. Implement task rollback/failure states/retries/timeouts.
3. Add unique constraints/upserts.
4. Implement real MX and NS lookup.
5. Add caching for all external enrichment calls.
6. Improve health/readiness and structured logging.

## Phase 4 — Improve security

1. Move secrets and credentials to environment variables.
2. Validate domains and block private/reserved network targets.
3. Restrict CORS and exposed service ports.
4. Add login rate limiting and role authorization.
5. Add dependency/SAST scans to CI.

## Phase 5 — Make the ML claim credible

1. Replace synthetic-only training with versioned real datasets.
2. Redesign train/test splitting and evaluation.
3. Choose documented thresholds based on false-positive cost.
4. Test unseen brands and modern phishing patterns.
5. Add model/version/feature compatibility checks.

---

# Final assessment

### Current maturity

**Prototype / academic proof of concept: 45%–55% complete**

### Suitable now for

- demonstrating the intended architecture;
- showing a basic React dashboard;
- demonstrating lexical features and a two-stage scoring concept;
- discussing a capstone implementation plan.

### Not suitable yet for

- claiming the whole system works end to end;
- reliable analyst alert review;
- real browser-extension tracking;
- production deployment;
- monitoring real newly registered domains;
- making trustworthy phishing decisions from the current model.

The strongest next milestone is: **a clean Docker Compose start on a new machine, followed by login → submit domain → Stage 1 → enrichment → alert creation → analyst review, all passing through an automated end-to-end test.**
