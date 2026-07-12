# Prompt Record 0030 — Polish Demo Frontend with Charts and Agent-to-Agent Flow

## Date

2026-07-12

## Development goal

Fix visible frontend bugs (including raw HTML rendering on the network
overview), verify end-to-end connectivity between Streamlit, FastAPI, and
PostgreSQL, and polish the judge demo path with charts, a one-click
agent-to-agent support workflow, and a step-by-step `DEMO_GUIDE.md`.
All changes remain frontend-only; backend logic was not modified.

**Retroactive record:** code landed in commit `850b9bd`; this prompt file
was added later to satisfy judging requirements without rewriting Git
history.

## AI tool

Cursor (Composer)

## Exact user prompt

> identify bugs. example like in picture. fix them. make sure frontend
> backend db are all connected. i just want a working thing i can show.
> and none of it malfunctions. make sure backend logic wasnt changed due
> to frontend. and write me a guide like i am child for the demo. in demo
> i gotta mention who is using whats happening whats the next solution.
> test the system like u are a judge at a hackathon. since its a finance
> helping app, use charts and graph where its easy to. so the system looks
> helpful for user. the agent to agent support is my unique feature. so fix
> accordingly.

Follow-up prompt:

> save this progress in git in frontend branch commit or push idc

## Guidance summary

The implementation keeps backend APIs unchanged and focuses on demo-ready
frontend polish:

- **Overview HTML fix:** Network overview cards render readable provider and
  agent labels instead of leaking raw HTML markup.
- **Charts:** Added liquidity and network visualizations on Agent desk,
  Ops Center overview, and Liquidity → Find support (capacity vs
  shortfall comparison).
- **Agent-to-agent support:** Find support flow improved with clearer
  recommended vs confirm-first ranking and a one-click request action for
  the recommended peer agent.
- **DEMO_GUIDE.md:** Added a judge walkthrough with who / what / solution
  steps covering dashboard, serviceability shortfall, peer support,
  cases, anomalies, and optional runway forecast.
- **Connectivity:** Confirmed Streamlit calls FastAPI only through
  `BackendClient`; alert and liquidity endpoints exercised manually during
  demo testing.

## Files affected

- `DEMO_GUIDE.md`
- `frontend/views/agent_dashboard.py`
- `frontend/views/overview.py`
- `frontend/views/tools.py`
- `prompts/0030-polish-demo-frontend-charts-and-agent-flow.md`

## Human review and modifications

The developer reviewed overview rendering, chart readability for the
finance demo, the agent-to-agent support one-click flow, and the
plain-language demo guide narrative. Backend source files were not
modified. Progress was saved on the `frontend` branch before later
fast-forward merge to `main`.

## Validation performed

- Manual end-to-end demo walkthrough following `DEMO_GUIDE.md`
- Verified API online / data ready pills on Streamlit startup
- Serviceability shortfall → Find support → support request workflow
- Confirmed `git status --short -- backend` shows no backend source
  changes
- Frontend tests run during adjacent frontend commits on the same branch

## SonarQube result

Not recorded at push time — retroactive prompt added after the code
commit.

Example:

- GitHub Actions: not recorded for this retroactive documentation commit
- Quality Gate: not recorded for this retroactive documentation commit
- Code commit: `850b9bd`
- Prompt commit: pending
