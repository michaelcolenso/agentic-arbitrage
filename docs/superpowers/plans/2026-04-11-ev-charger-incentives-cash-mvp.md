# EV Charger Incentives Cash MVP Improvement Plan

## Summary

Turn Agentic Arbitrage Factory from a simulator into a 30-day cash-seeking MVP focused on **EV charger incentive eligibility**, not broad EV rebates.

The first vertical should answer one high-intent user question:

> Can I get money back for installing a Level 2 EV charger at my address before the June 30, 2026 federal credit deadline?

This plan prioritizes:
- Real evidence over mock confidence.
- One deployable EV charger incentives site over many fake sites.
- Build/deploy/metrics truth gates before any success state.
- A proof packet that another operator, investor, or agent can evaluate.

## Key Product Decisions

- **Vertical:** EV charger incentives / home charger rebate eligibility.
- **Primary wedge:** Level 2 home charger incentives by state, utility, and federal 30C eligibility.
- **Primary CTA:** ZIP/email capture for a personalized rebate checklist.
- **Runtime modes:** Add explicit `demo`, `staging`, and `production` modes.
- **Production rule:** Production must never silently use mock Reddit, random validation, fake Cloudflare URLs, or simulated traffic.
- **Stack default:** Use Next.js for the MVP site because the current generated files already point that way. Defer Hono/D1 migration unless a later plan intentionally rewrites the template system.
- **Data budget:** Minimal paid APIs. Use public data and manual keyword/SERP snapshots first.

## Implementation Plan

### 1. Add Runtime Mode Guardrails

Add a `FACTORY_MODE` config option with valid values:

- `demo`: may use fixtures, mock data, fake deploy URLs, and simulated metrics.
- `staging`: must use real data/probes and local build checks; deployment may use a fake adapter only if clearly labeled.
- `production`: must use real providers and fail closed when required providers are missing.

Required behavior:
- `factory.py run --mode production` must fail before creating opportunities if required production providers are unavailable.
- `factory.py status` must display current mode.
- Existing demo behavior should remain available only in `demo`.

Suggested files:
- `config/settings.py`
- `factory.py`
- `agents/red_queen.py`
- `agents/midwife.py`
- `agents/constructor.py`
- `agents/mortician.py`
- `tests/test_runtime_modes.py`

### 2. Add Evidence-Based Lifecycle Records

Add persisted evidence records so each stage can explain why it made a decision.

Minimum evidence types:
- `discovery_evidence`: source, URL, captured text/snippet, timestamp, engagement, theme, confidence.
- `data_probe_evidence`: source URL, status code, content type, sample count, schema hints, error message if failed.
- `keyword_evidence`: keyword, volume, difficulty, CPC if known, source, captured date, confidence.
- `monetization_evidence`: partner/program/source URL, payout estimate, confidence, notes.
- `deployment_evidence`: build status, deployment adapter, deployment URL, health check status, checked timestamp.
- `metrics_evidence`: provider, date range, organic users, pageviews, conversions, revenue if known.

Use SQLite JSON columns if that is the smallest safe change; avoid a full database migration framework unless needed.

Required behavior:
- Opportunity/site status changes must be explainable from stored evidence.
- Failed stages must move to explicit failed/rejected statuses instead of staying in `VALIDATING` or `BUILDING`.

Suggested files:
- `core/models.py`
- `core/storage.py`
- `factory.py`
- `tests/test_evidence_storage.py`
- `tests/test_status_transitions.py`

### 3. Replace Mock Discovery With Real Reddit/Public Evidence

Fix `RedditMonitor`.

Required behavior:
- Remove the broken `praw` production path or add `praw` as a real dependency. Prefer the simpler public JSON `aiohttp` path for this MVP.
- Store source URLs and snippets for every pain point.
- Add rate limiting and user-agent handling.
- Add deduplication using source URL plus normalized text hash.
- Keep mock pain points only for `demo`.

EV charger discovery should prioritize:
- `r/evcharging`
- `r/electricvehicles`
- `r/TeslaLounge`
- `r/ModelY`
- `r/volt`
- `r/AskElectricians`
- `r/homeowners`

Search patterns should include:
- "EV charger rebate"
- "Level 2 charger rebate"
- "charger tax credit"
- "8911"
- "30C"
- "utility rebate"
- "charger install cost"
- "qualifying census tract"

Suggested files:
- `agents/red_queen.py`
- `config/settings.py`
- `tests/test_red_queen_real_mode.py`

### 4. Replace Random Validation With Deterministic Probes

Remove all `random.*` validation behavior outside `demo`.

Data validation must:
- Probe AFDC / DOE incentive-related data sources.
- Record HTTP status, content type, sample availability, and schema hints.
- Fail closed in production if data cannot be accessed or parsed.

Keyword validation must:
- Support manual CSV keyword/SERP snapshots as the first low-cost provider.
- Store source and capture date.
- Use deterministic fallback only in `demo`.

Validation scoring for this MVP:
- Data access and freshness: 30%.
- Keyword/SERP opportunity: 30%.
- Monetization evidence: 25%.
- Buildability/automation: 15%.
- Production pass threshold: 7.0/10.

Suggested files:
- `agents/midwife.py`
- `config/settings.py`
- `tests/test_midwife_deterministic_validation.py`
- `tests/fixtures/ev_charger_keyword_snapshot.csv`

