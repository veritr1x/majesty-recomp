# Port analysis

What Majesty Gold HD needs from the kit, measured on 2026-09-13 from the
GOG offline installer `setup_majesty_gold_hd_1.5.2.28_(24283).exe`
(693,371,256 bytes) extracted with innoextract 1.9. This is the `analyze`
stage of the kit's design (its section 3.2) done by hand, since the kit's
`analyze` command is milestone M2 work. Keep this file true as the
bring-up moves.

## Two executables

The installer's game directory holds two builds of the same game, and the
GOG launcher (`goggame-1423481910.info`) starts the second one.

| | `MajestyHD - Old.exe` (pinned) | `MajestyHD.exe` |
| --- | --- | --- |
| Version resource | Majesty HD 1.5.1.2, Cyberlore Studios, © 2000-2011 | Majesty HD 1.5.2.28, © 2000-2018 |
| Size, link timestamp | 2,986,089 bytes, 2011-06-24 | 4,058,112 bytes, 2018-10-08 |
| Linker | Microsoft 6.0 (Visual C++ 6), C runtime linked statically | Microsoft 9.0 (Visual C++ 2008), `MSVCR90.dll` and `MSVCP90.dll` imported (164 imports) |
| Graphics | **DirectDraw** (`DirectDrawCreate`, then `QueryInterface` for the 7, 4 and 2 interfaces) plus GDI DIB sections | **Direct3D 9** (`Direct3DCreate9`) plus GDI |
| Network | DirectPlay (`DPLAYX.dll`, one import by ordinal) | Winsock (`WS2_32`, 17 imports) and GOG Galaxy (`Galaxy.dll`, 8 imports) |
| Image base, entry point | `0x00400000`, `0x0064d96d` | `0x00400000`, `0x006ee1e9` |
| Relocations, TLS | none, none | none, none |
| SHA-256 | `654365fd1bdefa6d7f2349d162869f255388fadcb1bb8db9f7db2f3468dd5542` | `65c6dd32c3d873c2e320bdaa2de1b00488af85b44573fd0fd82f79a2ffd37792` |

The kit models DirectDraw through version 4 and fixed-function Direct3D 2;
shader-model Direct3D 9 is outside its envelope (the same wall
nfsmw-recomp stands at), and nothing in the kit serves a dynamically
linked Visual C++ runtime. The 2011 build is therefore the one this
repository pins; the 2018 build is recorded here and excluded from bundles.
Both read the same `Data/`, `DataMX/`, `Quests/` and `QuestsMX/`.

## The pinned executable

| | |
| --- | --- |
| Sections | `.text` 2.5 MB code (`0x00401000`, 0x27d2bd bytes), `.rdata` 0x38c9e, `.data` 0x6cbe0 (0x4cbe0 of them uninitialised), `.rsrc` 0xd18 |
| Packing, protection | none: plain Visual C++ 6 code with statically linked CRT, structured exception handling prologues (`FS:[0]`) throughout |
| Sentinel padding | `.rsrc` ends at `0x00725d18` and its section is mapped to `0x00726000`; the 744 bytes between are zero in the file and never referenced. `game.toml` parks its unidentified hooks and globals in the last 512 (`0x00725e00`-`0x00725fff`). |
| Command line | `-nointro`, `-nocdaudio`, `-nosound`, `-nocinesound`, `-nosuspend`, `-softwarecursor`, `-useddblit`, `-useglblit`, `-compatibleblit`, `-blitmovietobackground`, `-edgescroll`, `-extracheats`, `-debugout`, `-gplpath`, `-inifile`, `-localdata`, `-lobby`, `-recorder` and others read by one parser at `0x004d85b0` |
| Settings | `MajXPrefs`, an XML file under `<My Documents>\My Games\MajestyHD` (`PixWidth`, `PixHeight`, `PixDepth`, `Windowed`, `VSync`, `BlitMode`, `IntroVideo`); the installer seeds it with 1024×768×32, full screen, intro on. Registry under `HKCU\Software\Cyberlore\Majesty Expansion` (`MajestyInstallPath`, `SaveGamePath`, `LastSaveGameUsed`, sound format) |
| Saves | `SaveGame` under the same `My Games\MajestyHD` directory, found through `SHGetSpecialFolderPathA` |

## Import surface

258 imports across 10 DLLs. "Shimmed" counts the imports the kit's shim
tables (`runtime/`, `dx/`) name as of the kit's `game-dir-wip` snapshot
(81594e8); the rest bind to the kit's logging trampolines, which return 0
and pop only the return address, so a missing stdcall import drifts the
guest stack when it is reached.

