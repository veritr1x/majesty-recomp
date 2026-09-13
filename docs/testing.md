# Testing

Run checks appropriate to your change. Every suite's output belongs under
ignored `build/`; requested tests must report failure rather than silently
skip prerequisites. Every command is a wrapper around the kit's
`kit/tools/test.py` with this repository as the game directory.

| Command | What it checks | Needs game files? |
| --- | --- | --- |
| `tools/test.py` | The kit's portable Python suites (setup, config, texture and display-mode tooling) | No |
| `python -m pytest -q tests` | This repository's `game.toml` renders the hooks and globals the kit expects, unidentified ones stay sentinels, and the bundle exclusions keep the pinned executable | No |
| `tools/build.py --stub` | The kit configures and links its hosts against this config without game code | No |
| `tools/test.py --compile-only` | Every native test binary this platform has compiles | No |
| `tools/test.py --native` | Runtime, adapters, offscreen Metal and UI tests; the `game`-labelled suites load the image | Yes for the `game` label |
| `tools/test.py --mods`, `--gameplay`, `--integration` | Game-backed mod, gameplay and integration runs | Yes, plus a translated archive, which this game does not have yet |

Native suites are CTest entries with labels: `nogame` runs everywhere and in
the kit's CI, `game` needs your installation, `gpu` needs a Metal device,
`mods` needs the translated archive. Run one directly with
`.venv/bin/ctest --test-dir build/cmake/macos -L nogame` or `-R dx_tests`.

The game-backed suites are Populous-shaped today (they read the entity table
and camera `game.toml` names, and `--gameplay` wants
`smoke/native-options.script`). They become meaningful for this game once
the sentinels in `game.toml` are real addresses and a smoke script exists;
until then report them as not run, not as passing.

## Bring-up checks

`tools/analyze.py` leaves `analysis/decompiled/MajestyHD - Old.exe/summary.txt`
with the function count Ghidra discovered and how many decompiled.
`tools/build.py --regenerate` writes `build/recomp/translate-report.json`
once the translator gets past its discovery gates; its
unsupported-instruction and unresolved-target counts are the measure of
translator coverage recorded in [analysis.md](analysis.md). Until then the
translator's own error output (`build/translate.log` if you redirect it) is
the record, and a direct run of `kit/tools/recomp/translate.py
--allow-table-gaps <reason>` measures the gates behind the first one
without publishing anything into `build/recomp/gen`.
