# Prompt Record 0009 — Add Network Support Search

## Date

2026-07-11

## Development goal

Create an explainable Agent-to-Agent liquidity support discovery
endpoint.

The endpoint identifies nearby Agents that may be able to support an
unserviceable customer request without falling below their own safety
reserve.

## AI tool

ChatGPT

## Exact user prompt

> The Agent-to-Agent synthetic network is complete. Give me the steps
> for building `POST /network/find-support`.

## Guidance summary

The endpoint first performs the existing local transaction
serviceability check.

When the local Agent cannot serve the full request:

1. a cash-in searches for the requested provider's electronic float;
2. a cash-out searches for shared physical cash;
3. the requesting Agent is excluded from candidate results;
4. inactive Agents are excluded;
5. candidate capacity is reduced by a configurable prototype safety
   reserve;
6. candidates are filtered by maximum distance;
7. fresh candidates with enough capacity are recommended;
8. delayed candidates are shown as requiring confirmation;
9. candidates with insufficient capacity are ranked below full-capacity
   candidates;
10. all results require human confirmation.

The current prototype safety reserves are:

- provider electronic float: ৳40,000;
- shared physical cash: ৳40,000.

These are demonstration thresholds rather than official financial-sector
rules.

The endpoint never transfers, converts, reserves, or settles money.

## Files affected

- `backend/app/schemas/network.py`
- `backend/app/services/network_service.py`
- `backend/app/routers/network.py`
- `backend/app/main.py`
- `backend/tests/test_network_support_api.py`
- `prompts/0009-add-network-support-search.md`

## Validation

- verify the local serviceability check is reused;
- verify Nagad cash-in searches only Nagad capacity;
- verify cash-out searches physical-cash capacity;
- verify safety reserves are deducted;
- verify AGENT-SYL-002 is the preferred Nagad candidate;
- verify AGENT-SYL-003 is the preferred physical-cash candidate;
- verify delayed AGENT-SYL-004 requires confirmation;
- verify locally serviceable requests do not search the network;
- verify unknown Agents return 404;
- verify invalid amounts return 422;
- test the endpoint through Swagger UI;
- run all backend and synthetic-data tests;
- generate test coverage;
- inspect staged files before committing.

## Safety

The endpoint provides discovery and decision support only.

It does not:

- automatically transfer money;
- automatically convert provider balances;
- guarantee candidate availability;
- automatically refer a customer;
- create a real provider request;
- access real Agent or customer records.
