# Prompt Record 0013 — Add Anomaly Detection Core

## Date

2026-07-11

## Development goal

Add a deterministic and explainable anomaly-detection engine for
repeated or near-identical transaction amounts and transaction-velocity
increases.

## AI tool

ChatGPT

## Exact user prompt

> Done with this phase, now build the anomaly detection.

## Guidance summary

The first anomaly-detection increment is implemented as a pure analytics
module before database and API integration.

The detector compares:

- a recent 60-minute transaction window;
- the preceding 60-minute baseline window;
- the largest near-identical amount cluster;
- the recent-to-baseline transaction velocity ratio.

Prototype thresholds are:

- near-identical amount tolerance: BDT 100;
- minimum repeated transaction count: 5;
- velocity multiplier: 2.00.

Supported categories are:

- repeated_amounts;
- velocity_spike;
- repeated_amounts_and_velocity.

The result includes evidence, confidence, uncertainty, responsible
warning language, a safe next step, and whether human review is
required.

The detector never declares fraud and never performs an automatic
financial or enforcement action.

## Files affected

- `backend/app/analytics/__init__.py`
- `backend/app/analytics/anomaly_detector.py`
- `backend/tests/test_anomaly_detector.py`
- `prompts/0013-add-anomaly-detection-core.md`

## Validation performed

- `python -m pytest backend/tests/test_anomaly_detector.py -v`
- `python -m pytest backend/tests synthetic_data/tests -q`

## Post-push validation

- GitHub Actions: pending at commit time
- SonarQube: pending at commit time
- Quality Gate: pending at commit time
