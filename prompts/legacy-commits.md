# Commits Created Before the Prompt-Tracking Requirement

The judging panel introduced the prompt-record and SonarQube requirements
after the following commits had already been created and pushed.

| Commit    | Description                                     |
| --------- | ----------------------------------------------- |
| `f9c48c0` | Initial setup and testing                       |
| `6b62dd8` | Add environment-based application configuration |
| `3734d6d` | Add local PostgreSQL connectivity               |

These published commits will not be rewritten because rewriting shared
Git history could reduce traceability and disrupt the repository.

Starting with the next commit:

- every AI-assisted change will include a prompt record;
- the prompt and related code will be committed together;
- only one commit will be pushed at a time;
- the pushed commit will be analyzed using SonarQube.

Historical commits will be rewritten only if the judging panel explicitly
requests it.
