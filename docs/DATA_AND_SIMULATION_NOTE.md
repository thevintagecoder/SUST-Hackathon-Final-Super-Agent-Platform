# Data and Simulation Note

## 1. Purpose

This project uses fully synthetic data to demonstrate liquidity monitoring,
risk analytics, anomaly detection, support recommendations, and human-reviewed
alert workflows for simulated mobile financial service Agents.

No real customer, wallet, bank, provider-account, credential, PIN, OTP, or
personal financial data is used.

The generated data is intended only for prototype evaluation and demonstration.

## 2. Simulated Business Model

Each simulated Agent has:

- one shared physical cash reserve;
- one separate electronic-float balance for each provider;
- simulated transactions;
- provider-feed freshness information;
- generated alerts and workflow events.

The providers are represented using clearly synthetic identifiers:

- `BKASH_SIM`
- `NAGAD_SIM`
- `ROCKET_SIM`

Provider balances are not interchangeable.

A healthy total electronic balance can therefore still hide a shortage for one
specific provider.

## 3. Transaction Accounting Rules

The simulation follows these accounting rules.

### Cash-in

During cash-in, the customer gives physical cash to the Agent and receives
electronic value.

Therefore:

- shared physical cash increases;
- the selected provider's electronic float decreases.

### Cash-out

During cash-out, the customer receives physical cash from the Agent and sends
electronic value.

Therefore:

- shared physical cash decreases;
- the selected provider's electronic float increases.

A transaction for one provider never directly changes another provider's
electronic balance.

## 4. Data Generation

Synthetic data is generated through the code in:

```text
synthetic_data/

The generator uses a fixed random seed so that the same configuration produces
reproducible demonstration data.

Default seed:

42

The generated bundle includes records such as:

Agent starting positions;
shared physical cash;
provider-specific electronic balances;
provider-feed freshness;
completed cash-in and cash-out transactions;
scenario labels;
known ground-truth outcomes.

Generated files may include:

transactions.csv
initial_positions.csv
provider_balances.csv
provider_feed_status.csv
ground_truth.json
5. Simulation Scenarios

The demonstration uses controlled scenarios including:

NORMAL-001

Normal transaction activity, healthy liquidity, and no intentionally injected
risk condition.

FORECAST-001

A provider balance is gradually depleted so the platform can estimate its
remaining liquidity runway and predicted safety-threshold breach time.

SHORTAGE-001

A proposed transaction requires more of the relevant resource than the Agent
currently has, allowing the platform to calculate serviceability and shortfall.

REPEATED-001

Repeated or near-identical transaction amounts and increased transaction
velocity are injected to test unusual-activity detection.

STALE-001

A provider feed is delayed or non-fresh so the platform can lower confidence
and request human verification.

NETWORK-001

Multiple Agents are simulated so the system can identify support candidates
with the correct resource and sufficient safe surplus.

6. Ground Truth

Controlled ground-truth labels are stored for injected scenarios.

Ground truth may include:

scenario identifier;
whether an anomaly is expected;
anomaly category;
expected shortage resource;
injection start time;
expected threshold-breach time;
expected freshness state.

This allows the project to calculate measurable evaluation results instead of
only displaying dashboard outputs.

7. Liquidity Simulation

Liquidity runway is estimated using an explainable deterministic calculation.

The platform:

reads the current balance;
subtracts a prototype safety reserve;
measures recent resource consumption and replenishment;
calculates the net hourly depletion rate;
divides the usable balance buffer by the hourly depletion rate.

Conceptually:

usable buffer = current balance - safety threshold

net hourly depletion =
    (gross consumption - gross replenishment) / lookback hours

estimated runway =
    usable buffer / net hourly depletion

The estimate assumes that the recent transaction pattern continues.

It is not presented as a guaranteed future outcome.

8. Unusual-Activity Simulation

The anomaly analysis uses transparent signals:

repeated or near-identical transaction amounts;
transaction count within a recent window;
comparison between recent and baseline transaction velocity.

The system reports unusual activity requiring review.

It does not declare fraud or wrongdoing.

9. Evaluation

Because the scenarios contain known synthetic ground truth, the project can
measure:

true positives;
true negatives;
false positives;
false negatives;
precision;
recall;
false-positive rate;
liquidity forecast error;
shortage-warning lead time.

The displayed results apply only to the controlled synthetic benchmark.

They do not establish production performance.

10. Data Freshness and Confidence

Provider-feed data is labelled using states such as:

fresh;
delayed;
missing;
conflicting.

Forecast confidence considers available evidence such as data freshness and
transaction sample size.

A high numerical balance with stale data may still require human verification.

11. Human Review and Safety

The platform is a decision-support prototype.

It does not:

connect to real provider accounts;
execute or settle transactions;
transfer money;
reserve funds;
automatically suspend Agents;
automatically declare fraud;
perform enforcement actions.

Important alerts require human review and can be:

acknowledged;
assigned to an owner;
annotated with review notes;
escalated;
resolved.

The complete workflow remains traceable through persistent alert events.

12. Limitations
All data is synthetic.
Safety thresholds are configurable prototype values.
Liquidity forecasting assumes recent behaviour continues.
Synthetic scenarios cannot reproduce every real operational condition.
Confidence values are rule-based and are not calibrated probabilities.
Evaluation results come from a small controlled benchmark.
Real deployment would require provider integration, security review,
regulatory review, data-governance controls, monitoring, and larger-scale
validation.
13. Reproducing the Simulation

From the repository root:

python -m synthetic_data.generator

Run the synthetic-data tests with:

python -m pytest synthetic_data/tests -v

The same seed should generate equivalent deterministic output.


---

```
