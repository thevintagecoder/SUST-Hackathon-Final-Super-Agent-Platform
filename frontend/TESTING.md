# Frontend verification checklist

This checklist focuses on the priority demo path for the Streamlit
frontend. For exact balance counts, reload the intended synthetic
scenario first; dashboard balances come from the live PostgreSQL
snapshot, while scenario selection filters alerts and generated checks.

## Demo story (judge walkthrough)

Follow this story on Overview → Customer service → Alerts → Agent desk:

1. **Rahim** (`AGENT-SYL-001`, Zindabazar) gets a customer wanting
   **৳50,000 cash-out on bKash**.
2. **Customer service** → *Check customer request* → run the check.
3. If short, click **Prompt shortfall alert for operations** (no money
   moves).
4. **Alerts** → open the work item → read *why* and *next step* →
   acknowledge / assign / note / resolve.
5. **Agent desk** / **Operations** / **Provider** show balances and who
   owns the risk.
6. Switch **Alert text language** to **বাংলা** on an open alert — title,
   reason, and next step should change.

Overview has a **What am I looking at?** expander with the same path.

Run both services from the repository root:

```powershell
python -m uvicorn backend.app.main:app --reload
python -m streamlit run frontend/app.py
```

Run automated frontend tests:

```powershell
python -m pytest frontend/tests -q
```

## Manual acceptance cases

### 0. Look, navigation, and context controls

1. Open `http://localhost:8501`.
2. Confirm navigation is shown as two rows of top buttons inside a
   bordered panel, not a sidebar.
3. Confirm every navigation button is visible and clickable with no white
   bar covering them.
4. Switch the scenario selector between `FORECAST-001`, `NORMAL-001`,
   `STALE-001`, and `NETWORK-001`.
5. Switch **Alert text language (title, reason, next step)** between
   English, বাংলা, and Banglish on an opened alert.

Expected: the site stays usable, the header remains visible, and no
top-left controls or navigation buttons are hidden.

### 1. Agent dashboard — forecast-risk scenario

Inputs:

```text
Page: Agent desk
Agent code: AGENT-SYL-001
Scenario: FORECAST-001
```

Expected:

- Agent name: `Synthetic Zindabazar Agent`
- Area: `Sylhet`
- Shared physical cash is visible as a separate card.
- bKash, Nagad, and Rocket provider balances appear as separate float
  cards.
- Provider feeds show freshness and timestamps.
- If the forecast alert has been generated, active alerts show `1`,
  highest risk is `HIGH`, and human review is `Required`.
- Automatic action is reported as none.

### 2. Language switching

Inputs:

```text
Alert language: English
Alert language: বাংলা
Alert language: Banglish
```

Expected:

- Alert titles, messages, and next steps switch language where backend
  translations exist.
- Numbers, balances, and alert statuses remain unchanged.
- Missing translations fall back to English.
- The page does not crash or lose loaded dashboard data.

### 3. Normal scenario with no active risk

Inputs:

```text
Scenario: NORMAL-001
Agent: AGENT-SYL-001
```

Expected:

- Agent and balances still appear if that scenario snapshot is loaded.
- No false warning is shown.
- Highest active severity reads as **Clear** or a human priority label.
- Friendly empty-state copy says **No risk alerts yet** when no alert
  is prompted.

### 4. Stale-data scenario

Inputs:

```text
Scenario: STALE-001
```

Expected:

- At least one balance displays delayed, conflicting, missing, or stale
  feed wording after that scenario is loaded.
- Last-updated timestamp is visible.
- Stale-data alert wording asks for verification and does not claim the
  balance is definitely wrong.

### 5. Provider dashboard — Nagad network view

Inputs:

```text
Page: Provider
Provider: NAGAD_SIM
Scenario: NETWORK-001
```

Expected with a clean controlled `NETWORK-001` load:

```text
Agents with balance: 4
Total electronic balance: ৳320,000.00
Prototype safety threshold: ৳40,000.00
Agents at or below threshold: 2
Fresh balances: 3
Non-fresh balances: 1
```

Also verify:

- Critical or high-risk Agents appear before lower-risk Agents.
- Only the selected provider's balances and alerts appear.
- Resolved alerts are excluded from active-alert totals.

### 6. Operations dashboard overview

Inputs:

```text
Page: Operations
Scenario: All scenarios
Recent alerts: 10
```

Expected:

- Total and active Agent counts appear.
- Active, escalated, and unassigned alert counts appear.
- High/critical risk count appears.
- Human-review workload appears.
- Non-fresh provider-feed count appears.
- Agent risk table is sorted with the highest severity first.
- Resolved alerts do not appear in the active review queue.

