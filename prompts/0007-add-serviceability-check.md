# Prompt Record 0007 — Add Transaction Serviceability Check

## Date

2026-07-11

## Development goal

Create a real-time decision-support endpoint that determines whether an
Agent can serve a requested cash-in or cash-out transaction.

## AI tool

ChatGPT

## Exact user prompt

> The data loader is present. Move to the next step and give me the
> directions for building the serviceability check.

## Guidance summary

The endpoint implements the core business distinction:

1. cash-in requires sufficient electronic float in the specifically
   requested provider;
2. cash-out requires sufficient shared physical cash;
3. balances from different providers cannot be combined;
4. the response calculates the exact shortfall;
5. the response provides responsible recommendations;
6. no transaction, transfer, conversion, or replenishment is performed
   automatically.

The response uses three operational states:

- `SERVICEABLE`;
- `PARTIALLY_SERVICEABLE`;
- `NOT_SERVICEABLE`.

`PARTIALLY_SERVICEABLE` means that some capacity exists but the full
request cannot be served. It does not authorize automatic transaction
splitting.

## Files affected

- `backend/app/schemas/liquidity.py`
- `backend/app/services/liquidity_service.py`
- `backend/app/routers/liquidity.py`
- `backend/app/main.py`
- `backend/tests/test_serviceability_api.py`
- `prompts/0007-add-serviceability-check.md`

## Validation

- verify a Nagad cash-in cannot use bKash balance;
- verify cash-out checks shared physical cash;
- verify exact shortfall calculation;
- verify unknown Agents return 404;
- verify zero and negative amounts return 422;
- test through Swagger UI;
- run all backend and synthetic-data tests;
- generate coverage;
- inspect every staged file.

## Safety

This endpoint provides decision support only.

It does not:

- transfer money;
- convert one provider balance into another;
- contact real providers;
- approve a transaction;
- guarantee supporting liquidity;
- collect customer credentials.
