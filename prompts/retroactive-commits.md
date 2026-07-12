# Retroactive Prompt Records

Some AI-assisted commits were pushed before their matching prompt files
were included in the same commit. Published Git history was not rewritten.
Instead, prompt records were added in later documentation commits.

| Prompt file | Code commit | Description |
| ----------- | ----------- | ----------- |
| `0030-polish-demo-frontend-charts-and-agent-flow.md` | `850b9bd` | Demo polish, charts, HTML fixes, DEMO_GUIDE, agent-to-agent flow (prompt added in `167080a`) |
| `0031-refocus-streamlit-field-agent-branding.md` | `1102d50` | Field-agent branding, remove inline demo walkthrough (prompt added in `167080a`) |

Commits created before the judging panel introduced prompt tracking remain
documented in [`legacy-commits.md`](legacy-commits.md).