### 7. Human-review workflow

Use a newly created `OPEN` alert from **Alerts → Run a risk check**.

Actions:

```text
Acknowledge as frontend-tester
Assign owner liquidity-team
Add note: Agent reported increased demand during a local event.
Escalate as operations-lead
Resolve as operations-manager
```

Expected:

- Status transitions persist after refresh.
- Owner persists after refresh.
- Audit events remain in the alert detail view.
- Resolved alerts disappear from active queues but remain available under
  the `RESOLVED` filter.
- A duplicate invalid transition shows a readable error and no traceback.

### 8. Evaluation dashboard

Open **Model checks**.

Expected controlled values:

```text
Predicted runway: 8.00 hours
Actual breach: 8.50 hours
Absolute forecast error: 0.50 hours
Warning lead time: 8.50 hours
True positive: 1
True negative: 1
False positive: 0
False negative: 0
Precision: 1.0000
Recall: 1.0000
False-positive rate: 0.0000
```

Also confirm the page says these are controlled synthetic results and
does not claim production accuracy.

### 9. Responsible wording

Inspect anomaly and forecast alerts.

Expected acceptable wording:

```text
Unusual activity requires review
Possible liquidity shortage
Forecast indicates increased risk
```

Forbidden wording:

```text
This Agent committed fraud
The shortage will definitely happen
Funds were automatically moved
The Agent was automatically suspended
```

Every operational alert must clearly require human review.

### 1. Connection and navigation

1. Open `http://localhost:8501`.
2. Confirm the header shows **API online** and **Data ready**.
3. Confirm there is no sidebar.
4. Open every top navigation item.

Expected: every view opens without a Python traceback. Navigation remains
at the top.

### 2. Network overview

1. Open **Overview**.
2. Confirm shared cash reserve, bKash + Nagad float, stale balance count,
   active alert count, and unassigned work are visible.
3. Confirm the Agent and provider charts render.
4. Confirm the explanation says cash-in uses provider float and cash-out
   uses shared physical cash.

Expected with `FORECAST-001`: four Agents appear. Nagad has one delayed
feed. If no alert evaluator has run, the page explicitly says no alerts
have been prompted instead of implying there is no risk.

### 3. Agent balances

1. Open **Agent desk**.
2. Select `AGENT-SYL-001`.
3. Confirm shared physical cash is shown separately from bKash, Nagad,
   and Rocket electronic float.
4. Switch to each other Agent.

Expected for `AGENT-SYL-001`: shared cash is `৳65,000`, bKash float is
`৳26,000`, and Nagad float is `৳60,000`. Provider freshness and update
time are visible.

### 4. Serviceable cash-in

1. Open **Customer service → Check customer request**.
2. Select `AGENT-SYL-001`, bKash, cash-in, amount `10000`.
3. Click **Check before serving**.

Expected: request is serviceable and the page explains that bKash
electronic float is used.

### 5. Cash-in shortfall and alert prompt

1. Select `AGENT-SYL-001`, bKash, cash-in, amount `50000`.
2. Run the check.
3. Confirm the shortfall is explained.
4. Click **Prompt shortfall alert**.
5. Open **Alerts**.

Expected: a high/critical shortfall alert is created or deduplicated. The
alert identifies `AGENT-SYL-001` as recipient, starts unassigned, explains
why it was prompted, and includes a recommended next step.

### 6. Shared-cash behavior

1. Check a cash-out request for `AGENT-SYL-001`, any provider, amount
   `70000`.

Expected: the request is not fully serviceable because the Agent has
`৳65,000` shared physical cash. Changing the provider does not create a
different physical cash pool.

### 7. Alert ownership workflow

1. Open an active alert.
2. Acknowledge it as `operations.reviewer`.
3. Assign it to `liquidity.owner`.
4. Add a review note.
5. Resolve it.

Expected: status and owner update after each action; the event history
records the actor and note. Resolved alerts disappear from **All active**
and remain available under the **RESOLVED** filter.

### 8. Nearby support

1. Open **Customer service → Find nearby support**.
2. Use `AGENT-SYL-001`, bKash, cash-in, amount `50000`, radius `10 km`.

Expected: the backend returns a clear support status and either ranked
candidates or a no-support explanation. No transfer is performed.

### 9. Delayed provider data

1. Open **Overview** and inspect Nagad.
2. Open **Agent desk** for `AGENT-SYL-004`.

Expected: Nagad's delayed update is visible and operators are told to
verify stale/delayed data before acting.

### 10. Backend failure

1. Stop FastAPI.
2. Reload Streamlit.

Expected: the page shows API offline and a startup command, not a raw
connection traceback. Restart FastAPI and reload to recover.
