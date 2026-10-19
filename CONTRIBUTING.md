# Contributing to subeventually

Thanks for your interest! The project is in early development, so expect things to move fast. Issues and discussions are welcome at any stage.

## Getting started

Requirements: `git` and [`uv`](https://docs.astral.sh/uv/). uv installs the right Python version automatically.

```bash
git clone https://github.com/Ciovino/subeventually.git
cd subeventually
uv sync
```

### Common commands

<!-- To be confirmed when the scaffolding milestone (M0) lands. -->

| Task | Command |
|---|---|
| Run tests | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Type-check | `uv run mypy packages` |

## Workflow

- Every change starts from an issue. Comment on it before starting larger work.
- Branch from `main` with a descriptive name: `feat/...`, `fix/...`, `docs/...`, `chore/...`.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/),
  e.g. `feat(core): add wide move parsing`.
- Open a pull request that references the issue (`Closes #12`).
  CI must pass before merging. PRs are squash-merged, so feel free to commit messy intermediate work on your branch.

## Code conventions

- Python with type hints everywhere; mypy runs in strict mode for `packages/core`.
- `subeventually_core` must never import from `subeventually_tui` or any UI library.
- Prefer small pure functions and frozen dataclasses for state.
- Public functions and classes have docstrings.
- Tests use pytest and Hypothesis. Every bug fix starts with a failing test.
- New dependencies need a short justification in the PR.

## Architecture decisions

Significant decisions are recorded in [`docs/adr/`](docs/adr/). Don't change code in a way that contradicts an accepted ADR. If you think one is wrong, open an issue proposing a new ADR that supersedes it.

## Cubing conventions

- WCA notation everywhere (face turns, wide moves, slices, rotations).
- Scrambles are applied in WCA orientation: white on U, green on F. The player's method configuration decides the cross color; the solver applies rotations.
- Times are stored as integer milliseconds.

## Adding methods and algorithm sets

Algorithm sets are YAML files in `packages/core/src/subeventually_core/data/algsets/`.

Methods are Python plugins implementing the stage interface described in [ARCHITECTURE.md](docs/ARCHITECTURE.md).

Step-by-step guides will follow once the interfaces are stable.
