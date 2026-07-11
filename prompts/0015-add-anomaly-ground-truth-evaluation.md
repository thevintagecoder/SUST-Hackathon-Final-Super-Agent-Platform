# Prompt Record 0015 — Add Anomaly Ground-Truth Evaluation

## Date

2026-07-11

## Development goal

Evaluate deterministic anomaly detection against labeled synthetic
scenarios.

## AI tool

ChatGPT

## Exact user prompt

> GitHub and Sonar has passed, now give me the next steps.

## Guidance summary

The anomaly detector is evaluated against two synthetic scenarios:

- `NORMAL-001`, where no anomaly is expected;
- `REPEATED-001`, where an anomaly is expected.

Each prediction is classified as:

- true positive;
- false positive;
- true negative;
- false negative.

The evaluator calculates:

- precision;
- recall;
- false-positive rate.

The evaluation passes only when there are no false positives and no
false negatives in the selected synthetic evaluation set.

The reported values describe controlled synthetic performance only.
They do not establish production accuracy and do not classify unusual
activity as confirmed fraud.

## Files affected

- `backend/app/evaluation/anomaly_evaluator.py`
- `backend/tests/test_anomaly_evaluator.py`
- `prompts/0015-add-anomaly-ground-truth-evaluation.md`

## Validation performed

- `python -m pytest backend/tests/test_anomaly_evaluator.py -v`
- `python -m pytest backend/tests synthetic_data/tests -q`
- terminal execution of the anomaly evaluator

## Post-push validation

- GitHub Actions: pending at commit time
- SonarQube: pending at commit time
- Quality Gate: pending at commit time
