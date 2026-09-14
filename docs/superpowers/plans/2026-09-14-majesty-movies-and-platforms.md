# Majesty Gold HD: Cinematics and All-Platform Builds Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Majesty Gold HD's intro and in-game cinematics play through the kit's FFmpeg Bink player on macOS and the iPad, and the game builds for every kit platform (macOS, iPad, Linux, Windows, Android) from this repository with the current kit main.

**Architecture:** The game repository holds config, tests, docs and smoke scripts; every runtime change goes into the kit on a `majesty` branch of the `kit/` submodule and is landed on kit `main` afterwards. The kit already decodes Bink through FFmpeg (`dx/bink.cpp`) for a game that opens loose `.bik` files by path and resolves eight Bink entry points. This game loads `BINKW32.DLL` at run time, resolves eleven entry points by name without null checks, and opens its movies from inside `Data/cinedata*.dat` archives by handing `BinkOpen` a Windows file HANDLE positioned at the movie with the `BINKFILEHANDLE` flag. The kit therefore gains: `BinkOpen` from a guest file handle at an offset (an FFmpeg custom I/O window over the host file), and the three missing exports `_BinkOpenDirectSound@4`, `_BinkGetRects@8`, `_BinkPause@8`. The platform builds are the kit's existing presets; this repository re-pins the kit, verifies each target and documents them.

**Tech Stack:** Python 3.9 tooling, the kit's translator and C/C++17 runtime under clang, SDL3, Metal on Apple, Vulkan elsewhere, FFmpeg 7.1.1 (LGPL, dynamically linked, Bink/Smacker decoders only), CMake presets `macos`, `ios`, `linux`, `windows`, `android` with Gradle and the NDK.

**Spec:** `docs/analysis.md` in this repository (import surface, run log) and the measured facts in "How the game drives Bink" below.

## Global Constraints

- Game repository: `~/Documents/Tests/majesty-recomp` (git `main`). Kit checkout used for landing: `~/Documents/Tests/recomp-kit` (`main` is `4ab4604`). The submodule `kit/` currently pins the old main `31f0f24`; Task 0.1 moves it to `4ab4604` on a new branch `majesty`.
- Kit code under `runtime/`, `dx/`, `host/`, `platform/` may not name a game; `kit/tests/test_game_literals.py` enforces the kit's list and the same rule applies to this game: write "the game" or "a Bink game", never "Majesty" or "Cyberlore" or "CYLB", in kit sources, tests and changelog.
- Every environment switch is `RECOMP_<NAME>` read through `recomp_env("<NAME>")`; no other prefix and no aliases.
- Addresses live in `game.toml` and `globals.toml`, never in kit code. A sentinel is replaced only by an address verified in the listings; `tests/test_game_config.py` keeps sentinels in `0x00725e00`-`0x00726000`.
- Native code builds only through `tools/build.py` and `tools/test.py`. Kit sources are formatted with `.venv/bin/python kit/tools/format.py --write`; before a kit commit run `.venv/bin/python kit/tools/check_game_literals.py` and, with the change staged, `.venv/bin/python kit/tools/check_repo.py`.
- Nothing generated, no game file, no run log and no save is committed. `original/`, `analysis/`, `build/` are ignored.
- Executable identity is fixed: `MajestyHD - Old.exe`, SHA-256 `654365fd1bdefa6d7f2349d162869f255388fadcb1bb8db9f7db2f3468dd5542`, image base `0x00400000`, entry `0x0064d96d`. Do not touch the Direct3D 9 executable.
- Kit-side native tests build against the kit's stub game, never this game's translation:

  ```bash
  .venv/bin/python kit/tools/test.py --game-dir /Users/sattam.thakur/Documents/Tests/majesty-recomp/kit/games/stub --compile-only
  .venv/bin/ctest --test-dir kit/build/cmake/macos -R "dx_tests|host_tests" --output-on-failure
  ```

  `dx/tests/dx_tests.cpp` uses `CHECK`, `CHECK_EQ`, `tramp("DLL.dll", "Name")`, `call_shim(t, {args})`, `sc(offset)` scratch addresses and a `tests[]` table in `main`. The stub route links FFmpeg on macOS (`RECOMP_VIDEO` defaults ON), so `dx_tests` can open real Bink data when a test is told where it is.
