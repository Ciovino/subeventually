# Architecture

This document describes the intended design. Parts not yet implemented are marked *(planned)*. Decisions with lasting consequences are recorded as ADRs in `docs/adr/`.

## Packages

| Package | Distribution | Import | Role |
|---|---|---|---|
| `packages/core` | `subeventually-core` | `subeventually_core` | Cube model, notation, methods, solver, analysis, persistence |
| `packages/tui` | `subeventually` | `subeventually_tui` | Textual front end; `uvx subeventually` launches it |

The core is a library with no UI code, so the Phase 2 server can import it unchanged.

## Cube model

State representation, numbering and orientation conventions: [ADR 0004](adr/0004-cube-state-representation.md).

- Cubie-based state (corner/edge permutation and orientation), compact and hashable.
- Precomputed move tables and pruning tables for search.
- A facelet view only for display and input validation.
- WCA notation parser: face turns, wide moves, slices, rotations, comments (`// ...`).

## Methods and stages

A **Method** is an ordered list of **Stages**. A stage declares:

- **Goal predicate**: which pieces must be solved/oriented/permuted at the end. Goals are **relative**: "solved relative to each other, up to a layer offset" (e.g. up to AUF on U, up to ADF on D). This is required for LAU (D2-offset block building, D/D' moves during keyhole insertion) and for pseudo-slotting.
- **Sub-goals with free ordering** (e.g. two edges and two corners in any order); the solver searches over orders instead of the method hardcoding one.
- **Solver strategy**:
  - *search*: IDA*/BFS toward the goal (cross, Cross-1, intuitive blocks);
  - *lookup*: identify the case, choose an algorithm (OLL, PLL);
  - *hybrid*: search or known algorithms (F2L pairs).
- **Algorithm sets and fallback chains** (e.g. full PLL, then 2-look PLL, then the beginner last layer). The knowledge-limited solve is the same pipeline with the player's known subset; unknown cases fall back with their real time cost.
- **Configuration**: allowed cross colors, rotations, XCross allowed, etc.
- **Guided questions** (see below).

Methods are discovered as plugins via Python entry points *(planned)*.

### Methods, in implementation order

1. **Beginner (layer by layer)**: cross, first-layer corners, second layer, last-layer edge orientation, corner orientation, corner permutation, edge permutation. Simplest method; validates the whole pipeline and forms the bottom of every fallback chain.
2. **LAU**: Cross-1 (3 cross edges, ≤8 moves), D2 offset, front E-slice edges, front D corners via keyhole (with D/D' between corners), D2 join into a 2x2x3 block, last cross edge, last two F2L pairs, then last layer (OLL/PLL or ZBLL).
3. **CFOP** *(planned)*.

## Algorithms

An algorithm entry: set (OLL, PLL, ...), case id, name, one or more **executions** (alternative move sequences with notes), and per-user timing data.

- Algorithm sets are YAML data files shipped as package data (`subeventually_core/data/algsets/`), so contributors can add sets without code.
- **Validation**: applying an execution's inverse to a solved cube must produce the declared case (modulo AUF). Checked in tests/CI.
- **Recognition**: precomputed canonical-state to case lookup per set.
- **Timing**: entered manually or measured with a speed test (N repetitions, averaged). Recognition time is modeled separately from execution time.

## Cost model

"Best" means lowest estimated **time**, not fewest moves:

- lookup stages: the player's execution time plus a recognition constant;
- search stages: move count divided by the player's TPS for that stage;
- penalties for rotations and regrips.

## Analysis

- **Full-repertoire solve** and **your-repertoire solve**.
- **Constraint levels and gap decomposition**: the assistant solves at increasing freedom; the differences attribute lost time to a cause:

  | Level | Gap meaning |
  |---|---|
  | Your repertoire, your choices (same cross color, same Cross-1 edges...) | execution loss |
  | Your repertoire, free choices within your color | planning loss |
  | Full repertoire, same constraints | knowledge loss |
  | Full repertoire, color neutral (optional) | color-neutrality value |

- **Learn-next ranking**: for each unknown algorithm, expected saving per solve = P(case) × (fallback time − time with the algorithm). Also rank by reduction of slow-solve tails, not only the mean.

## Solve input

Three levels:

1. **Quick**: no input; compare total time only.
2. **Guided** (default): method-defined, typed, skippable questions:
   choice (which edge was left out of Cross-1), order (F2L pair order), case picker (which OLL/PLL), count (OLL looks). Options are generated from the scramble where possible. Answers become solver constraints; the assistant finds the best solve consistent with them.
3. **Full reconstruction** (advanced): manual move input.
   - Stage segmentation: a stage ends at the move after which its (relative) goal stays true until the end of the solve ("permanently true", not "first true").
   - Stages may merge (XCross, multislotting) instead of being split artificially.
   - User markers (`// cross`) override automatic boundaries.
   - Each boundary stores whether it was automatic or confirmed.

To keep sessions fluid, solves can be queued for later analysis, and the assistant can prompt only for outliers.

## Persistence

Phase 1 stores every solve and analysis in a local SQLite database *(planned)*.

Store raw data, not only conclusions: scramble, answers or reconstruction, stage times when available, cases met, algorithms used, and a versioned snapshot of the assistant and method config used for each analysis.

Export to CSV/Parquet.

## Performance

The solver sits behind an interface. The pure-Python implementation is the reference; hot paths (move tables, pruning, search) may be ported to Rust via PyO3/maturin later, with prebuilt wheels and tests asserting identical results.

## Phase 2 outlook (not implemented yet)

FastAPI, PostgreSQL, SQLAlchemy and Alembic; analysis as background jobs pushed via WebSocket/SSE; random-state scrambles; original and modified scramble stored per solve. Sync-ready data model: client-generated UUIDs, `created_at`/`updated_at`, soft deletes, idempotent batch upload.
