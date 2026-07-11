# Prompt Record 0003 — Optimize GitHub Actions Runtime

## Date

2026-07-11

## Development goal

Reduce unnecessary GitHub Actions execution time while preserving
automated tests, coverage reporting, and SonarQube analysis for every
pushed commit.

## AI tool

ChatGPT

## Exact user prompt

> I have pushed the current tests. Why does GitHub take so long to work?
> Can this be solved somehow? I am in a 24-hour hackathon and five hours
> have already passed.

## Guidance summary

The workflow runtime may include GitHub-hosted-runner queueing, Python
environment setup, dependency installation, test execution, coverage
generation, and SonarQube analysis.

The workflow was simplified by:

1. keeping pip dependency caching;
2. removing the unnecessary pip-upgrade command;
3. removing the duplicate pull-request trigger;
4. retaining analysis on every push;
5. retaining manual workflow execution support.

Development does not need to stop while GitHub Actions runs. Local work
may continue, but each feature commit should be pushed separately so its
analysis remains traceable.

## Files affected

- `.github/workflows/quality.yml`
- `prompts/0003-optimize-github-actions-runtime.md`

## Human review and modifications

The SonarQube scan was retained because the judging panel requires every
commit to be analyzed.

`cancel-in-progress` was intentionally not enabled because it could
cancel the analysis of an earlier pushed commit.

No secrets or tokens were added to repository files.

## Validation performed

Before committing:

- reviewed the workflow YAML;
- confirmed that the workflow still runs on every push;
- confirmed that pip caching remains enabled;
- confirmed that pytest still generates `coverage.xml`;
- confirmed that the workflow still references the GitHub secret
  `SONAR_TOKEN`;
- ran the complete local pytest suite;
- reviewed the staged changes.

## Post-push validation

- GitHub Actions: pending at commit time;
- SonarQube analysis: pending at commit time;
- Quality Gate: pending at commit time.

GitHub Actions and SonarQube Cloud retain the authoritative results for
the resulting commit.
