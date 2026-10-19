# 0002. Monorepo with a uv workspace

- Status: accepted
- Date: 2026-10-19

## Context

The assistant logic must be reused by the terminal app (Phase 1), the server (Phase 2) and possibly other clients. Code, documentation and future server and web parts should evolve together.

## Decision

One repository. Python packages live under `packages/` and are managed as a uv workspace with a single lockfile:

- `packages/core`: distribution `subeventually-core`, import `subeventually_core`. No UI code; never imports the terminal app.
- `packages/tui`: distribution `subeventually`, import `subeventually_tui`, console script `subeventually`.

Each package uses the `src/` layout. Directories for the server and web app are created only when Phase 2 starts.

## Consequences

`uvx subeventually` can run the app, and the core can be published and reused on its own. A single lockfile keeps every development environment and CI on identical dependency versions.
