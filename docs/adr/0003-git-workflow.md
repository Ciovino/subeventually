# 0003. Git workflow: GitHub Flow with squash merges

- Status: accepted
- Date: 2026-10-19

## Context

The project needs a workflow that is light enough for a small team, keeps `main` always working, and stays readable as contributors join.

## Decision

- `main` is protected: changes arrive only through pull requests, and CI must pass.
- One short-lived branch per issue: `feat/...`, `fix/...`, `docs/...`, `chore/...`.
- Pull requests are squash-merged; commit messages follow Conventional Commits.
- Releases are semantic-version tags (`v0.1.0`).

## Consequences

One clean commit per change on `main`, an automatic changelog later on, and freedom to commit work in progress on feature branches.