| DLL | Imports | Shimmed | Missing, and what the gaps are |
| --- | --- | --- | --- |
| `KERNEL32` | 137 | 109 | the `W` variants of the file API (`CreateFileW`, `FindFirstFileW`, `GetFullPathNameW`, `MoveFileW`, …: the game probes both), `GetDiskFreeSpaceA/W`, `GetLogicalDrives`, `GlobalMemoryStatus`, `GlobalSize`, `GlobalFlags`, `VirtualProtect`, `TerminateThread`, `SetErrorMode`, `SetConsoleCtrlHandler`, `GetEnvironmentVariableA`, `FatalAppExitA`, and the CRT's locale probes (`IsValidLocale`, `IsValidCodePage`, `EnumSystemLocalesA`, `GetUserDefaultLCID`) |
| `USER32` | 69 | 30 | the `W` window and message API (`RegisterClassW`, `CreateWindowExW`, `PeekMessageW`, `DispatchMessageW`, `DefWindowProcW`, `IsWindowUnicode`), `GetSystemMetrics`, `GetSysColor`/`SetSysColors`, `LoadCursorA`, `CreateIconIndirect`/`DestroyIcon` (the software cursor), `SetFocus`, `SetActiveWindow`, `GetActiveWindow`, `GetTopWindow`, `WaitMessage`, `ScreenToClient`, `FillRect`, `IsZoomed`/`IsIconic`/`GetWindowPlacement`, menus (`CreateMenu`, `AppendMenuA`, `InsertMenuItemA`, `RemoveMenu`), scroll bars (`GetScrollPos`, `SetScrollRange`, `GetScrollInfo`, `ScrollWindowEx`), dialogs (`GetDlgItem`, `SendDlgItemMessageA`) and DDE (`DdeInitializeA`, `DdeNameService`, `DdeCreateStringHandleA`, `DdeCreateDataHandle`, `DdePostAdvise`) |
| `GDI32` | 22 | 1 | everything but `GetStockObject`: `CreateDIBSection`, `SetDIBColorTable`, `GetDIBits`, `CreateCompatibleDC/Bitmap`, `SelectObject`, `BitBlt`, `PatBlt`, `DeleteDC/Object`, `GetObjectA`, the palette set (`CreatePalette`, `SelectPalette`, `RealizePalette`, `GetPaletteEntries`, `Get/SetSystemPaletteUse`) and text (`TextOutA`, `GetTextMetricsA`, `SetTextColor`, `SetBkMode`) |
| `WINMM` | 15 | 6 | the mixer API (`mixerOpen`, `mixerClose`, `mixerGetNumDevs`, `mixerGetDevCapsA`, `mixerGetLineInfoA`, `mixerGetLineControlsA`, `mixerGetControlDetailsA`, `mixerSetControlDetails`: the volume sliders) and `mciGetErrorStringA`; `timeGetTime`, `timeBeginPeriod`, `timeEndPeriod`, `timeSetEvent`, `timeKillEvent` and `mciSendCommandA` are shimmed |
| `ADVAPI32` | 5 | 5 | registry, all served |
| `SHELL32` | 2 | 1 | `SHGetSpecialFolderPathA` (the save and settings directory); `ShellExecuteA` is served |
| `VERSION` | 3 | 0 | `GetFileVersionInfoSizeA`, `GetFileVersionInfoA`, `VerQueryValueA`: the game reads its own version resource |
| `ole32` | 3 | 2 | `CoCreateInstance`: how the game creates DirectSound (see below) |
| `DPLAYX` | 1 | 0 | one import by ordinal (#4); multiplayer is out of scope and needs a stub that fails cleanly |
| `DDRAW` | 1 | 1 | `DirectDrawCreate` |

155 of 258 imports are shimmed. None of the gaps is a design problem: each
is a run-report item in the kit's `runtime/` or a new `gdi32` shim file.
The two shapes worth planning for are the `W` variants (the game calls
`IsWindowUnicode` and takes the wide path when it can, so the shims should
answer `RegisterClassW` and `CreateWindowExW` as their `A` twins) and GDI,
which the kit has never needed.

## Graphics: inside the envelope, with a GDI side

The game draws through DirectDraw. Its device setup (three copies of one
routine at `0x00516510`, `0x00516770` and `0x005169d0`, one per blit mode)
creates the object with `DirectDrawCreate`, asks `QueryInterface` for the
version 7, 4 and 2 interfaces in turn and logs `Using DirectDraw7
Interface`, `Using DirectDraw4 Interface` or `Using DirectDraw2 Interface`
depending on which it got; `Couldn't QI DDraw2` is the failure. The kit
defines `IDirectDraw`, `IDirectDraw2` and `IDirectDraw4` with surfaces 1
through 4, so a refused `IID_IDirectDraw7` lands the game on the version 4
path the kit already serves for Populous. Whether every surface method the
game then calls exists in the kit's `dx/ddraw.cpp` is the first run report.

Beside DirectDraw the game keeps a GDI path: `CreateDIBSection` and
`BitBlt` back the `-useddblit`/`-compatibleblit` switches and the
`BlitMode` setting, `CreatePalette`/`RealizePalette` the 8-bit modes, and
`TextOutA` with `GetTextMetricsA` draws text into DIBs. The kit has no
`gdi32` shims beyond `GetStockObject` and `GetSystemPaletteEntries`; a
DIB-section shim that hands the game guest memory it can draw into, and a
`BitBlt` that copies it onto the DirectDraw primary, is the graphics work
this game adds to the kit. The cursor is a `CreateIconIndirect` icon
unless `-softwarecursor` is passed, in which case it is a DirectDraw
surface, which is what the kit's cursor hook expects.

UI layouts ship for 14 resolutions (`Data/UIData_<w>_<h>.dat`: 800×600,
1024×768, 1280×768, 1280×800, 1280×960, 1280×1024, 1360×768, 1440×900,
1600×900, 1600×1200, 1680×1050, 1920×1080, 1920×1200), so the display
resolution is a `MajXPrefs` value, not a patch.

## Sound, video, time, network

- **DirectSound** is created with `CoCreateInstance` (`0x00533b80`, whose
  failure string is `Direct Sound: Failed to initialize DirectSound
  object`), not `DirectSoundCreate`. The kit has the `IDirectSound` family
  but no `CoCreateInstance`; a shim that recognises `CLSID_DirectSound` and
  returns the kit's object is the audio item. Music is five MP3 files in
  `Music/` (31 MB) named by `Data/MusicTracks.txt`; how the game decodes
  them (there is no MP3 library in the import table) is a question for the
  listings. CD audio goes through `mciSendCommandA`, shimmed; `-nocdaudio`
  exists.
- **Bink video** for the intro and cinematics (`Data/cinedata*.dat`,
  `DataMX/mx_cinedata*.dat`) is loaded at run time from `BINKW32.DLL` by
  name. Kit `4574a35` serves the dynamic imports and decodes the movie from
  the archive reader's positioned file handle through FFmpeg. The game's
  `Unable to find BINKW32.DLL` fallback is no longer taken. Movie frames,
  Return skips and non-silent headless audio are recorded in Task 1.3 below.
- **Time** is `timeGetTime` with `timeBeginPeriod`, plus `GetTickCount`
  and `QueryPerformanceCounter`; the kit's frame-clock hook identifies
  draw-loop waits by `GetTickCount` return addresses, and whether this
  game's limiter goes through it is a question for the listings.
- **Input** is user32: `GetCursorPos`, `SetCursorPos`, `ClipCursor`,
  `GetAsyncKeyState`, `GetKeyState` and window messages. No DirectInput,
  so the kit's `mouse_*` hooks (a DirectInput device object) may never be
  real for this game; the touch mapper would attach to the message pump.
- **DirectPlay** (one `DPLAYX` import by ordinal) and DDE are the LAN game
  and the InstallShield-era launcher handshake; both stub to failure.

## Data

| Directory | Size | |
| --- | --- | --- |
| `Data` | 380 MB | the base game: `.cam` archives, bytecode, cinematics, UI layouts |
| `DataMX` | 271 MB | the Northern Expansion |
| `Music` | 31 MB | five MP3 tracks |
| `Quests`, `QuestsMX` | 624 KB | quest scripts (`.q`) and their `.mqxml` metadata |
| `SDK` | 22 MB | Windows mod tools (`RGSeditor.exe`, `Gplbcc.exe`, a Steam library), excluded from bundles |
| `__redist`, `__support`, `commonappdata`, `tmp`, `app` | 111 MB | Visual C++ 2008 and DirectX redistributables, the seeded `MajXPrefs`, GOG's uninstaller and web cache, excluded |

Paths inside the executable are relative to the installation (found through
`GetModuleFileNameA` or `MajestyInstallPath`) and mixed case (`MajX\Data\`,
`UIData_*.dat`); the kit's case-folded path index handles that. Settings and
saves go under the `My Games\MajestyHD` directory `SHGetSpecialFolderPathA`
returns, which the kit has yet to answer.

## Translation

The kit's translator reads Ghidra listings and emits one C function per
original function. `tools/analyze.py` exports them with Ghidra's default
analyzers (`analysis/decompiled/MajestyHD - Old.exe/summary.txt` gives the
count). The translator's own coverage report,
`build/recomp/translate-report.json`, is the record of unsupported
instructions and unresolved indirect targets once a run gets far enough to
write it.

### Run log

Recorded runs of the pipeline against this executable, newest first.

#### 2026-09-14: intro playback and quest regression at 4574a35 (Task 1.3)

Continued at Step 3 after Tasks 1.1, 1.2, 1.4 and 1.5. The clean kit
checkout was already on `majesty` at
`4574a35c3702a9750516c545a39c136cb1808432` (`git -C kit rev-parse HEAD`,
exit 0); `git add kit` stages the game pin's move from `d36f25a` to this
commit. No kit source changed here. `git -C kit rev-list --count
31f0f24..4574a35` returned 34: the earlier 30 commits plus the four Bink
commits. The executable, config addresses and player profiles are unchanged.

Builds from the game root, each redirected to the named file under
`build/task-1.3/` with `> <log> 2>&1`:

| Command | Exit | Result / log |
| --- | --- | --- |
| `.venv/bin/python tools/build.py --regenerate --jobs 8` | 0 | Regenerated and linked the macOS app; `regenerate.log` |
| `.venv/bin/python tools/build.py --target smoke --jobs 8` | 0 | Linked `build/recomp/pop_smoke`; `build-smoke.log` |
| `.venv/bin/python tools/build.py --jobs 8` | 0 | No work to do; `build-app.log` |
| `cmp build/recomp/gen/x86.h kit/runtime/x86.h` | 0 | Generated runtime header matches the kit |
| `.venv/bin/python tools/build.py --jobs 8` (Step 4) | 0 | No work to do; `build-app-step4.log` |

Translation emitted 24,178 of 24,179 functions and 26,230 entry points in
17.7 s (122 chunks). One guessed block, `0053bee0`, was withdrawn because
its target `0053c004` went nowhere; there were 0 recovery errors, 0
jump-table entries dispatching nowhere and 0 sites decoding nothing.
The builds retain keypad C-linkage return-type and linker common-section
alignment warnings.

**Step 2 evidence, retained rather than rerun.** `build/intro/run.log`
records 9 of 9 steps, guest exit 0, 20.2 s and 221 presented frames (203
different from their predecessor). To repeat it, use the smoke command below
with `intro` in place of `freestyle` and `smoke/intro.script` as the script,
choosing unused output/profile paths for any new run.
The first movie is **640x480, 180 frames at 15 fps, from `cinedata3.dat`**,
not the plan's 320x240 `cinedata2.dat` test fixture. The second open is
640x480, 2,204 frames at 15 fps from the same archive. Return at 12 s and
15.1 s skips the two movies; clicks were not needed.

Re-read the existing PPMs with Pillow and counted RGB colours: `intro-2s`
has 1 (black during the fade-in), `intro-6s` has 4,183, `intro-12s` has
1,574, `after-skip` has 475 and `main-menu` has 3,861. All five pixel hashes
differ. Visually re-inspected the 6 s logo animation, 12 s completed logo
and 800x600 main menu, with its buttons and Version 1.5.1.2. The initial
black frame is not a playback failure.

The completed Task 1.5 run under `build/task-1.5-headless/` is Step 2's
audio and clean-exit evidence (host exit 0 supplied by that task; guest exit
0 and no teardown exception in its retained log). The following command
reproduces its recorded caps, paths and dump cadence; it was not rerun in
this continuation, and another run needs unused output/profile paths:

```sh
RECOMP_PROFILE_DIR="$PWD/build/task-1.5-headless/profile" \
RECOMP_MAX_FRAMES=100000 RECOMP_MAX_SECONDS=20 RECOMP_FRAME_EVERY=60 \
RECOMP_FRAMES="$PWD/build/task-1.5-headless/frames" \
RECOMP_HOST_AUDIO_CAPTURE="$PWD/build/task-1.5-headless/movie.wav" \
RECOMP_DDRAW_MODES=640x480x8,640x480x16,800x600x16 \
build/recomp/pop_headless > build/task-1.5-headless/run.log 2>&1
```

Re-measured its WAV with Python's `wave` and `array` modules: 48,000 Hz,
stereo PCM16, 880,907 frames (18.352229 s), 1,598,500 nonzero samples,
peak 27,506/32,768 (0.8394). These match `measurements.json`. The log
reports 16.7 s not silent, 277 presented frames, five saved frames, no
undeliverable calls and zero audio channels left allocated to players.
It also reports one 1.415 s silent gap and a queue-depth accounting warning;
this proves non-silent movie audio, not gap-free playback. The earlier
`build/intro/headless/` exit-time mutex abort is superseded by Task 1.5.

**Step 3, fresh quest smoke.** Preserved the pre-existing failed
`build/freestyle/` as `build/freestyle-before-task-1.3/` and created a new
dump directory. No `RECOMP_*` switches were inherited. Ran once:

```sh
RECOMP_PROFILE_DIR="$PWD/build/freestyle/profile" \
RECOMP_SCRIPT="$PWD/smoke/freestyle-beginner.script" \
RECOMP_HOST_DUMP_DIR="$PWD/build/freestyle/dumps" \
RECOMP_DDRAW_MODES=640x480x8,640x480x16,800x600x16 \
RECOMP_SMOKE_DRAWABLE=800x600 \
build/recomp/pop_smoke > build/freestyle/run.log 2>&1
```

Host exit 0, guest exit 0, all 14 steps in 68.4 s; 2,833 presented frames,
472 different from their predecessor, 800x600 at 16 bpp, no undeliverable
calls and no `GplException`. No retry was needed. The orchestrator's prior
measurement was three throws in three runs with a 4.5 s settle after
movies, then 14 of 14 steps with 9 s in `build/freestyle-varB/`. The script
retains that 9 s settle and both Return skips; it does not fix the game's
intermittent exception.

Converted each dump with the following command (substitute `quest-8s`,
`quest-20s`, then `quest-click` for `<name>`); all three exited 0 and
reported 800x600. Looked at all three PNGs:

```sh
.venv/bin/python kit/tools/recomp/ppm_to_png.py \
  build/freestyle/dumps/smoke_<name>_present.ppm \
  build/freestyle/dumps/smoke_<name>_present.png
```

All show "Random (Beginner)", 20,000 gold, a selected palace and the
sidebar. The day-progress indicator and characters/flags change; the day
count remains 0. Unlike the Task 0.1 record's level-2 palace, 700 HP, nearby
guild and Temple to Dauros, this run shows a level-1 palace, 550 HP and no
such nearby buildings in the captured view. `quest-click` shows the
"Palace (550 of 550 hp)" tooltip and a Tax Collector. No misplaced or
clipped UI is apparent; the quest state differs, so this is not a pixel
equivalence claim. The known mod-loader warning, unavailable Bink audio
streaming in the smoke host and DirectShow refill restarts remain.

**Step 4, macOS app.** After the second app build above, created
`build/app-intro/dumps/` and launched with another fresh profile:

```sh
RECOMP_PROFILE_DIR="$PWD/build/app-intro/profile" \
RECOMP_HOST_DUMP_DIR="$PWD/build/app-intro/dumps" RECOMP_HOST_DUMP_EVERY=60 \
perl -e 'alarm 25; exec @ARGV' \
  build/MajestyRecomp.app/Contents/MacOS/MajestyRecomp \
  > build/app-intro/run.log 2>&1
```

The 25 s alarm ended the process with **exit 142 (SIGALRM)**, as prescribed;
this is not a clean guest-exit test. Used the native app UI to observe the
logo and press Return once; the next observation was the main menu, so a
second press was unnecessary. Both Bink opens appear in the log. A skip
is needed within this time cap: the second movie alone lasts 2,204/15 =
146.93 s. Converted `present_00060`, `present_00120`, `present_00180` and
`present_00240` with the command below; all four exited 0. Looked at all
four PNGs: three different 640x480 logo frames, then the complete 800x600
main menu matching Step 2's layout and version label.

```sh
.venv/bin/python kit/tools/recomp/ppm_to_png.py \
  build/app-intro/dumps/present_<number>.ppm \
  build/app-intro/dumps/present_<number>.png
```

The app starts a 48 kHz stereo audio device and movie audio streams.
Its log also records the previously seen drawable-acknowledgement timeout
and command-completion fallback; frames still reached the menu. No
sustained performance or complete unskipped movie sequence was measured.

**Step 5 checks.** Logs are under `build/task-1.3/`; every command below
was run from the game root. Native tests used `kit/games/stub`, confirmed
in the CMake cache along with `RECOMP_VIDEO=ON`, never this translation.

| Command | Exit | Result / log |
| --- | --- | --- |
| `.venv/bin/python -m pytest -q tests` | 0 | 4 passed in 0.01 s; `game-tests.log` |
| `.venv/bin/python tools/test.py` | 0 | 123 passed, 3 skipped in 6.89 s; `portable-tests.log` |
| `.venv/bin/python tools/build.py --stub` | 0 | Linked `build/stub/MajestyRecomp.app`; `build-stub.log` |
| `.venv/bin/python kit/tools/test.py --game-dir /Users/sattam.thakur/Documents/Tests/majesty-recomp/kit/games/stub --compile-only` | 0 | Native binaries up to date; `native-compile.log` |
| `RECOMP_TEST_BINK_CONTAINER="$PWD/original/gog/Data/cinedata2.dat,124" .venv/bin/ctest --test-dir kit/build/cmake/macos -R dx_tests --output-on-failure` | 0 | 1/1 passed, 0 failed, 0.13 s; `dx-container.log` |
| `.venv/bin/ctest --test-dir kit/build/cmake/macos -R "dx_tests\|host_tests" --output-on-failure` | 0 | 2/2 passed, 0 failed, 0.81 s; private Bink fixture skip messages present without the variable; `dx-host.log` |
| `git diff --check` and `git diff --cached --check` | 0 | No whitespace errors in the task changes |

All game inputs, profiles, captures, generated files and run logs remain
under ignored directories. No iOS build or device intro check was run;
that verification belongs to the orchestrator. No push was performed.

#### 2026-09-14: re-pin the kit to main 4ab4604 on majesty (Task 0.1)

The kit moves from `31f0f24` to `4ab4604` on its new `majesty` branch.
In `kit/`, these commands each exited 0:

```sh
git remote add local /Users/sattam.thakur/Documents/Tests/recomp-kit
git -c protocol.file.allow=always fetch local main
git checkout -B majesty local/main
git log --oneline -1
```

The final command printed `4ab4604 ddraw: releasing the mode-setting object
restores the desktop`. No kit source or game config change was needed.
Checks from the game repository, in order:

| Command | Exit | Result |
| --- | --- | --- |
| `.venv/bin/python -m pytest -q tests` | 0 | 4 passed in 0.01 s; no schema additions needed |
| `.venv/bin/python tools/test.py` | 0 | 123 passed, 3 skipped in 7.07 s |
| `.venv/bin/python tools/build.py --stub` | 0 | Linked `build/stub/MajestyRecomp.app` |
| `.venv/bin/python tools/build.py --regenerate --jobs 8` | 0 | Regenerated the translation and linked `build/MajestyRecomp.app` |
| `.venv/bin/python tools/build.py --target smoke --jobs 8` | 0 | Linked `build/recomp/pop_smoke` |
| `.venv/bin/python tools/build.py --jobs 8` | 0 | App up to date; Ninja reported no work to do |

Translation emitted 24,178 of 24,179 functions and 26,230 entry points in
19.0 s (122 chunks); one guessed block, `0053bee0`, was withdrawn because
its dispatch target `0053c004` went nowhere. There were 0 recovery errors,
0 jump-table entries dispatching nowhere and 0 sites decoding nothing.
The generated `build/recomp/gen/x86.h` was compared byte for byte with
`kit/runtime/x86.h` and matched. Builds succeeded with warnings: FFmpeg
numeric conversions and linker options/search paths, host keypad C-linkage
return types, and the translated app/smoke linker's common-section alignment
reduction. These were not changed in this re-pin.

Regression smoke used a fresh, previously nonexistent profile and dump
directory, with no inherited `RECOMP_*` switches:

```sh
RECOMP_PROFILE_DIR="$PWD/build/repin/profile" \
RECOMP_SCRIPT="$PWD/smoke/freestyle-beginner.script" \
RECOMP_HOST_DUMP_DIR="$PWD/build/repin/dumps" \
RECOMP_DDRAW_MODES=640x480x8,640x480x16,800x600x16 \
RECOMP_SMOKE_DRAWABLE=800x600 \
build/recomp/pop_smoke > build/repin/run.log 2>&1
```

- Host exit 0, guest exit 0, 10 of 10 script steps in 48.7 s; 2,472
  presented frames, 272 different from their predecessor, final display
  800x600 at 16 bpp, no undeliverable calls, all script expectations met.
- This run did **not** reach the predicted null Bink call. Its log says
  `LoadLibraryA("binkw32.dll"): no shims for that module, reporting it as missing`.
  The intro remained skipped; the movie path and the three missing Bink
  exports were not exercised. Their handling remains Task 1.2's work.
- Converted each dump with
  `.venv/bin/python kit/tools/recomp/ppm_to_png.py build/repin/dumps/smoke_<name>_present.ppm build/repin/dumps/smoke_<name>_present.png`,
  substituting `quest-8s`, `quest-20s`, then `quest-click`; all three commands
  exited 0 and reported 800x600. All three PNGs were visually inspected.
  Each shows "Random (Beginner)", the selected level-2 palace, 20,000 gold,
  the sidebar, nearby guild and Temple to Dauros. Flags and the day-progress
  indicator change between the first two; the day count remains 0. The
  click dump shows the palace's 700-of-700-hit-points tooltip. No placement
  difference or clipping was apparent against the task's expected quest
  description; this was not a pixel comparison with an old-kit run.
- The smoke still reports the mod-loader failure and the DirectShow chunk
  restart limitation already recorded below. This run establishes the
  scripted quest screen, not movie playback or sustained app performance.

Build logs, the smoke log, dumps and profile remain under ignored
`build/repin/`. No iOS build was run; that check belongs to the orchestrator.

#### 2026-09-13 (late night): playing on the iPad by hand

Build 3 to build 9 on the iPad Pro (iPadOS 17+, 1210x834 points, 2420x1668
pixels; the game at 800x600 letterboxed with 98-pixel pillars). The console
was streamed with `devicectl device process launch --console` and the kit's
`RECOMP_TRACE_POINTER=1` reached the device through `Documents/switches.txt`.
Everything below is kit work on the `majesty-translator` branch, uncommitted
at the time of writing; each item has an `input_touch_tests` case.

- Taps landed nowhere. Two causes, found in this order. First, the game polls
  its mouse buttons once per frame with `GetKeyState(VK_LBUTTON)`
  (`FUN_004f6590`) and presents at 16 frames a second on the iPad (3917
  presents in 238 s), so the touch mapper's 90 ms clock-timed press and
  release often fell between two polls. The release now also waits for two
  presented frames after the press (`TouchMapper::frames_presented`, fed from
  the host's present count), with a 400 ms ceiling for a game that stops
  presenting. Second, and worse, the mapper read the press point back out of
  the action vector after pushing the press into it, past a reallocation; on
  the device the release then carried 0,0, so every tap pressed one control
  and released on another (nothing happened), and the game's cursor was moved
  to 0,0, where its edge scroll lives, so the view flew to the map's top-left
  corner after each tap. With both fixed, the user's taps take Play Game,
  ACCEPT, the quest map and OK into "The Bell, the Book, and the Candle" and
  select buildings there; 22 taps, every release at its press point.
- The top edge. iPadOS keeps a 32-point strip along the top (the status bar,
  visible in screenshots despite `UIStatusBarHidden`) and 25 at the bottom;
  a finger on the top bezel arrives no closer than 32 points down and a
  hardware pointer stops there too, so the mapper's 16-point edge snap never
  saw either. The snap margin now grows by the window's safe-area inset on
  each edge (`set_edge_insets`, from `SDL_GetWindowSafeArea`), and a pointer
  resting within 16 points of the strip's inner side is placed on the edge
  behind it (`pointer_behind_strip`). A finger held at the top scrolls the
  map up (user, build 6). The mouse pushed against the top scrolls the map up
  (user, build 10; the unthrottled trace shows the pointer resting at 33 to 41
  points, every event delivered as row 0). The game's edge scroll ramps up
  over a second of the cursor staying in the 8-row zone (`FUN_00440500` times
  it), which is why a hand wandering 8 points in and out of the zone looked
  like nothing, and why the first slack of 4 points was not enough.
- A drag the system cancels (an edge gesture iOS claims) released its button
  at 0,0 as well; it releases where the cursor was placed now.
- Still open: the right and bottom edges do not scroll in the smoke host
  either (left does, 90% of the map moved; right at x 795 and bottom at y 595
  did not), so that is the game under the kit, not the touch layer. The kit's
  settings page opened several times during the session: its key is F10, which
  the on-screen keypad and the three-finger tap both send. Exit Game closes the
  app on the iPad since build 3 (`platform_ui_process_exit`). The music
  "no such file" line for a bare `GeneralTheme.mp3` is the game's first try
  before the `Music\` path, as on the Mac.

#### 2026-09-13 (night): how the camera moves, measured

Smoke host, a running Beginner quest, the map view compared pixel for pixel
between frames (the sidebar excluded). Kit commit "Smoke scripts: button" adds
`button <side> down|up` so a drag can be scripted.

- Right-button drag across the map: the view does not pan (6% of the map
  changed, the cursor and animation). The press deselects the palace, as a
  right click does. Left-button drag: nothing.
- Arrow keys pan the view (95% of the map changed after 1.5 s of RIGHT, and
  again after LEFT and UP). A click on the minimap jumps the camera (97%).
- Edge scrolling: the pointer held on the top edge (y 0..7, and y = -10)
  scrolls the map up (97%). Held on the right edge (x 793..799, also 850,
  911, 950), on the bottom edge (y 595..599) or at the map viewport's own
  edges (x 212, 230, 785; y 538, 548), for 1.5 to 3 s, with and without the
  game's `-edgescroll` switch, before and after moving the camera up-left
  with the arrows: no movement in eleven probes. The game's edge routine
  (`FUN_00440300`, called from `FUN_00490a30`) compares the cursor from
  GetCursorPos + ScreenToClient against its display object's 800x600 (peeked
  live at `0x011001e0`+0x14/+0x18, ScrollSpeed 32); its translation matches
  the listing instruction for instruction, so why only the top edge moves is
  not established here. It may behave the same on Windows for this build;
  worth one check against the original.
- For the iPad this means: arrow keys through the keypad and taps or drags on
  the minimap move the camera reliably; the edge-hold gesture moves it up
  from the top edge and is unverified for the other three sides; the
  long-press drag (a wheel-button drag) does nothing in this game.

#### 2026-09-13 (evening, later): the iPad app boots

`tools/build.py --target ios --device <iPad> --team <id>` from this
repository: the kit's iOS preset configured, Xcode built and signed
`MajestyRecomp.app`, `devicectl` installed it on an iPad Pro 11-inch (M4) and
launched it. From the device console:

- The app seeds the bundled game into its Documents (`Documents/game/`, 724 MB,
  stamp `654365fd...`), maps the executable from there (entry 0064d96d) and
  opens a 1210x834-point, 2420x1668-pixel Metal window.
- The game sets its display modes as on macOS (800x600 16 bpp, a moment at
  640x480 while the menu loads) and reaches the main menu: the menu's music
  opens through the DirectShow shims, channel 0 becomes a stream, and the
  audio sink reports 4222 pulls with none late or starved over two minutes.
- The mod loader "reported a failure" as on macOS (no usable symbol table for
  this game); the overlay is installed first now, so saves and settings will
  go to the app's own profile directory.
- Screenshots through a `pymobiledevice3` developer tunnel (`developer dvt
  screenshot`, saved under `build/ipad/`): the loading screen and then the
  main menu fill the 2420x1668 display, buttons, map and "Version 1.5.1.2"
  in place. iPadOS draws its status bar (clock, battery) over the top edge
  despite `UIStatusBarHidden`; the presenter logged one "drawable
  acknowledgement exceeded queue grace" fault and fell back to command
  completion, as the kit does, with no visible effect.
- Not checked here: touch. The tunnel takes screenshots but injects no
  input, so whether a tap starts a quest and the keypad enters the player's
  name is for a hand on the iPad to confirm. `tools/ios_logs.py` pulled
  Documents; no save or preference had been written yet, as nothing was
  touched.

#### 2026-09-13 (later still): hooks judged, cleanup

- Hooks. Every `[hooks]` address in `game.toml` stays a sentinel, now with
  the reason beside it. The kit's frame-clock hook attaches to GetTickCount
  return addresses of a draw-loop wait; this game paces its main loop
  (`FUN_0049ac60`) on `timeGetTime`, so there is no site, and the app runs at
  the display's rate without one. Its cursor is composed into the frame by the
  game itself, so the host-drawn pointer hook has nothing to point at. The
  mouse comes through user32, never DirectInput. The smoke camera record is
  not identified and the scripts here judge frames instead.
- Version label. The main menu's "Version" read its string through
  VERSION.dll, which served nothing; the kit now serves the executable's own
  VS_VERSIONINFO (1.5.1.2, "Majesty HD") from the mapped image.
- The game's debug log no longer reports "Unable to enum DirectShow filter
  graph": the graph hands out an empty filter enumerator.
- The runtime's log lines carry `[recomp]` rather than another game's tag.

#### 2026-09-13 (late): settings and saves live in the profile

Kit branch `majesty-translator` (commit "File seam: the write tier at the
first write"). Driven with the smoke host.

- Where the game writes. It keeps its preferences (`MajXPrefs`, XML), its
  quest data (`questdata_majx.sav`) and its saves (`SaveGame\*.GMP`) under
  `<CSIDL_PERSONAL>\My Games\MajestyHD\`, its volumes and last-used names in
  the registry (`HKCU\Software\Cyberlore\Majesty Expansion`: `SFXVolume`,
  `VoiceVolume`, `CDVolume`, `ScrollSpeed`, `LastSaveGameUsed`, ...), and its
  `err.log` at the guest root. With the kit's overlay as the writable tier all
  of it lands in the profile: `build/recomp/profile/Documents/My Games/
  MajestyHD/` for the files, `build/recomp/registry.json` for the registry,
  and nothing is written into `original/gog` any more (the earlier runs had
  left a `Documents/` tree and `err.log` there, now removed).
- Two kit faults stood in the way. The mods loader gave up before installing
  the overlay when a port has no symbol table it can use, so no writable tier
  existed; it installs the overlay first now. And the file seam classified
  every `CreateFileA` with GENERIC_WRITE as a write, so the game's habit of
  opening its `.cam` archives read/write copied 590 MB of archives into a
  fresh profile at every first run - and a copy cut short by the smoke
  watchdog left a truncated archive that hung the next run. A handle opened
  for writing on an existing file now goes through the read tier and moves to
  the write tier at its first `WriteFile`; the profile is 350 KB after a save.
- Verified: Escape in a quest opens Options; Save Game, confirm, and a
  320 KB `(Freestyle Game) 0 Days.GMP` appears in the profile ("Game Saved.").
  A later run lists it in Load Game, and loading it restores the saved
  kingdom (Palace level 2, the dwarven settlement). The registry file holds
  the game's volume settings written at exit and is read back at boot
  ("registry: loaded 1 keys"). Moving the Levels sliders by synthetic clicks
  on their arrows or tracks did not register in the smoke host, so a changed
  volume surviving a restart is not shown by this run; the storage path is.
- Main menu: "Adjust Settings" prompts for the player's name and then shows
  the quest map, the same as Play Game does here; in the HD release the
  display settings belong to the launcher, not this executable.

#### 2026-09-13 (night): music plays

Kit branch `majesty-translator`, rebased onto kit main (m1.2) and carrying the
new `dx/dshow.cpp`. Driven with the headless host and the smoke host.

- The game plays its MP3 tracks through DirectShow multimedia streaming, and
  it has two players behind one switch (`FUN_005337f0`, mode at
  `DAT_00719634[0]`): a sample-pulling one (`FUN_005332d0`: IAudioMediaStream,
  `CLSID_AMAudioData`, `IAudioStreamSample::Update` into its own DirectSound
  stream) and a graph-driving one (`FUN_00563840`: `GetFilterGraph`, then
  IMediaControl, IMediaEventEx, IMediaSeeking, IBasicAudio). At run time the
  mode is 1 and the graph player is used: SetPositions(0) + Run to start,
  Stop to pause, a 50 ms multimedia timer polling the completion event and
  `GetEvent` for EC_COMPLETE, `put_Volume` from the music slider. The kit now
  serves both; the graph path decodes with minimp3 and streams the PCM to a
  host channel from the frame pump.
- Headless host, 30 s at the main menu with `RECOMP_HOST_AUDIO_CAPTURE`: the
  game logs "Playing digital music track: GeneralTheme.mp3" once, the mixer
  converts channel 0 to a stream once, and the capture holds 25.7 s of sound
  in 28.4 s with one voice live and no restart or underrun. The level is what
  the game asks for through IBasicAudio (its default music volume is low,
  loudest sample 0.065); effects are unchanged.
- The smoke host cannot continue a sound (no `host_audio_stream`), so under
  it the stream is restarted at every refill, as the DirectSound shims are
  too. Judge music in the headless host or the app, not the smoke host.
- Cosmetic: the game logs "Unable to enum DirectShow filter graph" once per
  track because `IFilterGraph::EnumFilters` is E_NOTIMPL; it only lists the
  filters for its debug log and carries on.
- Before this the first `OpenFile` of each track is the bare name
  (`GeneralTheme.mp3`), which does not exist at the guest root; the game
  retries with the full `Music\` path and that opens.

#### 2026-09-13 (evening): a Beginner Random quest runs; the freestyle start can throw

Kit on branch `majesty-translator` (see the submodule pin), game.toml unchanged.
Driven with the kit's smoke host and `smoke/freestyle-beginner.script`.

- Input: clicks and keys reach the game through user32 (`WM_LBUTTONDOWN`,
  `GetCursorPos` + `ScreenToClient`, `WM_CHAR` from `TranslateMessage`).
  Play Game, the name dialog (Return accepts the default), the quest map,
  Freestyle Quests and Beginner Random all respond. `ScreenToClient`,
  `GetActiveWindow` and `SetFocus` were the missing shims; the stray call to
  `0071c648` was their stack drift and is gone.
- The quest loads and runs: "Random (Beginner)", the palace, 20,000 gold, the
  sidebar, buildings appearing, the game clock advancing, at about 370
  frames a second in the smoke host. Effects and the narrator's voice play
  through the DirectSound buffers the game creates.
- Two translator gaps found on the way, both fixed in the kit: recovery from
  the PE followed the fall-through after `__CxxThrowException` into a switch
  table and rejected the vtable-named function `0x625910` as data; and a
  `PUSH 0x5b2370` was dropped because its address bytes read as text.
- Verification: the differential sweep over 1,254 loop-free leaf functions
  agrees with Unicorn (the five reported differences are undefined flags after
  a callee's `IDIV`, NaN payloads and x87 transcendental precision, none a
  translation fault), and a targeted differential check of the CRT's
  `memcpy` (both copies, through the decoded jump tables), `memset`,
  `strlen`, `memcmp`, `strcmp`, `strncmp`, `strncpy`, `strchr`, `strstr`,
  `__alldiv`, `__aulldiv`, `__aullrem` and `__allmul` passes 60 random cases
  each.
- Open: starting a freestyle quest 2-3 s after the Freestyle dialog opens
  (or under a pinned clock of `1:250`) throws the game's own `GplException`
  "bad conversion to list&": a `GplNull` where the script expected a list,
  from a natively driven list conversion (`0x00624970`, called from the
  interpreter at `0x00639a9d`), with no `catch` for it anywhere in the image
  (the only catch clauses are three `catch(...)` in CRT code and four typed
  ones for XML, dialog and regex errors). The kit cannot unwind a C++ throw,
  so it aborts where Windows would show a crash dialog. Players of the
  original report random freestyle crashes, so this is most likely the
  game's own bug; whether this runtime hits it more often is not known.
  The game's log (`RECOMP_GUEST_ARGS=-debugout`, written to
  `original/gog/err.log`) shows nothing unusual before it. The music state
  machine, the multimedia timer callback and file lookups were ruled out as
  triggers by experiment; the seed and frame timing both influence it.
- Music: the game plays its MP3 tracks through DirectShow multimedia
  streaming (`CoCreateInstance(CLSID_AMMultiMediaStream)`, `IAMMultiMediaStream`,
  `IAudioMediaStream`, `CLSID_AMAudioData`, `IAudioStreamSample`), which the kit
  does not serve; its log says "Unable to play digital music track". CD audio
  through MCI is refused, as on a machine without the disc.
- Pinned clock note: with `RECOMP_PIN_CLOCK=<start>:16` the game
  busy-waits on `timeGetTime` without presenting and never advances; steps of
  33 ms and up run.

#### 2026-09-13 (later): the main menu renders

Kit on branch `majesty-translator` (58d32c2, on top of 81594e8), pinned by
the submodule. Everything below is kit work; nothing in `game.toml` changed.

Translation: `tools/build.py --regenerate` now emits and compiles the whole
program: 24,168 of 24,170 functions (the two left out are recovered blocks
the sweep withdrew as data), 26,246 entry points, in 17 seconds, and the C
compiles in about a minute with no warnings. What it took, in the kit's
translator: the ten instruction forms of the previous entry plus `PUSHF`/
`POPF` and segment-register `MOV`s; the CRT `memcpy`'s jump-table shapes (an
`AND` mask bound with an unused slot 0, `CMP`/`SUB` guards that branch to
the jump, a negated index); a trap instead of a dangling dispatch where a
listing ends on `__CxxThrowException`; and a pushed immediate that decodes
as a ten-byte destructor thunk accepted as an entry, which is how the CRT's
`atexit` table reached functions Ghidra never listed.

Runtime: the app finds `original/gog` without a dialog (the developer
executable is an absolute path now), the two-component guest root resolves
(`C:\GOG Games\Majesty Gold HD\...` opens the same file as a relative
path), and the boot path's imports are shimmed with their argument counts,
so the guest stack no longer drifts: the CRT's locale probes,
`GlobalMemoryStatus`, `SetErrorMode`, `GetLogicalDrives`,
`SHGetSpecialFolderPathA` (the per-user folders live under the guest root,
so settings and saves land in `original/gog/Documents/My Games/MajestyHD`),
`IsWindowUnicode` (ANSI, so the game takes its `A` window path),
`GetSystemMetrics`, `LoadCursorA`, `CreateIconIndirect`, the mixer API (no
driver), `mciGetErrorStringA`, `VERSION.dll` (no version resource), and
`CoCreateInstance` for `CLSID_DirectSound` with `Initialize` succeeding. A
new `runtime/gdi32.cpp` gives the game its DIB section: the frame buffer it
renders into is a 16-bit 565 top-down DIB in guest memory, which the game
then moves onto the DirectDraw primary itself.

Result: the headless host (`tools/build.py --target headless`, then
`build/recomp/pop_headless` with `RECOMP_MAX_SECONDS=40`) presents the
main menu at 800x600 16 bpp: 355 frames in 40 seconds, 794 distinct colours,
every menu button and the "Version" label in place, and the game exits
cleanly on `WM_CLOSE`. The windowed app (`build/MajestyRecomp.app`) presents
at about 70 frames a second. The intro is skipped because `BINKW32.DLL` is
reported missing, which is the game's own `-nointro` path; the `Version`
label is empty because `VERSION.dll` serves no resource.

Not yet exercised: input (the game reads the mouse through user32, not
DirectInput, so the kit's pointer gate is bypassed and a click has not been
tried), sound through the DirectSound buffer the game created, the MP3
music, entering a quest, saving. One `call to unknown target 0071c648` (a
pointer into `.data`, from the instruction before `0x004f5ff1`) is logged
during the menu and needs a look. The `game`-labelled kit test binaries
carry Populous literals and report those as failures against this game;
the sections added for this bring-up pass.

#### 2026-09-13: listings exported, translation stops fourteen functions short of emitting

Kit at `game-dir-wip` (81594e8). Ghidra 12.1.3's default analyzers, run
by hand with the `analyzeHeadless` command `tools/analyze.py` issues (the
wrapper itself has not been exercised end to end yet): 14,953
functions discovered, all 14,953 decompiled, 0 failed, 127 MB of listings
in two minutes. The stub configure links `build/stub/MajestyRecomp.app`
against this config; the kit's portable suites pass through the wrappers
(56 passed, 3 skipped) and this repository's config tests pass (4).

`tools/build.py --regenerate --target gen` parses every listing in
fifteen seconds and stops at the translator's discovery gates before
emitting any C:

| Gate | Count | What it is |
| --- | --- | --- |
| jump-table sites that decoded no entries | 6 | three `switch` dispatches in each of two identical 231-instruction Visual C++ 6 runtime routines, `fn_0064e6f0` and `fn_00650720`, whose tables the decoder does not recognise |
| jump-table entries with no block entry | 0 | |
| literal dispatch targets that are not entry points | 112 | direct calls to four functions the translator dropped: `0x00501850` (11 of the 20 call sites the translator prints), `0x0053cae0`, `0x00498480`, `0x0045fee0` |

The third gate is the interesting one, and it is not a listing problem:
all four targets are functions Ghidra listed. They are absent because the
translator failed them, and a run instrumented to print its failure list
shows 14 functions failing on ten instruction forms the translator does
not handle:

| Instruction | Functions | Where |
| --- | --- | --- |
| `LOOP` | 4 | `0x00501988`, `0x0054fcc2`, `0x0054fd73`, `0x00550194` (string and memory helpers in the CRT and the game) |
| `INT3` | 2 | `0x0053caf2`, `0x005a93c8` (debug-break checks on a flag, `0x0071b384`) |
| `CLC` | 2 | `0x00559717`, `0x005599bd` |
| `REPE CMPSD` | 2 | `0x00460170`, `0x006511c7` (`memcmp`-shaped compares at dword width) |
| `PUSH AX` | 1 | `0x00501867` (a 16-bit push) |
| `MOV word ptr [ECX], CS` | 1 | `0x00499215` (a segment-register store in an exception-record writer) |
| `FPTAN` | 1 | `0x00664911` (the CRT's `tan`) |
| `FSAVE` | 1 | `0x0064f501` (the CRT's floating-point environment save) |

Every one of these is a bounded translator addition in the kit
(`tools/recomp/translate.py`, semantics in `runtime/x86.h`), and the
`0x00501850` helper (a 91-byte routine with `PUSH AX` and a `LOOP`) is
the one most of the printed call sites want. Until they land nothing
compiles and no run report exists, so the instruction-level coverage of
the other 14,939 functions is unmeasured: the translator gates on control
flow before it emits code. The 6 untyped jump tables are accepted with
`--allow-table-gaps` for measurement only; the two CRT routines they live
in still need their tables decoded before the game can format text.

Order of work from here, all of it in the kit:

1. Translator: the ten instruction forms above, then the two CRT switch
   tables, until `--regenerate` emits and compiles the translation.
2. Run report on the stub hosts: which `kernel32`, `user32`, `gdi32` and
   `winmm` calls the boot path makes; the `W` window API answered as its
   `A` twins; `SHGetSpecialFolderPathA`, `VERSION.dll`, `CoCreateInstance`
   for DirectSound; stubs for `DPLAYX` and DDE that fail cleanly.
3. GDI: DIB sections, palettes and `TextOutA` onto the kit's DirectDraw
   primary; confirm the `IDirectDraw4` fallback and the surface methods
   the game uses.
4. Only then the hooks: replace the sentinels in `game.toml` with the frame
   clock and cursor addresses the listings name, and decide what the input
   hooks mean for a game without DirectInput.
