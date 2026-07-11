# Prompt Record 0029 — Shortfall Rescue CTAs and Provider Portfolio Insights

## Date

2026-07-12

## Development goal

Improve the demo story for judges by connecting shortfall alerts to the
peer-support rescue workflow, surfacing cross-provider comparative insight
on Ops Center, flagging bottleneck providers on the Agent desk, and
clarifying in the demo guide that alerts notify ops while Find support
rescues customers. All changes remain frontend-only; no backend
modifications.

## AI tool

Cursor (Composer)

## Exact user prompt

> Implement the following to-dos from the plan (the plan is attached for
> your reference). Do NOT edit the plan file itself.
>
> You have been assigned the following 4 to-do(s) with IDs: alert-copy-cta,
> provider-portfolio, agent-bottleneck-insight, demo-guide-reframe
>
> 1. [alert-copy-cta] Replace passive ownership copy for
> SERVICEABILITY_SHORTFALL alerts; add Find peer support deep-link in
> Cases/alert detail
> 2. [provider-portfolio] Surface management.provider_risks on Ops Center
> as comparative Provider Portfolio panel (include Rocket)
> 3. [agent-bottleneck-insight] Add derived bottleneck provider callout on
> Agent desk using existing dashboard APIs
> 4. [demo-guide-reframe] Update DEMO_GUIDE to clarify alert = ops
> notification, rescue = Find support workflow
>
> These to-dos have already been created. Do not create them again. Mark
> them as in_progress as you work, starting with the first one. Don't stop
> until you have completed all the assigned to-dos.

Follow-up prompt:

> kill earlier Streamlit running and refresh and rerun

Follow-up prompt:

> i have to push in main and do ci cd and also provide the prompt under
> prompt folder in the format as the rest of the prompts so judges can see
> what ai prompts were used. we dont want merge conflict at all. just push
> this entirely with prompt with correct name and format inside.

## Guidance summary

The implementation keeps backend APIs unchanged and composes existing
management, provider, and agent dashboard data on the frontend:

- **Shortfall alert copy:** Unassigned `SERVICEABILITY_SHORTFALL` alerts
  show action-oriented rescue guidance instead of passive queue ownership
  text. Alert detail adds a **Find peer support** button that deep-links to
  Liquidity → Find support with agent, provider, amount, and transaction
  type pre-filled from alert evidence.
- **Liquidity navigation:** Sub-tabs use session state so deep-links open
  the Find support section directly.
- **Provider Portfolio (Ops Center):** Renders `management.provider_risks`
  with float, HIGH-alert, and feed-trust charts plus a synthesized insight
  sentence. Provider Health now includes Rocket alongside Nagad and bKash.
- **Agent desk bottleneck:** Compares each provider float to network
  averages and safety thresholds, warning when one provider is the binding
  constraint.
- **Demo guide:** Reframes Steps 2 and 5 so alerts notify ops and Find
  support rescues the customer; adds a judge Q&A on float not changing on
  resolve.
- **Navigation polish:** Agent desk becomes the default bottom-nav entry;
  network overview remains reachable from Agent desk and role-filter views.

## Files affected

- `DEMO_GUIDE.md`
- `frontend/app.py`
- `frontend/components/common.py`
- `frontend/components/styles.py`
- `frontend/views/agent_dashboard.py`
- `frontend/views/alerts.py`
- `frontend/views/overview.py`
- `frontend/views/tools.py`
- `prompts/0029-add-shortfall-rescue-and-provider-portfolio-insights.md`

## Human review and modifications

The developer reviewed alert card copy, the Find peer support deep-link
flow, Provider Portfolio charts on Ops Center, Agent desk bottleneck
callouts, and DEMO_GUIDE narrative for the judge demo. Backend code was
not modified. Navigation defaults were adjusted so field agents land on
Agent desk first while Liquidity and Cases remain one tap away.

## Validation performed

- `python -m pytest frontend/tests -q` — 15 passed
- `python -m pytest backend/tests -q` — 110 passed
- `python -m pytest frontend/tests backend/tests -q` — 125 passed
- Restarted Streamlit on http://localhost:8501 after stopping the prior
  instance on port 8501
- Confirmed `git status --short -- backend` shows no backend source
  changes

## SonarQube result

Pending — to be recorded after this commit is pushed and analyzed.

Example:

- GitHub Actions: pending
- Quality Gate: pending
- Commit: pending
