# Prompt Record 0001 — Prompt Tracking and SonarQube

## Date

2026-07-11

## Development goal

Introduce a repository-based process for storing AI prompts and configure
automated testing, coverage reporting, and SonarQube analysis for future
pushed commits.

## AI tool

ChatGPT

## Exact user prompts

> So I have completed what you told us till now, but the judging panel
> came and gave the following instructions:
>
> 1. Push prompt with every commit
> 2. Have to analyze every commit with SonarQube
>
> What does this mean? And what do I do now?

Follow-up prompt:

> This is what I got. Should I go ahead with the prompt record system?

Follow-up prompt:

> I am confused. Give me the entire text that I need to include inside
> README that I can copy directly. Also give me the next steps.

Follow-up prompt:

> I have done everything you have done till now. I have saved the token.
> What do I do next?

## Guidance summary

The repository will contain a `prompts` directory.

Each future AI-assisted commit will include a numbered Markdown prompt
record containing the relevant user prompt, affected files, human review,
validation, and analysis status.

Existing commits created before the judging-panel instruction will be
documented without rewriting published Git history.

The project will use GitHub Actions to:

1. install Python 3.12;
2. install project dependencies;
3. run the automated tests;
4. generate a Python coverage report;
5. send the code analysis to SonarQube Cloud.

Only one new commit should be pushed at a time so that each pushed commit
has a clearly traceable GitHub Actions and SonarQube result.

## Files affected

Prompt tracking:

- `prompts/README.md`
- `prompts/legacy-commits.md`
- `prompts/0001-add-prompt-tracking-and-sonarqube.md`

Testing and SonarQube configuration:

- `.coveragerc`
- `.github/workflows/quality.yml`
- `sonar-project.properties`
- `backend/requirements.txt`
- `.gitignore`

## Human review and modifications

The prompt-tracking and analysis process was reviewed before committing.

Existing published commits were preserved instead of rewriting Git
history.

The SonarQube token was stored as a GitHub Actions repository secret named
`SONAR_TOKEN`. The token value was not placed in any repository file.

No passwords, database credentials, API tokens, private environment
values, or real customer information were included in the prompt records.

## Validation performed

Before committing:

- inspected all prompt-record files;
- ran `git diff --check`;
- ran the complete pytest suite;
- generated `coverage.xml`;
- verified that `.env` was ignored by Git;
- verified that `coverage.xml` was ignored by Git;
- checked that no secret token value was stored in repository files;
- reviewed the files staged for the commit.

Post-push validation:

- GitHub Actions workflow: pending at commit time;
- SonarQube analysis: pending at commit time;
- Quality Gate: pending at commit time.

The authoritative post-push results are retained by GitHub Actions and
SonarQube Cloud and are associated with the resulting Git commit.
