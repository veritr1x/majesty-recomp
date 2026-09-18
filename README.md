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
export) and docs. The kit is public; recursive checkout needs no separate
access token.

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

## Status: intro movies play on macOS; a freestyle quest runs

The pinned executable translates, compiles and runs. Intro movies play
through FFmpeg in the macOS app and smoke host; the headless capture
confirms non-silent movie audio. `smoke/intro.script` captures the movies
and skips to the main menu with Return. `smoke/freestyle-beginner.script`
skips both movies, then reaches a running Beginner Random quest at 800x600
with a 9-second settle before starting it. The kit is pinned to `majesty`
`4574a35`; commands, captures and results are in
[docs/analysis.md](docs/analysis.md).

Music, saves, settings and iPad touch play were verified in earlier runs.
The game's intermittent freestyle-start `GplException` remains open; the
9-second settle passed this regression run but is not a proven fix. Movie
playback on iPad at this kit pin remains the orchestrator's check.

## Platform status

Status at kit `4574a35`. Build commands assume the private game installation
and Ghidra listings are prepared as described below. macOS and mobile
results come from the recorded runs in [docs/analysis.md](docs/analysis.md)
and the orchestrator's iPad build update; Task 2.2 ran only the packager and
portable tests on macOS. Linux and Windows target current releases
supported by SDL3.

| Platform | Verified status | Build command | Remaining checks |
| --- | --- | --- | --- |
| macOS 14+ | Intro frames and Return skips verified in the app and smoke host; headless capture has non-silent movie audio. Fresh-profile smoke reaches a running Beginner Random quest. Music, saves and settings have earlier verification. | `.venv/bin/python tools/build.py --regenerate --jobs 8` | Full unskipped movies, gap-free audio and sustained performance remain unmeasured. Intermittent freestyle-start `GplException` and right/bottom edge scrolling remain open. |
| iPadOS 17+ | Plays on an iPad Pro with kit `4574a35`: the logo and intro movies play from inside the archives with sound (`bink: open` 640x480, 180 and 2204 frames; the audio sink reports no starvation), the front end follows at 800x600, and the expansion's movie opens from `DataMX/mx_cinedata1.cam`. Touch play was verified on the earlier kit. | `.venv/bin/python tools/build.py --target ios --team <TEAM_ID> --no-install` | Gameplay regression by hand on the new kit; manual save/load on the device. |
| Linux | Never built or run on Linux; packager tests use fake binaries on macOS. | `.venv/bin/python tools/build.py --regenerate --jobs 8` | Native build/package, shared-library loading, Vulkan window/driver validation, movies/audio, quest input, Save/Load and exit on hardware. |
| Windows | Never built or run on Windows; packager tests use fake binaries on macOS. | `.venv\Scripts\python tools\build.py --regenerate --jobs 8` | Native build/package, Vulkan validation, guest path separators, movies/audio, quest input, Save/Load and exit on hardware. Windows CI has not run for this change. |
| Android 10+ (Vulkan 1.1) | Stub and translated arm64-v8a APKs build with FFmpeg; no device was attached. | `.venv/bin/python tools/build.py --target android` | Installation, boot, movies/audio, touch play, Save/Load, background/resume and Exit Game on a tablet. |

## Build on macOS

The steps are the kit's. Use the submodule commit pinned by this repository;
cloning with `--recurse-submodules` checks out that commit automatically.

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

## Build on Linux

**Never built or run on Linux, including hardware playback.** The packager
tests use fake binaries on macOS. CI covers portable tests and a stub build
without game code; it does not establish native packaging or gameplay.

Start in a recursive checkout with your supported installation copied to
`original/gog`. Install Python with venv support, Ghidra 12.1.3 and a
compatible JDK as described in [CONTRIBUTING.md](CONTRIBUTING.md). The
following Ubuntu dependencies match the kit's native CI; a Vulkan-capable
driver is also required for the app:

