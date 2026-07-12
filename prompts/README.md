# AI Prompt Records

This directory stores the AI prompts used during development of the
Super Agent Liquidity & Risk Intelligence Platform.

## Purpose

The judging panel requires AI prompts to be included with every
AI-assisted commit.

The prompt record connects:

1. the development request;
2. the AI guidance used;
3. the source files changed;
4. the developer's review;
5. the tests performed;
6. the related Git commit.

## Commit rule

Every AI-assisted code commit created after July 11, 2026 must include
a prompt record in the same commit as the related code changes.

The prompt record must be staged and committed together with the source
code it describes.

## One-commit-per-push rule

Only one new commit should be pushed at a time.

The workflow is:

```text
Make one small change
→ Create its prompt record
→ Run tests
→ Commit the code and prompt together
→ Push the commit
→ Wait for GitHub Actions and SonarQube
→ Review the result
→ Begin the next change
```

This helps ensure that each new commit receives its own code-quality
analysis.

## File naming convention

Prompt files use the following format:

```text
NNNN-short-description.md
```

Examples:

```text
0001-add-prompt-tracking-and-sonarqube.md
0002-configure-sqlalchemy.md
0003-create-agent-model.md
0004-add-agent-api.md
```

The number must increase for every new AI-assisted commit.

## Required sections

Every prompt record must include:

1. Date
2. Development goal
3. AI tool used
4. Exact user prompt
5. Summary of the guidance received
6. Files affected
7. Human review or modifications
8. Validation performed
9. SonarQube result

## Prompt record template

Copy the following structure when creating a new prompt record:

```markdown
# Prompt Record NNNN — Short Title

## Date

YYYY-MM-DD

## Development goal

Describe the small feature, fix, or configuration change.

## AI tool

ChatGPT

## Exact user prompt

> Paste the exact prompt here.

## Guidance summary

Briefly summarize the guidance or implementation approach received.

## Files affected

- `path/to/file-one.py`
- `path/to/file-two.py`

## Human review and modifications

Describe what was reviewed, corrected, accepted, or changed by the
developer before committing.

## Validation performed

- Tests that were run
- Manual API checks
- Expected and actual results

## SonarQube result

Record the result after the commit has been pushed and analyzed.

Example:

- GitHub Actions: passed
- Quality Gate: passed
- Commit: `abcdef1`
```

## Security rules

Prompt records must never contain:

- passwords;
- API tokens;
- SonarQube tokens;
- private keys;
- OTPs;
- real financial credentials;
- private `.env` values;
- customer personal information;
- sensitive or confidential data.

Secrets must be stored using environment variables or GitHub Actions
secrets and must never be committed to the repository.

## Existing commits

Commits created before the judging panel introduced this requirement are
documented separately in:

```text
prompts/legacy-commits.md
```

Prompt records added after the related code was already pushed are
documented in:

```text
prompts/retroactive-commits.md
```

Published Git history will not be rewritten unless the judging panel
explicitly requires it.
