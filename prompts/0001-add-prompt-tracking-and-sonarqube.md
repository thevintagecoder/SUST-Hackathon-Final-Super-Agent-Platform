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

Follow-up prompt:

> It is already created. What do I do next? I have edited the legacy
> Markdown file as well.

Follow-up prompt:

> Here is the file. What changes do I have to make?
>
> Give me the exact file to replace. Also, this is what I have created
> till now.

The final follow-up included a screenshot of the current VS Code project
state and the current contents of this prompt record.

## Guidance summary

The repository contains a `prompts` directory for development traceability.

Each future AI-assisted commit will include a numbered Markdown prompt
record containing:

- the relevant user prompt;
- the development goal;
- the files affected;
- human review or modifications;
- validation performed;
- the analysis status at commit time.

Existing commits created before the judging-panel instruction are
documented separately without rewriting published Git history.

The project uses GitHub Actions to:

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
history because collaborators may already have pulled those commits.

The SonarQube token was stored as a GitHub Actions repository secret named
`SONAR_TOKEN`. The token value was not placed in any repository file.

The SonarQube project key and organization key were stored in
`sonar-project.properties`. These are project identifiers, not secret
credentials.

No passwords, database credentials, API tokens, private environment
values, or real customer information were included in the prompt records.

## Validation performed

Local validation required before committing:

- inspect all prompt-record files;
- run `git diff --check`;
- run the complete pytest suite;
- generate `coverage.xml`;
- verify that `.env` is ignored by Git;
- verify that `.coverage` is ignored by Git;
- verify that `coverage.xml` is ignored by Git;
- confirm that no placeholder remains in `sonar-project.properties`;
- confirm that no secret token value is stored in repository files;
- review every file staged for the commit.

Post-push validation:

- GitHub Actions workflow: pending at commit time;
- SonarQube analysis: pending at commit time;
- Quality Gate: pending at commit time.

The authoritative post-push results will be retained by GitHub Actions and
SonarQube Cloud and associated with the resulting Git commit.