```sh
sudo apt-get update -qq
sudo apt-get install -y -qq clang lld build-essential pkg-config libasound2-dev \
  libpulse-dev libaudio-dev libjack-dev libsndio-dev libx11-dev libxext-dev \
  libxrandr-dev libxcursor-dev libxfixes-dev libxi-dev libxss-dev libxtst-dev \
  libxkbcommon-dev libdrm-dev libgbm-dev libgl1-mesa-dev libgles2-mesa-dev \
  libegl1-mesa-dev libdbus-1-dev libibus-1.0-dev libudev-dev \
  libpipewire-0.3-dev libwayland-dev libdecor-0-dev liburing-dev \
  mesa-vulkan-drivers glslc
python3 -m venv .venv
.venv/bin/python -m pip install -r kit/requirements-dev.txt
.venv/bin/python tools/setup.py --install original/gog --link-only
.venv/bin/python tools/analyze.py --ghidra-home /path/to/ghidra_12.1.3_PUBLIC
.venv/bin/python tools/build.py --regenerate --jobs 8
RECOMP_EXE="$PWD/original/gog/MajestyHD - Old.exe" \
  build/package/MajestyRecomp/MajestyRecomp
```

After a successful app build, `tools/build.py` calls the kit's
`package_desktop.py` automatically. It writes `build/package/MajestyRecomp/`
and `build/package/MajestyRecomp-linux-<arch>.tar.gz` (`x86_64` or
`aarch64`). `RECOMP_EXE` names the original **executable**, not a directory;
its parent is the game data root. Keep `MajestyHD - Old.exe` with all its
data directories. The package includes no game files.

Linux defaults `RECOMP_VIDEO` ON in a fresh CMake cache; the first build
fetches and builds FFmpeg from source. The packager puts
`libavformat.so.61`, `libavcodec.so.61` and `libavutil.so.59` beside the app
and includes `resources/ffmpeg-NOTICE.md` in the folder and tarball. Keep
the shared libraries and `resources/` with the app. Native compilation,
library loading after moving the package away from the build tree, Vulkan
window/driver validation, movies and audio, quest input, Save/Load and exit
still need a Linux run recorded in [docs/analysis.md](docs/analysis.md).

## Build on Windows

**Never built or run on Windows, including hardware playback.** The packager
tests use fake binaries on macOS. The new `windows-2025` CI entry runs
portable tests and a stub build; it has not run for this change.

Start in a recursive checkout with the supported installation copied to
`original\gog`. Prepare the Ghidra listings with the macOS steps above and
copy the private `analysis/decompiled/MajestyHD - Old.exe/` directory to the
same ignored path in the Windows checkout. The build below regenerates C
from those listings. Install Python and LLVM's clang/lld, then use a Visual
Studio developer PowerShell with the Windows SDK and clang/lld on `PATH`:

```powershell
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r kit\requirements-dev.txt
.venv\Scripts\python tools\setup.py --install original\gog --link-only
.venv\Scripts\python tools\build.py --regenerate --jobs 8
$env:RECOMP_EXE = (Resolve-Path 'original\gog\MajestyHD - Old.exe').Path
.\build\package\MajestyRecomp\MajestyRecomp.exe
```

