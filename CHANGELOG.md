# Changelog

## Unreleased

- Re-pin the kit to `main` `ac86bba`, which teaches main's recovery an MSVC
  7.1 image. This game is MSVC too, and the pin moves its translation
  forward: `--regenerate` used to raise on the Delphi SEH classifier ("SEH
  stub 0064c94c is not a JMP rel32 to code") at both `0b4fa9a` and `dd31356`,
  and now gets past every frame site to a single remaining literal dispatch
  target, `fn_0061e4c0`'s `JMP 0xe613ea57`. The app still builds from the
  generated sources already in `build/recomp/gen/`.
- Re-pin the kit to `main` `dd31356` (the touch controls: JSON layouts, an
  on-screen pad, physical controllers, phone layouts and a layout editor) and
  give this game its `[controls]` mapping. The sticks and d-pad pan on held
  arrow keys and steer the pointer at 700 points per second; Cross and Circle
  are the only two mouse buttons the game polls; Square is Return, Triangle
  the system keyboard, L1/R1 the Control and Shift modifiers it reads, Start
  Escape and Select the kit's settings page. The triggers and stick clicks
  stay unmapped because this game handles no mouse wheel and no middle
  button. Both halves show by default (`pad+keys`), since the UI's letter
  accelerators live in the `UIData` records rather than in code. No repo
  layout ships; the built-in pad fits. The pad is unplayed on a device at
  this pin. `[settings] rows` takes the new `controls` spelling.
- iPad: the logo, intro and expansion movies play with sound on the device
  with kit `4574a35`; the README's iPadOS row and the run log record the
  console evidence.
- Add a platform status table and Linux/Windows build, package and
  `RECOMP_EXE` launch notes. Both desktop ports remain never built or run
  on their target OS; packager tests use fake binaries on macOS. Record the
  iPad build with the new kit and device installation/playback pending the
  orchestrator. Add `windows-2025` portable tests and stub build CI, and
  remove the checkout token requirement now that the kit is public.
- Android stub and translated APK builds verified with FFmpeg at kit
  `4574a35`. Document the Android toolchain, build and data-push commands,
  external game/profile paths and `switches.txt`. Installation and gameplay
  remain unverified because no Android device was attached.
- Intro movies play through FFmpeg on macOS, with non-silent audio verified
  in the headless host. Re-pin the kit to `majesty` `4574a35` for Bink
  file-handle input, dynamic imports, frame-driven audio and safe teardown.
  Add `smoke/intro.script`; the freestyle smoke skips both movies with
  Return and settles for 9 seconds before Beginner Random. Its fresh-profile
  regression passed all 14 steps; the intermittent game exception remains
  open. Document the private Bink container test and macOS movie/menu dumps.
- Re-pin the kit to `majesty` `4ab4604`.
- The game plays on the iPad by touch and with a Bluetooth mouse: taps take
  the menus into a quest and select buildings there, a finger held against
  the top edge or a mouse pushed against the top scrolls the map, Exit Game
  closes the app. Kit: the touch mapper's release waits for presented
  frames and carries the press position (it carried 0,0 after a vector
  reallocation, which failed every tap and flung the view to the map's
  top-left), the edge snap grows by iPadOS's status bar strip, a hardware
  pointer against that strip is held on the edge through the glide iPadOS
  gives it. `RECOMP_*` switches reach the device through
  `Documents/switches.txt`. Run log: "playing on the iPad by hand".
- The iPad app builds, signs, installs and boots to the main menu with music
  (`tools/build.py --target ios`); the game is seeded from the bundle into the
  app's Documents on first launch.
- The `[hooks]` sentinels in `game.toml` are annotated with why this game has
  no site for each kit hook. The main menu's Version label fills in from the
  executable's version resource, and the game's log stops reporting a failed
  DirectShow filter enumeration.
- Saves, preferences, the registry and the game's log live in the profile
  (`build/recomp/profile`, the app's user data directory in a bundle), never
  in the game's installation. Save Game and Load Game work from the in-game
  Options dialog. Kit: the overlay is installed before anything game-specific
  can fail, and a file opened for writing reaches the write tier only when a
  byte is written, so the game's archives are no longer copied per profile.
- Music: the MP3 tracks play through the kit's new DirectShow streaming shims
  (`dx/dshow.cpp` on the `majesty-translator` branch, decoded with minimp3).
  Verified in the headless host with an audio capture; the smoke host cannot
  continue a sound and restarts the stream at every refill.
- A Beginner Random freestyle quest loads and runs under the kit's smoke host;
  `smoke/freestyle-beginner.script` drives it from the main menu. The
  submodule moves along the `majesty-translator` branch for the input shims,
  translator fixes and throw diagnostics this took.
- The game boots to its main menu on macOS (800x600, 16 bpp, through the
  recompiled DirectDraw path) and exits cleanly. The kit submodule moves to
  the `majesty-translator` branch (58d32c2), which carries the translator,
  runtime and GDI work this needed; docs/analysis.md's run log records it.
- New game repository for Majesty Gold HD (GOG offline installer 1.5.2.28)
  in the shape of populous-recomp: the kit as the submodule `kit/`,
  `game.toml` and `globals.toml`, thin `tools/*.py` wrappers, config tests
  and CI.
- The pinned executable is the installer's DirectDraw build,
  `MajestyHD - Old.exe` (Majesty HD 1.5.1.2, SHA-256 `654365fd…d5542`),
  because the kit models DirectDraw; the launcher's default `MajestyHD.exe`
  (1.5.2.28) is Direct3D 9 on the Visual C++ 2008 runtime DLLs and is
  recorded as blocked in `docs/analysis.md`.
- `game.toml` carries the measured identity of the executable (image base
  `0x00400000`, entry point `0x0064d96d`, guest root, required data
  directories, iOS bundle exclusions). The Populous-shaped hooks and globals
  the kit compiles against are sentinels in the executable's unused section
  padding until the bring-up identifies them; `tests/test_game_config.py`
  enforces that and that the exclusion list keeps the pinned executable.
- `tools/analyze.py`: listing export with Ghidra's own analyzers, because the
  kit's setup expects a curated annotation set this game does not have.
- `docs/analysis.md`: the executable's import surface (258 imports, 155 of
  them shimmed by the kit), its DirectDraw, GDI, DirectSound and Bink paths,
  the kit work each needs, and the run log of the pipeline against it.
