# Responsible Design Boundaries

## 1. Purpose

The Super Agent Liquidity & Risk Intelligence Platform is a
decision-support and operational-coordination prototype.

It helps simulated mobile-financial-service Agents and operations teams:

- monitor shared physical cash;
- monitor provider-specific electronic float;
- estimate liquidity runway;
- identify unusual transaction patterns;
- review data freshness and confidence;
- route alerts to a human owner;
- acknowledge, investigate, escalate, and resolve alerts.

The platform supports human decision-making. It does not replace human
judgement or execute financial actions.

---

## 2. Prototype and Synthetic-Data Boundary

This project uses synthetic demonstration data only.

All identifiers are clearly synthetic, including:

- Agents;
- providers;
- customers;
- transactions;
- alerts;
- scenarios;
- workflow actors.

Examples include:

```text
AGENT-SYL-001
BKASH_SIM
NAGAD_SIM
ROCKET_SIM
CUSTOMER-0001
TXN-000001
FORECAST-001

The platform does not use real customer records, real wallet balances, real
provider accounts, or real financial credentials.

A visible Synthetic demonstration data notice is shown in the user
interface.

3. No Real Financial Integration

The platform must never:

connect to a real wallet;
connect to a bank account;
connect to a real provider account;
execute a transaction;
transfer money;
convert money;
reserve funds;
recover or reverse money;
settle a payment;
modify a real financial balance.

Transaction input is used only for simulation, serviceability analysis,
forecasting, anomaly analysis, and alert demonstration.

The platform may recommend that a human prepares additional cash or float, but
it does not perform that action automatically.

4. Credential and Privacy Boundary

The platform must never request or store:

PINs;
OTPs;
passwords;
private keys;
production API secrets;
real provider credentials;
real customer personal information;
real account numbers.

Local environment values, database passwords, and API secrets must remain in
ignored environment files and must not be committed to GitHub.

5. Human-in-the-Loop Decision Making

Important alerts require human review.

An alert may move through the following workflow:

OPEN
→ ACKNOWLEDGED
→ ASSIGNED
→ ESCALATED
→ RESOLVED

A human user may:

acknowledge the alert;
assign it to an owner;
add investigation notes;
escalate the case;
resolve the case after review.

The system records the actor, timestamp, note, status change, and ownership
change.

The platform does not automatically:

resolve a case;
escalate a case;
punish an Agent;
block an Agent;
suspend an Agent;
determine fraud;
take enforcement action.

Where supported by the API response, the platform explicitly returns:

human_review_required = true
automatic_action_taken = false
6. Responsible Language

The platform uses careful language that describes evidence without making
unsupported accusations.

Approved language
unusual activity;
anomaly;
requires review;
possible explanation;
liquidity pressure;
estimated runway;
low confidence;
stale data;
human review required;
recent patterns indicate;
may reach the threshold;
if the recent pattern continues.
Prohibited language
confirmed fraud;
fraudulent Agent;
criminal activity detected;
proof of wrongdoing;
certain shortage;
guaranteed prediction;
automatic final decision;
complete real-time truth.

An anomaly signal means that a pattern is unusual relative to the selected
rules and evidence. It does not prove fraud or wrongdoing.

7. Explainability Boundary

The initial analytics use transparent, deterministic calculations.

Liquidity forecasts show evidence such as:

current balance;
safety threshold;
lookback period;
transaction sample size;
gross consumption;
gross replenishment;
hourly net depletion;
estimated runway;
freshness;
confidence.

Anomaly alerts show evidence such as:

repeated or near-identical amounts;
repeat count;
recent transaction count;
baseline transaction count;
transaction-velocity ratio;
analysis window;
possible legitimate explanation.

The platform avoids unexplained or opaque risk scores.

Every important result should answer:

What was detected?
What data was used?
Why was it flagged?
How reliable is the evidence?
What safe human action is recommended?
8. Forecast Uncertainty

Liquidity runway is an estimate, not a guarantee.

The forecast assumes that the recent net-consumption pattern continues.

Actual demand may change because of:

time of day;
local events;
customer behaviour;
provider-feed delays;
cash replenishment;
operational interventions;
missing or conflicting records.

Forecast messages therefore use language such as:

The resource may reach the prototype safety threshold within the configured
warning window if the recent net-consumption pattern continues.

The system must not claim that a shortage will certainly occur.

9. Data Freshness and Confidence

Critical metrics display:

last-updated time;
freshness state;
confidence;
evidence window where relevant.

Supported freshness states may include:

fresh
delayed
missing
conflicting

A large balance does not automatically mean the situation is safe when the
balance data is stale or conflicting.

When data is unreliable, the platform should:

reduce confidence;
display a warning;
require human verification;
suppress overly strong recommendations where appropriate.

Confidence describes confidence in the available analytical evidence. It is
not a probability that an Agent committed fraud or wrongdoing.

10. Provider Separation

Each Agent has:

one shared physical cash reserve;
one separate electronic-float balance for every provider.

Provider balances are not interchangeable.

For example:

BKASH_SIM float
NAGAD_SIM float
ROCKET_SIM float

A high total electronic balance can still hide a shortage for one specific
provider.

The accounting rules are:

Transaction	Shared physical cash	Selected provider float
Cash-in	Increases	Decreases
Cash-out	Decreases	Increases

A transaction for one provider must not directly alter another provider's
electronic balance.

This boundary prevents misleading aggregation and incorrect support
recommendations.

11. Safe Support Recommendations

When an Agent cannot service a proposed transaction, the platform may identify
potential support candidates.

Support recommendations must:

match the exact required resource;
preserve the supporting Agent's safety reserve;
consider data freshness;
show supporting evidence;
require human coordination.

For a cash-in shortage, the required resource is provider-specific electronic
float.

For a cash-out shortage, the required resource is shared physical cash.

The platform recommends coordination only. It does not transfer, reserve, or
settle funds.

12. Alert Routing and Auditability

Alerts are persistent records rather than temporary frontend notifications.

The current alert stores information such as:

alert type;
severity;
status;
Agent;
provider where relevant;
evidence;
confidence;
freshness;
owner;
human-review requirement.

Workflow actions are stored as separate timeline events.

Example events include:

CREATED
ACKNOWLEDGED
ASSIGNED
NOTE_ADDED
ESCALATED
RESOLVED

This append-only timeline preserves:

who performed the action;
when it happened;
what note was added;
the previous status;
the new status;
ownership changes.

Resolution removes an alert from active-risk counts, but its audit history
remains available.

13. Frontend and Backend Boundary

The final demonstration uses:

Streamlit
→ HTTP request
→ FastAPI
→ backend services
→ PostgreSQL

Streamlit must not query PostgreSQL directly.

The backend remains responsible for:

validation;
analytics;
workflow rules;
status transitions;
persistence;
response contracts.

The frontend is responsible for:

collecting inputs;
calling FastAPI;
displaying results;
showing errors clearly;
presenting evidence and responsible warnings.

The frontend must not silently fall back to mock data when API mode fails.

14. Safe Failure Behaviour

When data or infrastructure is unavailable, the platform should fail clearly
and safely.

Examples include:

backend unavailable;
database unavailable;
provider balance missing;
stale provider feed;
conflicting balance;
unknown Agent;
unknown provider;
insufficient transaction history;
invalid workflow transition.

The platform should:

display a readable error;
avoid showing fabricated results;
avoid silently using stale or mock information;
preserve existing records;
require human review where necessary.
15. Evaluation Boundaries

Evaluation results are produced from controlled synthetic scenarios with known
ground truth.

Metrics may include:

true positives;
true negatives;
false positives;
false negatives;
precision;
recall;
false-positive rate;
forecast error;
warning lead time.

Results apply only to the small synthetic benchmark used in the demonstration.

The project must not claim:

production accuracy;
universal generalisation;
regulatory approval;
real provider validation;
financial certification;
production readiness.

A suitable statement is:

The prototype achieved the displayed results on a small controlled synthetic
benchmark. Further testing with representative, governed data would be
required before any real-world use.

16. Safe Recommended Actions

Recommended actions are limited to non-destructive human steps such as:

verify provider-feed freshness;
review the supporting evidence;
contact the assigned operations owner;
prepare additional cash or provider float;
coordinate with a nearby eligible Agent;
contact the relevant provider team;
continue monitoring;
escalate for additional review;
record an investigation note.

The interface must not include an automatic:

money-transfer button;
wallet-block button;
Agent-suspension button;
fraud-confirmation button;
punishment or enforcement control.
17. Known Limitations
All data is synthetic.
Safety thresholds are prototype configuration values.
Forecasts assume recent activity continues.
Rule-based anomaly detection cannot represent every real behaviour.
Confidence is rule-based and not a calibrated probability.
Data freshness may vary by resource.
Synthetic ground truth is simpler than real operational conditions.
Support recommendations are not financial-transfer instructions.
No real provider systems have been integrated.
Security, regulatory, privacy, and operational reviews would be required
before real deployment.
18. Responsible-Demo Checklist

```