After a successful app build, the kit's `package_desktop.py`, called by
`tools/build.py`, writes `build\package\MajestyRecomp\`. Its `README.txt`
also shows how to launch from that folder with `RECOMP_EXE` set to the full
path of the original `MajestyHD - Old.exe`. Its parent supplies the game
data; the package contains no game files. Keep `resources\` beside the app.

The Visual Studio/MSVC-ABI compiler path keeps `RECOMP_VIDEO` OFF, so the
commands above do not enable movie decoding. The kit's video path requires
MSYS2 `bash` and GNU `make` on `PATH` plus a matching MinGW-compatible
compiler for the whole build. When enabled, packaging also stages
`avformat-61.dll`, `avcodec-61.dll`, `avutil-59.dll` beside the app and
`resources/ffmpeg-NOTICE.md`; keep these files together. Windows video
compilation, DLL loading and playback remain unverified.

Native packaging, Vulkan validation, quest input, audio, Save/Load and exit
still need hardware checks. Include game-data and save paths containing
backslashes and spaces when checking guest path separators, and record the
GPU/driver and results in [docs/analysis.md](docs/analysis.md).

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
the arrow keys, a two-finger tap right-clicks, the on-screen keypad stands in for the keyboard). A
fresh profile also shows the on-screen pad beside those keys: the right stick
steers the pointer, the left stick and the d-pad hold the arrow keys that pan
the view, Cross and Circle are the game's two mouse buttons, Square is Return,
Triangle raises the system keyboard for the player's name, L1 and R1 hold the
Control and Shift the game polls, Start opens the in-quest Options page and
Select the kit's own. `[controls]` in `game.toml` carries the whole table with
the evidence for each entry, and the settings page's Controls rows switch
layout or open the editor. **Unverified on a device at this pin:** the pad
itself has not been played by hand here. A
Bluetooth mouse works too; pushed against the top of the screen it scrolls
the map up even though iPadOS keeps the pointer out of the status bar strip.
Exit Game closes the app. `tools/ios_logs.py --device <id> --game-dir .`
pulls the app's Documents back to `build/ios-pull`. The session that made
taps work on the device is in the run log ("playing on the iPad by hand").

## Play on an Android tablet

**Build verified; device play unverified.** The stub and real translation
build into an arm64-v8a APK for Android 10 (API 29) or later, requiring
Vulkan 1.1. No Android device was attached for this check; installation,
boot, movies, audio, touch play, Save/Load and background/resume remain
unverified. The APK includes `libmain.so`, `libavcodec.so`, `libavformat.so`
and `libavutil.so` under `lib/arm64-v8a/`, plus
`assets/ffmpeg-NOTICE.md`. The first build fetches and cross-builds FFmpeg.
Measurements and build warnings are in the
[Android run record](docs/analysis.md#2026-09-14-android-apk-with-ffmpeg-task-21).

First complete the game preparation and translation steps under
[Build on macOS](#build-on-macos). Android uses the existing
`build/recomp/gen/`; omit `--stub` and `--regenerate` for the translated
build. Install Android Studio, SDK platform 36, build-tools 37.0.0,
platform-tools and NDK 27.2.12479018. On the development Mac (adjust paths
for your installation):

```sh
export JAVA_HOME='/Applications/Android Studio.app/Contents/jbr/Contents/Home'
export ANDROID_HOME="$HOME/Library/Android/sdk"
export ANDROID_NDK_HOME="$ANDROID_HOME/ndk/27.2.12479018"
export PATH="$PWD/.venv/bin:$ANDROID_HOME/platform-tools:$PATH"
.venv/bin/python tools/build.py --target android
```

The APK is `build/android/app/build/outputs/apk/debug/app-debug.apk`;
the native library is `build/cmake/android/host/libmain.so`. With no
device, the build skips installation and launch. Add `--no-install` to
build without device actions when a tablet is connected.

Enable USB debugging, connect and authorize the tablet, then run:

```sh
adb devices
.venv/bin/python tools/build.py --target android --push-game --console
```

Use `--device <adb serial>` when multiple devices are ready. The command
rebuilds as needed, installs the APK, stages `original/gog` minus
`[bundle].exclude` into `build/android/game`, pushes it, launches the
activity and streams logcat. An explicit `--push-game` requires a ready
device. The pinned DirectDraw executable and the cinematics in `Data/`
and `DataMX/` are retained; the Direct3D 9 executable, Windows DLLs and
installer support files are excluded.

Game data is pushed separately from the APK. SDL supplies the app's
external files directory, normally
`/sdcard/Android/data/dev.recompkit.majesty/files/`; the host expects
`game/MajestyHD - Old.exe` beneath it and verifies the pinned hash. Missing
data logs the expected path and push command, then exits. Android uses
these files directly. The default writable profile is
`/sdcard/Android/data/dev.recompkit.majesty/files/profile/`. Pushing data
preserves device files and the profile; back it up before uninstalling
the app or clearing its storage.

For runtime switches, put full `RECOMP_` names in external `switches.txt`.
For example, `RECOMP_FRAME_TIMINGS` takes a CSV path:

```sh
cat > build/android-switches.txt <<'EOF'
RECOMP_FRAME_TIMINGS=/sdcard/Android/data/dev.recompkit.majesty/files/frame-timings.csv
EOF
adb push build/android-switches.txt /sdcard/Android/data/dev.recompkit.majesty/files/switches.txt
adb shell am force-stop dev.recompkit.majesty
adb shell am start -n dev.recompkit.majesty/dev.recompkit.RecompActivity
# After playing and quitting normally:
adb pull /sdcard/Android/data/dev.recompkit.majesty/files/frame-timings.csv build/android-frame-timings.csv
```

Record the device/GPU, intro playback and skips, music and effects, touch
input in a quest, Save/Load, background/resume and Exit Game in
[docs/analysis.md](docs/analysis.md). These checks still need a tablet.

## Check a change

```sh
.venv/bin/python tools/test.py              # the kit's portable suites
.venv/bin/python -m pytest -q tests         # this game's config
.venv/bin/python tools/build.py --stub      # the kit configures against this config, no game code
```

Changes to the runtime, hosts or tools belong in the kit's repository; bump
the submodule here once they land.
