# Prompt Record 0012 — Add Forecast Ground-Truth Evaluation

## Date

2026-07-11

## Development goal

Add a deterministic synthetic liquidity forecast scenario and measure
forecast error and shortage-warning lead time against known ground truth.

## AI tool

ChatGPT

## Exact user prompt

> Add a deterministic FORECAST-001 synthetic scenario and ground-truth
> evaluation for forecast error and shortage-warning lead time.

## Guidance summary

The FORECAST-001 scenario uses one synthetic Agent and one selected
provider resource.

The scenario contains:

- current Nagad electronic float of ৳100,000;
- a prototype safety threshold of ৳40,000;
- five Nagad cash-in transactions of ৳10,000;
- one Nagad cash-out transaction of ৳5,000;
- six hours of forecast history;
- net consumption of ৳45,000;
- net consumption of ৳7,500 per hour.

The deterministic forecast predicts:

- runway: 8 hours;
- predicted threshold breach: 22:00 UTC;
- risk level: HIGH.

Synthetic ground truth records an actual threshold breach at 22:30 UTC.

The evaluation therefore records:

- absolute forecast error: 0.50 hours;
- shortage-warning lead time: 8.50 hours.

A scenario identifier was added to the forecast request so transactions
from different synthetic scenarios are not mixed during evaluation.

## Files affected

- `backend/app/schemas/forecast.py`
- `backend/app/services/forecast_service.py`
- `backend/app/evaluation/__init__.py`
- `backend/app/evaluation/forecast_evaluator.py`
- `synthetic_data/scenarios.py`
- `synthetic_data/generator.py`
- `synthetic_data/tests/test_generator.py`
- `backend/tests/test_forecast_evaluator.py`
- regenerated synthetic demonstration files
- `prompts/0012-add-forecast-ground-truth-evaluation.md`

## Evaluation definitions

Forecast error is:

```text
absolute(
    predicted threshold-breach time
    - actual synthetic threshold-breach time
)
```
