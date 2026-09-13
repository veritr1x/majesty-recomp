# Majesty Recomp

[Build & contribute](CONTRIBUTING.md) · [Port analysis](docs/analysis.md) ·
[Testing](docs/testing.md) · [Changelog](CHANGELOG.md)

A native macOS and iPad recompilation of **Majesty Gold HD** (the 2018 GOG
release of Cyberlore's Majesty: The Fantasy Kingdom Sim with its Northern
Expansion), in progress. Original game instructions are translated to C
ahead of time and compiled with the native host, the way
[populous-recomp](https://github.com/veritr1x/populous-recomp) does it.

The runtime, translator, hosts and mod foundation are
[recomp-kit](https://github.com/veritr1x/recomp-kit), pulled in as the git
submodule `kit/`. This repository holds what is Majesty's: `game.toml` and
`globals.toml` (identity, addresses, curated symbols), `tests/` (the
config's contract with the kit), `tools/analyze.py` (this game's listing
export) and docs. The kit is private at the moment, so the submodule needs
access to it.

**You need your own copy of the game.** Game executables, artwork, sound,
music, quests, generated game code and replacement packs are prepared
locally and are not included. See [NOTICE](NOTICE) for ownership and
dependency credits.

## Which executable

The GOG installer ships two game executables. This port pins
**`MajestyHD - Old.exe`** (Majesty HD 1.5.1.2, built 2011), the release
that renders through **DirectDraw**, which the kit models. The launcher's
default, `MajestyHD.exe` (1.5.2.28, built 2018), renders through
**Direct3D 9** and links the Visual C++ 2008 runtime DLLs; both are outside
the kit's supported envelope today, so that executable is not translated and
is excluded from bundles. Both play the same data. The reasoning and the
measurements are in [docs/analysis.md](docs/analysis.md).

## Status: a freestyle quest runs, with music, saves and settings; it plays on the iPad by touch

The pinned executable translates, compiles and runs: the kit's macOS app
boots to the main menu, and the kit's smoke host drives it through the name
dialog and the quest map into a running Beginner Random freestyle quest at
800x600, with effects and the narrator's voice playing. That took kit work
on the `majesty-translator` branch the submodule pins, recorded in the run
log at the end of [docs/analysis.md](docs/analysis.md).

Open items: MP3 music (the game streams it through DirectShow, which the
kit does not serve); a `GplException` the game throws on some freestyle
starts, which the kit cannot unwind and the original is reported to crash
on as well; saving. The intro is skipped because the Bink
video library is not served, which is the game's own `-nointro` behaviour.

## Build on macOS

The steps are the kit's. The submodule must be on the `majesty-translator`
branch's commit (it is, when cloned with `--recurse-submodules`); the kit's
`main` does not translate this executable yet.

```sh
git clone --recurse-submodules https://github.com/veritr1x/majesty-recomp.git
cd majesty-recomp
python3 -m venv .venv
.venv/bin/python -m pip install -r kit/requirements-dev.txt
innoextract --extract --output-dir original/gog "/path/to/setup_majesty_gold_hd_1.5.2.28_(24283).exe"
.venv/bin/python tools/setup.py --install original/gog --link-only
.venv/bin/python tools/analyze.py --ghidra-home /path/to/ghidra_12.1.3_PUBLIC
.venv/bin/python tools/build.py --regenerate
```

`original/gog` is where `game.toml` expects the game; extracting the GOG
installer there with [innoextract](https://constexpr.org/innoextract/) is
the same as linking an installed copy with `tools/setup.py --install
/path/to/installed/game --link-only`. `tools/setup.py`, `tools/build.py`,
`tools/test.py` and `tools/ios_logs.py` are four-line wrappers around the
kit's tools; every option is the kit's (`--help` lists them).
`tools/analyze.py` is this game's own: the kit's setup exports listings from
a curated annotation set, and none exists for this executable, so this
script runs Ghidra's analyzers instead. Outputs (the translation, the apps,
the logs) live under ignored `build/`; the game lives in ignored
`original/` and the Ghidra listings in ignored `analysis/`.

## Play on an iPad

Requires Xcode with the iOS SDK, an Apple developer team signed in to Xcode,
a paired iPad with developer mode on, and a macOS build already regenerated.

```sh
export RECOMP_IOS_TEAM=<your team id>       # security find-identity -v -p codesigning
.venv/bin/python tools/build.py --target ios --console
```

This builds `build/ios/**/MajestyRecomp.app`, signs it, installs it on the
paired iPad (`--device <devicectl id>` when there are several) and launches
it, streaming its console with `--console`. The app carries the game minus
`[bundle].exclude` in `game.toml` (the installer's redistributables, the mod
SDK, the Windows DLLs, the Direct3D 9 executable) and seeds it into its own
Documents on first launch, 724 MB, stamped with the executable's SHA-256 so a
rebuilt bundle is recognised. It runs fullscreen at the game's 800x600, 16
bpp, scaled to the display; the kit's pointer gestures apply (a tap places
the pointer and clicks, a long press right-clicks, a finger held against an
edge scrolls the map as the mouse on that edge would, two fingers pan with
the arrow keys, the on-screen keypad stands in for the keyboard). A
Bluetooth mouse works too; pushed against the top of the screen it scrolls
the map up even though iPadOS keeps the pointer out of the status bar strip.
Exit Game closes the app. `tools/ios_logs.py --device <id> --game-dir .`
pulls the app's Documents back to `build/ios-pull`. The session that made
taps work on the device is in the run log ("playing on the iPad by hand").

## Check a change

```sh
.venv/bin/python tools/test.py              # the kit's portable suites
.venv/bin/python -m pytest -q tests         # this game's config
.venv/bin/python tools/build.py --stub      # the kit configures against this config, no game code
```

Changes to the runtime, hosts or tools belong in the kit's repository; bump
the submodule here once they land.
