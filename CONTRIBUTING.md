# Contributing

This repository holds Majesty Gold HD's configuration, tests and docs on
top of [recomp-kit](https://github.com/veritr1x/recomp-kit), the submodule
at `kit/`. Runtime, translator, host and tooling changes go to the kit; open
an issue there before a large architecture change. Here, the useful work is
the bring-up itself: identifying the hooks and globals that `game.toml`
still marks as sentinels, curating symbols in `globals.toml`, and keeping
[docs/analysis.md](docs/analysis.md) true.

## Prerequisites

- Python 3.9 or later; create `.venv` and install `kit/requirements-dev.txt`.
- Native builds on macOS: Apple Silicon, Xcode Command Line Tools and Git.
  CMake and Ninja come from the requirements file. iPad builds need Xcode
  with the iOS SDK and a developer team.
- Listings: [Ghidra 12.1.3](https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_12.1.3_build)
  and a Java runtime compatible with it (tested with OpenJDK 26.0.1; set
  `JAVA_HOME` to the JDK directory or pass `--java-home`).
- Your own copy of Majesty Gold HD from GOG, either installed or as the
  offline installer plus [innoextract](https://constexpr.org/innoextract/)
  (`brew install innoextract`).

The executable must be `MajestyHD - Old.exe` with SHA-256:

```text
654365fd1bdefa6d7f2349d162869f255388fadcb1bb8db9f7db2f3468dd5542
```

That is the DirectDraw build (Majesty HD 1.5.1.2) the installer ships
beside the Direct3D 9 `MajestyHD.exe`; see the README for why it is the one
pinned. The loader refuses other binaries because translated addresses and
data layouts are tied to this image. Do not bypass the hash to add support
for another version; a second version is a second `game.toml`.

## Prepare your game installation

The game directory must contain `MajestyHD - Old.exe` and its `Data`,
`DataMX`, `Quests`, `QuestsMX` and `Music` directories. Either extract the
GOG installer straight into `original/gog`, which is where `game.toml`
expects the game:

```sh
innoextract --extract --output-dir original/gog "/path/to/setup_majesty_gold_hd_1.5.2.28_(24283).exe"
.venv/bin/python tools/setup.py --install original/gog --link-only
```

or link an installed copy (paths containing spaces are supported when
quoted):

```sh
.venv/bin/python tools/setup.py --install "/path/to/GOG Games/Majesty Gold HD" --link-only
```

Setup verifies the executable and links the installation at ignored
`original/gog/` (a copy or extraction placed there directly is accepted, as
above). It does not download the game. Then export the listings:

```sh
.venv/bin/python tools/analyze.py \
  --ghidra-home "/path/to/ghidra_12.1.3_PUBLIC" \
  --java-home "/path/to/your/jdk/Contents/Home"
```

`tools/analyze.py` imports the executable into a disposable Ghidra project,
runs Ghidra's default analyzers and exports translation inputs into ignored
`analysis/decompiled/MajestyHD - Old.exe` with the kit's export script; it
takes about two minutes and the log is `build/analyze.log`. The kit's own
`tools/setup.py` without `--link-only` is not used here: it exports with
analysis off and expects a curated annotation set, which this executable
does not have.

## Build and run

```sh
.venv/bin/python tools/build.py --regenerate --jobs 8   # translate, then compile
.venv/bin/python tools/build.py --jobs 8                # afterwards
```

The translation is where the bring-up currently stops; see
[docs/analysis.md](docs/analysis.md) for the state of it. `--target ios`
builds, signs and installs the iPad app (`RECOMP_IOS_TEAM` or `--team`) once
a macOS build runs. The CMake tree lives in `build/cmake/<preset>`.

## Check your change

```sh
.venv/bin/python tools/test.py             # the kit's portable suites; no game files required
.venv/bin/python -m pytest -q tests        # this repository's config tests
.venv/bin/python tools/build.py --stub     # link-only configure of this config through the kit
.venv/bin/python kit/tools/format.py       # handwritten native code style (kit sources)
```

See [docs/testing.md](docs/testing.md).

## Updating the kit

`git -C kit checkout <commit>` then commit the submodule pointer here, with a
changelog line naming what changed. Keep the pin on a kit tag when one exists.