### 5. Generate One Complete EV Charger Incentives Site

Update Constructor to produce a compilable Next.js site for the first vertical.

Required generated routes:
- `/`
- `/ev-charger-rebates`
- `/ev-charger-rebates/[state]`
- `/ev-charger-tax-credit`
- `/level-2-charger-rebate-checklist`
- `/api/health` or an equivalent static health check

Required site features:
- State-level incentive pages.
- Federal 30C explainer with deadline language.
- ZIP/email capture form stub that writes locally or logs to a simple configured sink in staging.
- SEO metadata.
- `robots.txt`.
- `sitemap.xml`.
- JSON-LD for relevant informational pages.
- Internal links between national, state, and checklist pages.

Required build gate:
- Run package install/build during Constructor in staging/production.
- Do not mark the site `DEPLOYED` if `npm run build` fails.
- Store build output in deployment evidence.

Suggested files:
- `agents/constructor.py`
- `config/settings.py`
- `tests/test_constructor_next_site.py`

### 6. Add Real Deployment Adapter and Health Check

Split deployment into adapters.

Minimum adapters:
- `LocalDeploymentAdapter`: used for tests/staging.
- `CloudflareDeploymentAdapter`: used in production when credentials are present.
- `DemoDeploymentAdapter`: only used in demo mode.

Required behavior:
- Production deployment returns a real deployment URL, project ID, and health-check result.
- A site can only become `DEPLOYED` after the deployed URL returns HTTP 200 for the health endpoint.
- Failed deployment sets a failed status and stores error evidence.

Suggested files:
- `agents/constructor.py`
- `config/settings.py`
- `tests/test_deployment_adapter.py`

### 7. Replace Mock Metrics With Manual Import First

Do not simulate traffic in staging/production.

Add manual metrics import:
- CLI: `factory.py metrics import <csv_path>`
- CSV fields: `site_id,date,organic_users,pageviews,conversions,revenue,source`
- Imported metrics should feed `factory.py status` and dashboard output.

Culling behavior:
- If no real metrics exist, mark `metrics_unavailable`; do not cull based on fabricated traffic.
- Culling decisions require real metrics evidence.

Suggested files:
- `factory.py`
- `agents/mortician.py`
- `core/storage.py`
- `dashboard.py`
- `tests/test_metrics_import.py`
- `tests/test_mortician_no_fake_metrics.py`

### 8. Fix Stats and Dashboard Truthfulness

Current aggregate stats can show zero while sites/opportunities exist. Fix stats so dashboard and CLI reflect persisted state.

Required behavior:
- `factory.py status` derives counts from actual opportunities/sites/metrics or updates stats transactionally after every lifecycle change.
- Dashboard shows:
  - mode
  - active vertical
  - opportunities by status
  - sites by status
  - evidence completeness
  - deployment health
  - last real metrics date
  - "ready to fund" / "not ready" flag

"Ready to fund" should require:
- validated EV charger incentives opportunity
- passing local build
- verified live deployment
- at least one metrics source configured or imported
- conversion path present

Suggested files:
- `factory.py`
- `dashboard.py`
- `core/storage.py`
- `tests/test_status_truthfulness.py`

## Test Plan

Run after each implementation phase:

```bash
uv run pytest -q
```

Add targeted checks:

```bash
uv run pytest tests/test_runtime_modes.py -q
uv run pytest tests/test_evidence_storage.py -q
uv run pytest tests/test_midwife_deterministic_validation.py -q
uv run pytest tests/test_constructor_next_site.py -q
uv run pytest tests/test_deployment_adapter.py -q
uv run pytest tests/test_metrics_import.py -q
uv run pytest tests/test_status_truthfulness.py -q
```

Manual acceptance flow:

```bash
FACTORY_MODE=demo uv run python factory.py run --mode demo
FACTORY_MODE=production uv run python factory.py run --mode production
```

Expected:
- Demo completes and clearly labels all fixture/mock behavior.
- Production without required providers fails early and creates no fake deployed site.

Then, with staging config:

```bash
FACTORY_MODE=staging uv run python factory.py run --mode staging
uv run python factory.py status
```

Expected:
- EV charger incentives opportunity includes stored evidence.
- Validation scoring is deterministic.
- Generated site builds successfully.
- Status counts match persisted data.
- No fake deployment URL is reported as production deployment.

## Acceptance Criteria

The factory is meaningfully improved when:

- No mock/random/fake success path can run in production.
- EV charger incentives is the only production vertical in scope.
- Validation decisions have inspectable evidence.
- The generated EV charger incentives site compiles.
- Deployment success requires a real URL health check.
- Metrics and culling no longer use simulated traffic outside demo.
- Dashboard and status output are truthful.
- Another agent can run the plan and know exactly what "done" means.

## Assumptions

- First goal is a 30-day cash MVP, not a generalized platform.
- Initial vertical is EV charger incentives / home charger rebate eligibility.
- Broad "EV rebates" is too vague and should not be the positioning.
- Minimal paid API budget: public data plus manual keyword/SERP snapshots.
- SQLite remains acceptable for this MVP.
- PostgreSQL, distributed workers, and multi-vertical scaling are intentionally deferred.
