# Demo Guide — Super Agent Liquidity Platform

Read this top to bottom once before the demo. During the demo, just
follow the numbered steps. Every step tells you **who** is in the story,
**what is happening**, and **what the solution is**.

---

## Part 0 — Before the judges arrive (5 minutes)

Open **three PowerShell terminals** in the project folder
(`SUST-Hackathon-Final-Super-Agent-Platform`).

**Terminal 1 — start the backend:**

```powershell
python -m uvicorn backend.app.main:app --reload
```

Wait until you see `Application startup complete`.

**Terminal 2 — load the demo data (do this every time before a demo):**

```powershell
python -m backend.app.data_loading.synthetic_loader --scenario NETWORK-001
python -m backend.app.data_loading.synthetic_loader --scenario REPEATED-001
python -m backend.app.data_loading.synthetic_loader --scenario NETWORK-001
```

Yes, NETWORK-001 twice — the **last** load decides the balances, and the
demo starts with NETWORK-001 balances. The middle load puts the
suspicious transactions in the database for the anomaly step.

**Terminal 3 — start the frontend:**

```powershell
python -m streamlit run frontend/app.py
```

The browser opens at **http://localhost:8501**.

**Check before starting:** the top-left of the app must show
**● API online** and **● Data ready** (both green). If either is red,
see "If something breaks" at the bottom.

---

## Part 1 — The story (say this to judges first)

> "Mobile money agents in Bangladesh — bKash, Nagad shops — constantly
> run out of float and cash. When they can't serve a customer, that
> customer walks away. Our platform watches agent liquidity, predicts
> shortages, flags unusual activity, and — our unique feature — lets an
> agent get help from a **nearby peer agent** instead of turning the
> customer away. Everything is synthetic data. No real money moves.
> Every decision needs a human."

---

## Part 2 — The demo, step by step

### Step 1 — Dashboard (30 seconds)

- **Who:** The operations team at head office.
- **What is happening:** They see 5 agents in Sylhet, provider feed
  health for Nagad and bKash, total shared cash, and a **bar chart of
  shared cash per branch**. One agent — **AGENT-SYL-001 (Zindabazar)** —
  is flagged "Liquidity warning".
- **Solution:** Investigate that agent. Click **Open** next to
  AGENT-SYL-001. It takes you straight to the Liquidity page with the
  problem pre-filled.

Say: *"The dashboard already spotted trouble at the Zindabazar branch.
Let's investigate."*

### Step 2 — Can we serve this customer? (1 minute)

You are now on **Liquidity → Can we serve?**

- **Who:** Rahim, the field agent at Zindabazar. A customer walks in
  wanting to deposit **৳80,000 into Nagad** (a cash-in).
- **What is happening:** Click **Check before serving**. The system
  answers: **✗ CANNOT SERVE — short by ৳60,000**. Rahim only has
  ৳20,000 of Nagad float.
- **Solution:** Two things. First, click **Prompt shortfall alert for
  operations** — this creates an evidence-backed alert for the ops team
  (show that it says "Alert #N created"). Second — don't send the
  customer away — find a nearby agent who can help. Go to the
  **Find support** tab.

Say: *"The system stopped a failed transaction before it happened, told
operations, and now it will find help nearby."*

### Step 3 — Agent-to-agent support (2 minutes) ← YOUR UNIQUE FEATURE

You are on **Liquidity → Find support**.

- **Who:** Still Rahim, plus the network of nearby agents.
- **What is happening:** Click the scenario card, then **Find nearby
  support**. The system searches the Sylhet network and shows:
  - **Ambarkhana (0.87 km)** — ৳120,000 Nagad float, data is fresh →
    **✓ Recommended**
  - **Shibgonj (2.2 km)** — more money (৳150,000) but its feed is
    **3 hours old** → **⚠ Confirm first**
  - A **bar chart** compares each branch's usable capacity against the
    ৳60,000 shortfall.
- **Solution:** Click **Request from Ambarkhana (recommended)**. This
  creates a formal support request — agent to agent — that operations
  tracks. Point at the success message with the request number.

