# Prompt Record 0011 — Add Liquidity Runway Forecast

## Date

2026-07-11

## Development goal

Create an explainable forward-looking liquidity runway forecast for
provider electronic float and shared physical cash.

## AI tool

ChatGPT

## Exact user prompt

> The support-request workflow is complete. Give me the steps for the
> explainable liquidity runway forecast.

## Guidance summary

The forecast uses completed synthetic transactions from a configurable
lookback window.

For provider float:

- cash-in consumes provider electronic float;
- cash-out replenishes provider electronic float;
- only the selected provider's transactions are analyzed.

For shared physical cash:

- cash-out consumes physical cash;
- cash-in replenishes physical cash;
- transactions from all providers are analyzed.

The forecast calculates:

1. gross consumption;
2. gross replenishment;
3. net consumption;
4. net consumption per hour;
5. balance above the prototype safety threshold;
6. estimated runway to the threshold;
7. estimated threshold-breach time;
8. risk classification;
9. freshness- and sample-adjusted confidence;
10. human-readable explanation factors.

The prototype safety thresholds are inherited from the Agent network
feature:

- provider float: ৳40,000;
- physical cash: ৳40,000.

The endpoint does not claim that a shortage is certain. The estimate
assumes that the recent net-consumption pattern continues.

## Files affected

- `backend/app/schemas/forecast.py`
- `backend/app/services/forecast_service.py`
- `backend/app/routers/forecasts.py`
- `backend/app/main.py`
- `backend/tests/test_forecast_api.py`
- `prompts/0011-add-liquidity-runway-forecast.md`

## Validation

- verify cash-in consumes provider float;
- verify cash-out replenishes provider float;
- verify cash-out consumes physical cash;
- verify physical cash combines all providers;
- verify runway is calculated to the safety threshold;
- verify replenishing resources do not get a false breach time;
- verify delayed data reduces confidence;
- verify missing provider codes return 400;
- verify unknown Agents return 404;
- verify missing history returns 409;
- verify invalid lookback values return 422;
- run all tests;
- generate coverage;
- inspect staged files.

## Safety

The forecast is decision support only.

It does not:

- guarantee a future shortage;
- automatically move money;
- automatically request support;
- reserve another Agent's liquidity;
- execute a provider action;
- classify suspicious activity as confirmed fraud.
