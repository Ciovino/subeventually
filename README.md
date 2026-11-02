# subeventually

*Sub-20. Sub-15. Sub-10. Eventually.*

A self-hosted speedcubing platform built around a **cubing assistant**. After each solve, the assistant works out the best solve possible with every algorithm, and the best solve possible with *the algorithms you actually know*. It then shows where the time went and which algorithm is worth learning next.

> **Status:** early development (Phase 1, terminal app). So far it has a cube you can play with. Solving it is still on you.

## Planned features

- **Two reference solves per scramble:** full repertoire and your repertoire, with lost time split into execution, planning and knowledge gaps.
- **Learn-next ranking:** which algorithm saves you the most time on average, and which one removes your worst solves.
- **Method plugins:** Beginner, LAU and CFOP first; new methods without touching the core.
- **Algorithm sets as YAML files**, validated automatically.
- **Guided solve review:** a few quick questions (F2L order, OLL case...) instead of a full reconstruction, which remains available as an advanced option.
- **Later:** timer, sessions and statistics in a web app, multi-user self-hosting with Docker, an offline-first Android app, and data-driven improvements to the assistant.

## Repository layout

```
packages/
  core/   subeventually-core: cube model, notation, methods, solver, analysis
  tui/    subeventually: terminal app
docs/     vision, architecture, roadmap, decision records
```

## Try it

You need [`uv`](https://docs.astral.sh/uv/). From a clone of the repository:

```bash
uv sync
uv run subeventually show "R U R' U'"
```

This prints the cube after the moves as an unfolded net, starting from white on top and green in front. There are two styles:

- `letters` (the default): one bold letter per sticker, in its color (W white, Y yellow, G green, B blue, R red, O orange);
- `blocks`: one colored square per sticker, with `--style blocks`.

Both are drawn on their own dark background, so white and yellow stay readable whatever your terminal theme. Here they are in a light and in a dark terminal:

<p>
  <img src="docs/images/show-light.png" width="49%" alt="subeventually show in a light terminal: the net of R U R' U' in the letters style and in the blocks style, each on a dark background">
  <img src="docs/images/show-dark.png" width="49%" alt="subeventually show in a dark terminal: the same two nets of R U R' U'">
</p>

When the output is not a color terminal (piped to a file, or with `NO_COLOR` set), it falls back to plain text with the face letters of the [facelet string](docs/NOTATION.md#facelets).

### Playground

```bash
uv run subeventually playground
```

An interactive cube: type moves in [WCA notation](docs/NOTATION.md) and press Enter, and the net, the [facelet string](docs/NOTATION.md#facelets) and the history update. Each line you enter is one step you can undo. A mistyped line is not applied: the error points at the problem and the line stays there to fix.

<p>
  <img src="docs/images/playground-light.png" width="49%" alt="subeventually playground in a light theme: the net in the letters style, a history of three lines, the status line, the facelet string, and an error pointing at the mistyped U2 R'2">
  <img src="docs/images/playground-dark.png" width="49%" alt="subeventually playground in a dark theme: the same session">
</p>

Commands start with `:`.

| Command | Key | Does |
|---|---|---|
| `:undo`, `:redo` | `ctrl+z`, `ctrl+y` | undo or redo the last line |
| `:inverse` | | apply the inverse of the whole history, back to the start |
| `:reset` | | back to a solved cube, with an empty history |
| `:setup R U R' U'` | | start again from a solved cube after these moves |
| `:state` | | copy the facelet string to the clipboard (if your terminal allows it) |
| `:state UUUUUUUUURRR...` | | start again from a facelet string |
| `:style` | `ctrl+t` | switch between letters and blocks |
| `:help` | `f1` | list the commands and keys |
| `:quit` | `ctrl+q` | quit |

## Documentation

- [Vision](docs/VISION.md): goals, phases, non-goals
- [Architecture](docs/ARCHITECTURE.md): how the assistant works
- [Roadmap](docs/ROADMAP.md): milestones
- [Decision records](docs/adr/): why things are the way they are

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

See [LICENSE](LICENSE).