Say: *"This is our unique feature. Notice it did NOT pick the agent
with the most money — Shibgonj's data is stale, so the system refuses
to blindly trust it. It recommends the fresh, confirmed option. And no
money moved automatically — a human approves every step."*

### Step 4 — The support workflow (1 minute)

Scroll down, open **Advanced dashboards → Support only**, go to the
**Detail & actions** tab. Your request from Step 3 is already loaded.

- **Who:** The operations coordinator at head office.
- **What is happening:** The request from Rahim to Ambarkhana is
  **pending**. The coordinator picks **Accept** with the approved
  amount, then **Resolve** when the float transfer is done in real
  life.
- **Solution:** Every action is recorded in a **timeline** — who did
  what, when, with notes. Full audit trail. Show the timeline table.

Say: *"Accept, escalate, resolve — with a full audit trail. Regulators
love this."*

### Step 5 — Cases: the alert we created (1 minute)

Click **Cases** in the top navigation.

- **Who:** The operations team working through their queue.
- **What is happening:** The shortfall alert from Step 2 is here, with
  severity, evidence, and a recommended next step written in plain
  language.
- **Solution:** Acknowledge it, assign an owner, resolve it. Bonus:
  switch **Alert text language** (top of page) to **বাংলা** — the alert
  text changes language. Field agents read Bangla, not English.

### Step 6 — Unusual activity (1 minute)

Click **Anomalies** in the top navigation.

- **Who:** The risk team.
- **What is happening:** Click the **Repeated bKash amounts** scenario
  card, then **Check for unusual activity**. The system finds **5
  nearly-identical cash-ins within an hour** plus a velocity spike —
  and shows a **chart of last hour vs baseline volume**.
- **Solution:** It flags the pattern for **human review**. Read the
  recommended next step out loud.

Say: *"Notice the careful language — it never says 'fraud'. It says
'unusual pattern, please review'. A machine should not accuse a human;
it should help a human decide."*

### Step 7 — Runway forecast (optional, 1 minute)

Only do this if time allows. In **Terminal 2**, run:

```powershell
python -m backend.app.data_loading.synthetic_loader --scenario FORECAST-001
```

Then in the app: **Liquidity → Runway forecast** → click the **Nagad
runway** card → **Estimate runway**.

- **Who:** The ops team planning ahead.
- **What is happening:** Zindabazar is burning **৳7,500 of Nagad float
  per hour**. The **line chart** shows the projected balance crossing
  the safety threshold in **~8 hours**.
- **Solution:** Rebalance float **before** it runs out, not after.

**After this step**, reload the main scenario so the rest of the app
looks right:

```powershell
python -m backend.app.data_loading.synthetic_loader --scenario NETWORK-001
```

---

## Part 3 — One-line answers for judge questions

- **"Is this real money?"** — No. 100% synthetic data. The system never
  moves money; it only recommends, and a human approves everything.
- **"What's unique?"** — Agent-to-agent liquidity support: a shortage
  at one shop is solved by the network, ranked by data freshness and
  safety reserves, not just balance size.
- **"Why didn't it pick the richest agent?"** — Its data was stale.
  Trusting a 3-hour-old balance could send a customer to a dead end.
- **"How does it detect fraud?"** — It doesn't declare fraud. It flags
  statistical patterns (repeated amounts, velocity spikes) for human
  review, with the evidence attached.
- **"What's the stack?"** — FastAPI + PostgreSQL backend, Streamlit
  frontend, talking only over HTTP. 110 backend tests, 15 frontend
  tests, all passing.

---

## If something breaks

| Symptom | Fix |
|---|---|
| "API offline" (red pill) | Terminal 1: `python -m uvicorn backend.app.main:app --reload` |
| "Data unavailable" (red pill) | Start PostgreSQL, then `python -m alembic -c backend/alembic.ini upgrade head` |
| Numbers look wrong / agent not short | Terminal 2: reload `--scenario NETWORK-001` |
| Page looks stale after a change | Press **R** in the browser, or `Ctrl+Shift+R` |
| Port 8501 already in use | Close ALL old terminals, then restart Streamlit once |

Golden rule: **one** Streamlit terminal, **one** backend terminal.
Never start a second copy of either.
