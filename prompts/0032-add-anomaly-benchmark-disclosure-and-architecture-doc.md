# Prompt Record 0032 — Anomaly Benchmark Disclosure and Architecture Doc

## Date

2026-07-12

## Development goal

Meet judge criteria for responsible-AI transparency by surfacing controlled
false-positive benchmark metrics on the main Anomalies demo path (not only
Advanced → Model checks), and add `ARCHITECTURE.md` so reviewers can
understand the repository structure without reading every file. All changes
remain frontend-only and documentation; backend logic was not modified.

## AI tool

Cursor (Composer)

## Exact user prompt

> in my code, was failure, uncertainty and false positivw considerations
> shown?

Follow-up prompt:

> False positives
> ✓ (evaluator)
> ✗ on main path. i need to show it in code to meet judge criteria. do not
> break the backend logic

Follow-up prompt:

> add

Follow-up prompt:

> create architecture.md of my code so judges can understand from the repo

Follow-up prompt:

> push anomaly and whatever latest update i have, with prompt.md

## Guidance summary

The implementation keeps backend evaluation APIs unchanged and composes
existing `GET /dashboards/evaluation` data on the frontend:

- **Anomalies main path:** Added `_render_anomaly_quality_disclosure()` on
  the Anomalies tab showing false positives, false positive rate, precision,
  recall, and an info box stating the prototype never auto-labels fraud
  (NORMAL-001 vs REPEATED-001 benchmark language).
- **Cached fetch:** Added `cached_evaluation_dashboard()` in
  `frontend/components/common.py` (60s TTL) to avoid hammering the API.
- **Live anomaly results:** `_render_anomaly_result()` now surfaces
  `uncertainty`, `confidence`, and `decision` from the anomaly API response.
- **Architecture doc:** Added `ARCHITECTURE.md` covering system purpose,
  high-level diagram, module map, API surface, data flow, and judging notes.
- **README links:** Linked `ARCHITECTURE.md` and `DEMO_GUIDE.md` from the
  top of `README.md`.

## Files affected

- `ARCHITECTURE.md`
- `README.md`
- `frontend/components/common.py`
- `frontend/views/tools.py`
- `prompts/0032-add-anomaly-benchmark-disclosure-and-architecture-doc.md`

## Human review and modifications

The developer reviewed that benchmark metrics appear on the primary Anomalies
navigation path, that disclosure language avoids fraud accusations, and that
`ARCHITECTURE.md` accurately describes frontend/backend boundaries. Backend
source files were not modified.

## Validation performed

- `python -m pytest frontend/tests -q` — 19 passed
- Confirmed `git status --short -- backend` shows no backend source changes
- Manual check: Anomalies tab loads evaluation metrics from
  `GET /dashboards/evaluation`

## SonarQube result

Pending — to be recorded after this commit is pushed and analyzed.

Example:

- GitHub Actions: pending
- Quality Gate: pending
- Commit: `6bed890`
