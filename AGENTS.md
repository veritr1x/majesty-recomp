# Working on Majesty Recomp

Read README.md, CONTRIBUTING.md and docs/analysis.md before a broad change.
This repository holds only what is Majesty Gold HD's: config, curated
symbols, game headers, docs and, once they exist, mods and smoke scripts.
The runtime, translator, hosts and tools are the kit in `kit/` (a git
submodule of recomp-kit); edit those in the kit's own repository and bump the
submodule here. Game files and translations are private local inputs under
ignored `original/`, `analysis/` and `build/`.

- The port is at the translation stage. docs/analysis.md records what the
  executable needs, what the kit lacks and how far each run got; keep it
  current rather than claiming progress in README.md.
- The pinned executable is `MajestyHD - Old.exe` (DirectDraw), not the
  launcher's `MajestyHD.exe` (Direct3D 9). Do not swap them, and do not
  bypass the hash: a second executable is a second `game.toml`.
- Keep changes focused; preserve unrelated local work and player profiles.
- Never replace 32-bit guest addresses with host pointers. Addresses belong
  in `game.toml` `[hooks]` and `globals.toml`, never in kit code. A sentinel
  address (see game.toml) is replaced only by an address verified in the
  listings; `tests/test_game_config.py` keeps the unverified ones in the
  sentinel range.
- Edit translation rules in the kit, not `build/recomp/gen/`. Regenerate with
  `tools/build.py --regenerate` after changing the translator.
- Native code builds only through `tools/build.py` and `tools/test.py`, never
  by invoking compilers directly. Format kit sources with
  `.venv/bin/python kit/tools/format.py --write`.
- Run relevant suites from docs/testing.md and report exactly which checks
  ran; a configure or a listing export does not establish that the game runs.
- Do not commit game assets, generated code, binaries, credentials, personal
  saves or run logs.
- Keep setup/build instructions reproducible from a clean checkout. Update
  the changelog for user-visible behaviour.
