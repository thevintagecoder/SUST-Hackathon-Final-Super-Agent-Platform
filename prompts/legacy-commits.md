# Commits Created Before the Prompt-Tracking Requirement

The judging panel introduced the prompt-record and SonarQube requirements
after the following commits had already been created and pushed.

| Commit    | Description                                     |
| --------- | ----------------------------------------------- |
| `f9c48c0` | Initial setup and testing                       |
| `6b62dd8` | Add environment-based application configuration |
| `3734d6d` | Add local PostgreSQL connectivity               |

These commits were created and shared before the new judging-panel
instruction.

They have not been rewritten because rewriting published Git history
could disrupt collaborators and reduce repository traceability.

Starting with the next commit:

- every AI-assisted change will include a prompt record;
- the prompt record and related files will be committed together;
- the commit will be pushed individually;
- GitHub Actions and SonarQube will analyze the pushed commit.