- Game-side checks: `.venv/bin/python -m pytest -q tests`, `.venv/bin/python tools/test.py`, `.venv/bin/python tools/build.py --stub`. The translation is regenerated with `.venv/bin/python tools/build.py --regenerate --jobs 8`; the smoke host is `.venv/bin/python tools/build.py --target smoke --jobs 8` producing `build/recomp/pop_smoke`; the macOS app is `.venv/bin/python tools/build.py --jobs 8`.
- Smoke runs use a fresh profile per run and never the developer's real profile: `RECOMP_PROFILE_DIR="$PWD/build/<run>/profile" RECOMP_SCRIPT="$PWD/smoke/<name>.script" RECOMP_HOST_DUMP_DIR="$PWD/build/<run>/dumps" RECOMP_DDRAW_MODES=640x480x8,640x480x16,800x600x16 RECOMP_SMOKE_DRAWABLE=800x600 build/recomp/pop_smoke > build/<run>/run.log 2>&1`. `RECOMP_LOG=2` logs every import call. Convert dumps with `.venv/bin/python kit/tools/recomp/ppm_to_png.py <in.ppm> <out.png>` and LOOK at them; a non-black dump is not a passing screen.
- iOS builds are run by the orchestrator only (Codex's shell configures the iOS target against the macOS SDK and fails). Codex verifies what it can on macOS and records that the iOS check is the orchestrator's.
- Commit messages: imperative subject, a body that says what changed and why. Kit commits go on branch `majesty` in `kit/`; game commits go on `main` of the game repository and re-pin the submodule. Never push.
- Minimum platforms (kit decision): iOS 17, Android 10 with Vulkan 1.1, macOS 14, current Linux and Windows releases SDL3 supports.

## How the game drives Bink (measured 2026-09-14)

From `analysis/decompiled/MajestyHD.exe/functions/` (the listing directory name is the launcher's; the functions are the pinned executable's):

- `FUN_00658eb0`: `LoadLibraryA("BINKW32.DLL")`, then `GetProcAddress` for `_BinkPause@8`, `_BinkDDSurfaceType@4`, `_BinkDoFrame@4`, `_BinkCopyToBuffer@28`, `_BinkGetRects@8`, `_BinkNextFrame@4`, `_BinkWait@4`, `_BinkClose@4`, `_BinkSetSoundSystem@8`, `_BinkOpenDirectSound@4`, `_BinkOpen@8` into `PTR_FUN_007db1e0..007db208`. No result is checked; a null pointer is called later. When the library is missing the game logs `Unable to find BINKW32.DLL` and skips movies. The kit at `4ab4604` registers `binkw32.dll` shims for games that import them statically, but `k_LoadLibraryA` answers only a fixed list of nine system modules (`runtime_serves_module` in `runtime/kernel32.cpp`), so the run-time load still fails (Task 0.1's run log: `LoadLibraryA("binkw32.dll"): no shims for that module`). Task 1.2 makes a module loadable when shims are registered under its name and serves all eleven entry points, since the game calls them without null checks.
- `FUN_006588f0`: `BinkSetSoundSystem(PTR_FUN_007db204 /* the OpenDirectSound entry itself */, 0)`; a non-zero return means sound.
- `FUN_00658670` (`CYBinkMovie` constructor): with a stream argument of kind 2 (or 4 wrapping 2) it calls `BinkOpen(handle, 0x00800000 /* BINKFILEHANDLE */)`, where `handle` is a Windows file HANDLE the game's archive reader positioned at the movie; otherwise `BinkOpen(path, 0)`. It keeps the record and reads `+0x00` width and `+0x04` height.
- `FUN_00658920` (a frame): `BinkDoFrame(rec)`; lock the target surface; `BinkCopyToBuffer(rec, lpSurface, pitch, height, x, y, BinkDDSurfaceType(surface))`; unlock; then `n = BinkGetRects(rec, 0)` and for each of the `n` rectangles at `rec + 0x34 + 16*i` (`x, y, w, h` ints) it blits that region to the screen. With `n == 0` nothing is shown. The Bink SDK record layout places `FrameRects[8]` at `+0x34` and `NumRects` at `+0xb4`; the kit's record is 0x100 bytes.
- `FUN_006584e0` / `FUN_00658750`: `BinkPause(rec, 1)` on focus loss, `BinkPause(rec, 0)` on resume and before `BinkClose(rec)`.
- The movies: `Data/cinedata2.dat` (CYLB archive, entries `MV02` at offset `0x78` and `MV04` at `0x21f800`, each a Bink stream after a 4-byte tag: `BIKh` at `0x7c`, 320x240, 180 frames; `BIKi` at `0x21f804`), `Data/cinedata3.dat` (`BIKf` at `0x7c`, `BIKx` at `0x18c247`, `BIKh` at `0x20abbc`), `DataMX/mx_cinedata2.dat` (`BIKh` at `0x44`). `MajXPrefs` in the profile has `IntroVideo` 1.

---

## Phase 0: the kit moves to main

### Task 0.1: Re-pin the kit submodule to main `4ab4604` on a `majesty` branch

**Files:**
- Modify: `kit` (submodule pin), `CHANGELOG.md`, `docs/analysis.md` (run log entry)

- [ ] **Step 1: Branch.** In `kit/`: `git remote add local /Users/sattam.thakur/Documents/Tests/recomp-kit` (skip if present), `git -c protocol.file.allow=always fetch local main`, `git checkout -B majesty local/main`; `git log --oneline -1` must show `4ab4604`.
- [ ] **Step 2: Config and portable checks.** `.venv/bin/python -m pytest -q tests`, `.venv/bin/python tools/test.py`, `.venv/bin/python tools/build.py --stub`. All exit 0. If a config test fails because the kit's `game_config` schema grew (a new required key), add the key to `game.toml` with a comment and record it; do not weaken the test.
- [ ] **Step 3: Regenerate and build.** `.venv/bin/python tools/build.py --regenerate --jobs 8` (the generated tree carries a copy of `runtime/x86.h`), then `--target smoke --jobs 8`, then the app `--jobs 8`. Record exit codes.
- [ ] **Step 4: Regression smoke.** Run `smoke/freestyle-beginner.script` as in the constraints into `build/repin/`. Expected on the OLD kit: a running Beginner Random quest at 800x600 in `quest-8s`/`quest-20s`. On the new kit the game finds `binkw32.dll` and, at its first movie, calls a null `_BinkOpenDirectSound@4`/`_BinkGetRects@8`/`_BinkPause@8` pointer: if `run.log` ends in a guest fault with a call to address 0 from `0x006588f0`, `0x00658920`, `0x006584e0` or `0x00658750`, record exactly that and the frames reached; it is Task 1.2's job and not a blocker for this task. If the run gets past the intro (it may, when the game's own `IntroVideo` path differs from the analysis), compare the three dumps with the description above and record any difference (the kit's `GetSystemMetrics` now follows the display mode and reverts to a 1024x768 desktop when the DirectDraw object is released; the game reads it for windowed placement).
- [ ] **Step 5: Commit** the game repository: re-pin, changelog line "Re-pin the kit to `majesty` `4ab4604`", the run log entry (commands, exit codes, what the smoke reached).

## Phase 1: the kit serves this game's Bink

### Task 1.1: `BinkOpen` from a guest file handle (`BINKFILEHANDLE`)

**Files:**
- Modify: `kit/runtime/kernel32.cpp`, `kit/runtime/win32.h` (a small query: given a guest HANDLE that is an open file, return its host path and current offset)
- Modify: `kit/dx/bink.cpp` (FFmpeg custom I/O over a window of a host file; `BinkOpen` flag handling)
- Test: `kit/dx/tests/dx_tests.cpp`
- Modify: `kit/CHANGELOG.md` (no kit document mentions Bink today; the changelog entry and the source comments are the record, and if `kit/README.md` lists the served DLLs, add the handle route in one line there)

**Interfaces:**
- Produces in `win32.h`: `bool win32_file_handle_position(uint32_t handle, std::string *host_path, int64_t *offset);` returning false for anything that is not an open `H_FILE`; `offset` is the handle's current position (`os_fd_seek(fd, 0, OS_SEEK_CUR)`), the guest's position is not moved.
- `BinkOpen(name, flags)`: `flags & 0x00800000` means `name` is a guest HANDLE. Resolve it with the query above; open the host path again read-only for the player (the guest keeps its own descriptor), and build an `AVIOContext` (`avio_alloc_context`, a 64 KiB buffer, `read_packet` and `seek` callbacks) whose byte 0 is `offset` and whose end is the host file's size (Bink knows its own length from its header; FFmpeg's Bink demuxer reads exactly the container's frames, so extra trailing data is harmless); `AVSEEK_SIZE` answers `size - offset`. Attach it as `input->pb` with `AVFMT_FLAG_CUSTOM_IO` before `avformat_open_input(&input, nullptr, nullptr, nullptr)`. `BinkPlayer` owns the context and frees its buffer and the file in its destructor. `flags & 0x04000000` (from memory) is refused with `BinkGetError` text "memory-resident video is not supported"; other flag bits are logged at the verbose level and ignored. The path route (`flags & 0x00800000 == 0`) is unchanged.
- Error texts stay readable through `BinkGetError`; a failed open returns 0 as today.

- [ ] **Step 1: Write the failing tests** in `dx_tests.cpp`: `test_bink_open_from_handle`. It reads `recomp_env("TEST_BINK_CONTAINER")` shaped `<host path>,<offset>`; when unset it prints `bink container test: RECOMP_TEST_BINK_CONTAINER unset, skipped` and returns. Otherwise: `win32_init` against the directory of that file so the guest can name it (`win32_guest_path(host)` gives the guest spelling), `CreateFileA` through the shim, `SetFilePointer` to the offset, `BinkOpen(handle, 0x00800000)`; CHECK the record is non-zero, `rd32(rec)` and `rd32(rec+4)` are between 16 and 4096, the frame count at `+0x10` is above 0 and the current frame at `+0x14` is 1; `BinkDoFrame`, `BinkNextFrame` twice; `BinkCopyToBuffer` into a guest buffer of pitch `width*2` with surface type 10 (RGB565) and CHECK the buffer is non-uniform; `BinkClose`; `SetFilePointer(handle, 0, 0, 1)` (query) still returns the offset the test set, proving the guest's position was not moved; `CloseHandle`. Also add `test_bink_handle_flag_errors`: `BinkOpen(0x12345678, 0x00800000)` returns 0 and `BinkGetError` is a non-empty string; `BinkOpen(sc(0), 0x04000000)` returns 0 with the memory-resident text. Register both in `tests[]`.
- [ ] **Step 2: Run them** through the stub route; the container test must fail (not skip) when run as `RECOMP_TEST_BINK_CONTAINER="/Users/sattam.thakur/Documents/Tests/majesty-recomp/original/gog/Data/cinedata2.dat,124" .venv/bin/ctest --test-dir kit/build/cmake/macos -R dx_tests --output-on-failure` before the implementation (the record is 0 because `name` is not a path). Record the failing output.
- [ ] **Step 3: Implement** as in Interfaces. Keep `BinkPlayer`'s single-owner cleanup; `avformat_close_input` with custom I/O does not free the `AVIOContext` buffer, so free `pb->buffer` with `av_freep` and the context with `avio_context_free` after closing the input.
- [ ] **Step 4: Verify**: the two tests pass with the container variable set (expected for offset 124: 320x240, 180 frames); `dx_tests` and `host_tests` pass without it (skip line printed); `format.py --write`, `check_game_literals.py`, `check_repo.py` (staged) exit 0.
- [ ] **Step 5: Commit** the kit on `majesty`: "bink: open a video from a guest file handle at its current offset". Do not re-pin yet.

### Task 1.2: `_BinkOpenDirectSound@4`, `_BinkGetRects@8`, `_BinkPause@8`

**Files:**
- Modify: `kit/dx/bink.cpp` (three shims in both the FFmpeg and the no-decoder build), `kit/CHANGELOG.md`
- Test: `kit/dx/tests/dx_tests.cpp`

**Interfaces:**
- `_BinkOpenDirectSound@4(lpDS)`: returns 1 (a non-zero sound-system token; the game passes the entry point's own address to `BinkSetSoundSystem`, which already returns 1).
- `_BinkGetRects@8(rec, flags)`: when the player holds a decoded frame (`have_frame`), write one rectangle `{0, 0, width, height}` at `rec + 0x34`, write 1 at `rec + 0xb4` and return 1; otherwise write 0 at `rec + 0xb4` and return 0. The no-decoder build returns 0.
- `_BinkPause@8(rec, pause)`: `pause != 0` freezes the clock: remember `host_millis()` in `paused_at`, set `paused = true`, and `BinkService` queues no more audio while paused; `pause == 0` on a paused player adds `host_millis() - paused_at` to `t0` and clears the flag. `BinkWait` returns 1 while paused (the game keeps looping without advancing). Returns 0. Unknown records are ignored.
- All three appear in `g_video_shims` under the `BINK(...)` macro with byte counts 4, 8, 8, so `GetProcAddress` resolves them.
- `runtime_serves_module(name)` in `kit/runtime/kernel32.cpp` (also modify `kit/runtime/imports.cpp`/`.h` if a query is missing): a module is served when it is in the fixed system list OR the imports registry holds at least one shim registered under that module name (case-insensitive; the registry keys are as the shim tables spell them, e.g. `binkw32.dll`, `DDRAW.dll`). Add `bool imports_serves_module(const char *dll)` beside `imports_resolve` if no such query exists. `LoadLibraryA("BINKW32.DLL")` then returns a pseudo module for any game, and `GetProcAddress` resolves through the same registry. The no-decoder build registers the finished-record stubs under the same names, so the game there plays each movie as already finished.

- [ ] **Step 1: Write the failing tests**: `test_bink_entry_points_resolve`: `LoadLibraryA("BINKW32.DLL")` through the kernel32 shim returns non-zero (this fails today: the module is not in the fixed list) and `GetProcAddress` returns non-zero for all eleven names listed in "How the game drives Bink" (the list belongs in the test as data, without the game's name). `test_bink_rects_and_pause`: on the no-frame record from the path route failure case use the container test's record when `RECOMP_TEST_BINK_CONTAINER` is set (GetRects before DoFrame returns 0 and `+0xb4` is 0; after DoFrame returns 1 with `{0,0,w,h}` at `+0x34`; Pause(1) then a 30 ms `os_sleep`-equivalent wait (use the kit's existing test sleep helper if one exists, else a busy loop on `host_millis`) then Pause(0): `BinkWait` returned 1 while paused and the frame due time moved by at least the paused span, checked through `BinkWait` returning 1 immediately after resume for frame 2 when it would have returned 0); without the variable the test checks only that `OpenDirectSound` returns 1, `GetRects(0, 0)` returns 0 and `Pause(0, 1)` returns 0. Register both.
- [ ] **Step 2: Run** (fail: the three names resolve to 0). **Step 3: Implement.** **Step 4: Verify** the suites, format, literals, repo check. **Step 5: Commit** the kit: "bink: the sound-system, rectangle and pause entry points".

### Task 1.3: The intro plays in the smoke host; the quest smoke skips it

**Files:**
- Modify: `kit` (re-pin to the Task 1.2 commit), `smoke/freestyle-beginner.script`
- Create: `smoke/intro.script`
- Modify: `docs/analysis.md` (run log), `docs/testing.md` (the `RECOMP_TEST_BINK_CONTAINER` value for this game), `README.md` (status paragraph: the intro plays; the "Bink is not served" sentence goes), `CHANGELOG.md`

- [ ] **Step 1: Re-pin** the submodule to the Task 1.2 commit (`git -C kit rev-parse HEAD`), regenerate (`--regenerate --jobs 8`), build the smoke host and the app.
- [ ] **Step 2: `smoke/intro.script`**: `wait 2000` / `dump intro-2s` / `wait 4000` / `dump intro-6s` / `wait 6000` / `dump intro-12s` / `key RETURN down` / `wait 100` / `key RETURN up` / `wait 3000` / `dump after-skip` / `key RETURN down` / `wait 100` / `key RETURN up` / `wait 5000` / `dump main-menu`. Run it into `build/intro/`. Expected: `run.log` has `bink: open` lines (the first 320x240, 180 frames), the three intro dumps are non-uniform and differ from each other, and `main-menu` shows the main menu (compare with the menu the freestyle script starts from). If a key does not end a movie, try `click left 400 300` instead and record which input the game accepts. Also run once as the headless host with `RECOMP_HOST_AUDIO_CAPTURE` (see the kit's headless host for the switch's file argument) and record that the capture is non-silent during the movie.
- [ ] **Step 3: `smoke/freestyle-beginner.script`**: prepend the skip(s) found in Step 2 before its first `wait 8000` so the script reaches the main menu as before; rerun it into `build/freestyle/` and LOOK at `quest-8s`, `quest-20s`, `quest-click`: a running quest at 800x600. This is also the regression check for the 30 kit commits since `31f0f24` (pointer confinement, tap timing, window-message posting, screen metrics); record any difference from the description in `docs/analysis.md`'s earlier freestyle record.
- [ ] **Step 4: The macOS app**: `.venv/bin/python tools/build.py --jobs 8`, launch `build/MajestyRecomp.app/Contents/MacOS/<exe>` with `RECOMP_HOST_DUMP_DIR="$PWD/build/app-intro/dumps" RECOMP_HOST_DUMP_EVERY=60` for 25 seconds (`perl -e 'alarm 25; exec @ARGV' ...`), convert the dumps and confirm movie frames then the menu. Record.
- [ ] **Step 5: Docs and commit** the game repository: run log entry with every command and result, `docs/testing.md` gains a row for `RECOMP_TEST_BINK_CONTAINER="$PWD/original/gog/Data/cinedata2.dat,124"` with the stub-route `dx_tests` command, README status updated, changelog. Commit: "The intro plays through FFmpeg; smoke scripts skip it".

**Measured in the first Step 2 run (2026-09-14):** the first movie is 640x480, 180 frames, from `cinedata3.dat`, and it fades in from black, so `intro-2s` being black is the movie, not a failure; judge the 6 s and 12 s dumps. The audio capture was silent because this game never calls `BinkService`: Task 1.4 fixes that in the kit first, then Step 2's audio check is repeated.

### Task 1.4: Bink audio starts and refills from the frame calls, not only `BinkService`

**Why:** real Bink feeds its sound output from a background thread; `BinkService` is an optional foreground helper. The kit's player only started and refilled audio inside `BinkService`, which the game measured in Task 1.3 never calls (its loop is `BinkDoFrame`, copy, `BinkGetRects`, blit, `BinkNextFrame`, `BinkWait`), so movies played silent.

**Files:**
- Modify: `kit/dx/bink.cpp` (factor the body of `BinkService` into `void service_audio(uint32_t rec, BinkPlayer &p)`; call it at the end of `BinkDoFrame` (after a frame is decoded), in `BinkNextFrame` and in `BinkWait`, and keep `BinkService` calling it; the paused guard from Task 1.2 stays in the shared routine), `kit/CHANGELOG.md`
- Test: `kit/dx/tests/dx_tests.cpp`

- [ ] **Step 1: Write the failing test** `test_bink_audio_without_service`, sharing the container fixture (skips without `RECOMP_TEST_BINK_CONTAINER`): open from the handle, call `BinkDoFrame` and `BinkNextFrame` three times with `BinkWait` in between and never `BinkService`; CHECK that the player's channel is a host audio stream with queued bytes (expose what the existing Task 10.2-era test used to check `host_audio_stream`/`host_audio_queued_bytes`, or read them through the same headers `dx_tests.cpp` already includes). Register it.
- [ ] **Step 2: Run** (fails: no channel). **Step 3: Implement.** **Step 4: Verify** `dx_tests` with and without the container variable, `host_tests`, format, literals, staged repo check. **Step 5: Commit** the kit on `majesty`: "bink: feed audio from the frame calls, not only BinkService".

### Task 1.5: A movie still open at process exit does not abort the host

**Measured (Task 1.3, `build/intro/headless/run.log`):** the headless host with a 20 s cap ended while the second movie was still open; after `guest process exited with code 0` the host died with `libc++abi: terminating due to uncaught exception of type std::system_error: mutex lock failed: Invalid argument` (exit 6). The open `BinkPlayer` objects live in a static map in `kit/dx/bink.cpp`; their destructors run at static destruction and call `host_audio_stop` / `dx_free_audio_channel` on host audio state that is already torn down. The smoke and headless hosts exited 0 before movies played, so this is the player's teardown order.

**Files:**
- Modify: `kit/dx/bink.cpp` (a `bink_shutdown()` that closes every open player while the host is still alive: free the FFmpeg state, stop the audio channel, forget the records), `kit/dx/dx.h` or wherever `bink_reset` is declared, and the host teardown sequence that already stops audio (find where `host_audio_shutdown` or the equivalent is called in `kit/host/` and call `bink_shutdown()` before it; grep `bink_reset` for the existing wiring pattern), `kit/CHANGELOG.md`
- Test: `kit/dx/tests/dx_tests.cpp`

- [ ] **Step 1: Write the failing test** `test_bink_shutdown_with_open_player` (container fixture; skips without it): open from the handle, decode one frame so audio starts, do NOT close, call `bink_shutdown()`; CHECK the record no longer resolves (a `BinkDoFrame` on it is a no-op returning 0 and `BinkClose` on it does not crash) and that a subsequent open still works. Register it.
- [ ] **Step 2: Run** (fails to link or fails). **Step 3: Implement** and wire the call into every host's teardown (smoke, headless, SDL app share a path; find it). **Step 4: Verify** the suites, format, literals, staged repo check, and re-run the headless intro capture from Task 1.3 Step 2 with the 20 s cap: exit 0 after the guest exit. **Step 5: Commit** the kit on `majesty`: "bink: close open players before host audio is torn down".

## Phase 2: every platform builds

### Task 2.1: Android APK

**Files:**
- Modify: `README.md` (an Android section mirroring `~/Documents/Tests/pharaoh-recomp/README.md`'s: prerequisites, `--target android`, `--push-game`, data path under external storage, `switches.txt`), `docs/analysis.md`, `CHANGELOG.md`

- [ ] **Step 1**: `.venv/bin/python tools/build.py --target android --stub` then `.venv/bin/python tools/build.py --target android` (the NDK is `~/Library/Android/sdk/ndk/27.2.12479018`, `JAVA_HOME` is Android Studio's JBR; the kit's build tool finds them as it does for the sibling game). Record the APK path and size; `unzip -l` must list `lib/arm64-v8a/libmain.so`, `libavcodec.so`, `libavformat.so`, `libavutil.so`. No device is attached: install and play stay unverified and the README says so.
- [ ] **Step 2**: docs and commit: "Android APK builds with FFmpeg; documented".

### Task 2.2: Linux and Windows packages, CI, platform status table

**Files:**
- Modify: `README.md` (a platform status table like the sibling's with rows macOS, iPadOS, Linux, Windows, Android: verified status, build command, remaining checks; Linux/Windows sections with `tools/build.py --regenerate --jobs 8` and the kit's `package_desktop.py` output under `build/package`, `RECOMP_EXE`; both marked never run on hardware), `.github/workflows/checks.yml` (drop the `KIT_TOKEN` checkout token and the "private submodule" comment: the kit is public; add `windows-2025` to the matrix for the portable tests and the stub build exactly as `~/Documents/Tests/pharaoh-recomp/.github/workflows/*.yml` does), `docs/analysis.md`, `CHANGELOG.md`

- [ ] **Step 1**: On macOS, run the kit's packager tests `.venv/bin/python -m pytest -q kit/tools/tests/test_package_desktop.py` and `.venv/bin/python tools/test.py`; record. The Linux and Windows native builds cannot run here; the README's rows say "never built or run on Linux/Windows; packager tests use fake binaries on macOS".
- [ ] **Step 2**: README table and sections, CI change, docs, commit: "Platform status, Linux/Windows packaging notes and Windows CI".

### Task 2.3 (orchestrator): iPad build, install, intro on the device (done 2026-09-14: movies play with sound on the device, see docs/analysis.md)

Not a Codex task. From the orchestrator's shell: `.venv/bin/python tools/build.py --target ios --team BDFW2Z27HA --device 15A75531-8976-580D-AF09-5DAA939FDF32 --no-install`, `xcrun devicectl device install app --device ... build/ios/Release/MajestyRecomp.app` (path from the build output), launch with `--console` for 60 s; expect `bink: open` lines and movie frames in pulled dumps. Record in `docs/analysis.md` and the README's iPad row.

### Task 2.4 (orchestrator): land the kit on main, re-pin, push (done 2026-09-14: kit main 4574a35, both game repositories re-pinned and pushed)

`git -c protocol.file.allow=always pull --ff-only /Users/sattam.thakur/Documents/Tests/majesty-recomp/kit majesty` in `~/Documents/Tests/recomp-kit`, `git push origin main`; re-pin the submodule to `local/main`; push the game repository. Then re-pin `pharaoh-recomp` to the same kit main and check its `dx_tests` and boot smoke still pass.
