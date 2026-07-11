# Prompt Record 0014 — Add Anomaly Detection API

## Date

2026-07-11

## Development goal

Connect the tested deterministic anomaly detector to stored transaction
data and expose an explainable API endpoint.

## AI tool

ChatGPT

## Exact user prompt

> Here is the output, what is the next step?
>
> 5 passed in 0.02s

## Guidance summary

The anomaly detector was connected to completed transaction records
stored in the database.

The endpoint is:

```text
POST /anomalies/detect
```
