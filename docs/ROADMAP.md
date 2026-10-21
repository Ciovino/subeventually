# Roadmap

Milestones are tracked as GitHub milestones and broken down into issues.

Phase 1 ends with release `v0.1.0`.

## Phase 1: Terminal assistant

- **M0: Scaffolding.** uv workspace, `core` and `tui` packages, ruff, mypy, pytest and Hypothesis, pre-commit, GitHub Actions CI, smoke tests.
- **M1: Cube model, notation, and playground.** Split into:
  - *M1a Cube state*: Cubie representation (ADR 0004), the 18 face turns, inverses, validity check;
  - *M1b Slices, wide moves, and rotations*: M, E, S, wide moves, x/y/z, and the whole-cube orientation (frame);
  - *M1c Notation*: Parser and formatter for WCA notation, including comments and clear error messages;
  - *M1d Facelet view and display*: The 54-sticker view, import and export of the standard facelet string, plain and colored text nets;
  - *M1e Cube playground*: A minimal interactive terminal app. Apply moves and algorithms, see the cube, undo. Pre-release `v0.1.0a1`.
- **M2: Algorithm library.** YAML format for algorithm sets, loading, validation, case recognition for OLL and PLL (modulo AUF).
- **M3: Method interface and Beginner method.** Relative goal predicates, stage pipeline, fallback chains, a solver for each Beginner stage.
- **M4: Cost model and timing.** Per-user algorithm timings, recognition estimates, TPS per stage, speed-test logic.
- **M5: Analysis.** Full-repertoire vs your-repertoire solve, learn-next ranking.
- **M6: LAU method.** Search-based stages (Cross-1, block building with D-layer offsets, keyhole), last two pairs, last layer.
- **M7: Solve input.** Guided questions, gap decomposition, full reconstruction with stage segmentation.
- **M8: Terminal app and persistence.** Full Textual app (building on the *M1e playground*), method and algorithm configuration screens, local SQLite storage, CSV export. Release `v0.1.0`.

## Phase 2: Server and web app

To be broken down when Phase 1 is complete.

## Open questions

- Cost-model constants (recognition time, rotation and regrip penalties).
- How much F2L search depth is affordable in pure Python before a Rust port.
