# Playing on your Mac

Launching, settings and known issues. Setting up is in the [README](../README.md#setup); playing
with others is in [MULTIPLAYER.md](../MULTIPLAYER.md). Every script and tool is listed in
[REFERENCE.md](REFERENCE.md).

## Launch

| Game | Command |
|---|---|
| BFME2 (1.06) | `scripts/play-bfme2.sh` |
| Rise of the Witch-king (2.02, HD Edition optional) | `scripts/play-rotwk.sh` |

Or use the apps in /Applications (`scripts/make-apps.sh`; the installer makes them). On first
launch macOS asks whether the app may access your Documents folder; allow it once per app.

Both games run on the Wine 10.0 engine in `engines/w10`. They start borderless full-screen
(windowed underneath, so Cmd-Tab and screen sharing work), with screen-edge scrolling emulated
by `ahk/edgescroll.ahk`. `Esc` skips the intro. A skirmish loads in about 12 s. Logs go to `logs/`
(`logs/gamepatch.log` for the game patch). If nothing happens, read the newest
`logs/rotwk-*.log` or `logs/bfme2-*.log`; if the game folder is missing, run `scripts/install.sh`.

Before playing, set System Settings → Battery → Energy Mode to High Power. Low Power Mode visibly
hurts frame pacing.

## Keys

- **Ctrl+Alt+E** (Control+Option+E): edge scrolling on/off. A tooltip confirms. While the cursor
  is within 4 points of the window edge, the matching arrow key is held; nothing happens while a
  mouse button is down, so right-drag rotation works as usual. `EDGESCROLL=off scripts/play-rotwk.sh`
  starts with it off. The play scripts pass the margin, 4, as the second argument to
  `edgescroll.ahk`, which overrides the `margin :=` line in the script; for a wider margin change
  that `4` in `scripts/play-rotwk.sh` (or `play-bfme2.sh`). If the arrow keys don't reach the
  game, try `EDGESCROLL_SEND=event` (or `play`).
- **Ctrl+Alt+R**: gets the mouse back after Cmd-Tab (below).

## Settings

- **Resolution.** The installer sets `Resolution` in `Options.ini` to your display's size in points.
  `scripts/retina.sh on` switches Wine's Retina mode on and doubles it (e.g. `3024 1964` on a 14"
  MacBook Pro), rendering every physical pixel: sharper, smaller text, little GPU cost.
  `scripts/retina.sh off` goes back. `Resolution` must be a mode the display offers.
- **Detail.** The installer sets UltraHigh, the setting the performance numbers were measured at
  ([PERFORMANCE.md](PERFORMANCE.md) lists the exceptions for its first runs).
- **Frame rate.** The engine runs at 30 FPS, tied to the simulation. Unlocking it speeds the game
  up; don't.
- **Mouse wheel zoom** needs `UsePreciseScrolling = n` for Wine's Mac driver (the installer sets it).
- **Game patch switches** are in `gamepatch.ini` in the RotWK folder,
  `prefixes/w10/drive_c/Program Files (x86)/Electronic Arts/RotWK/` (1 = on). `GAMEPATCH=0` in the
  environment turns every patch off for one launch.
- **Mods** go in with `scripts/install-mod.sh <bfme2|rotwk> <folder|zip>`, which backs up what it
  replaces (`--revert` undoes it). Anything that changes INI files must be identical for everyone in
  a multiplayer game.

## New buildings

The redesigned buildings for Dwarves, Elves, Men (Arnor uses Men's) and Goblins, and the
Dwarven and Elven builders, are optional. `scripts/install.sh --buildings` installs them all,
`--buildings dwarves,elves` some; the installer asks otherwise (default no). The download holds only
our changes, none of EA's files: the installer rebuilds the buildings from your own game. So they
need RotWK 2.02: the installer checks your game first and skips a faction whose files differ from
the ones the packs were built against.
`scripts/install.sh --no-buildings` takes them out and restores `asset.dat`. Everyone in a LAN game
must make the same choice ([MULTIPLAYER.md](../MULTIPLAYER.md#art-packs)). They are not yet checked
in a full game.

## Known issues

- **Mouse after Cmd-Tab.** Switching away and back can leave the 3D view ignoring the mouse and
  keyboard (Sikarugir issue #237). Press **Ctrl+Alt+R**; if that doesn't help, save and relaunch.
  To have it run on every switch back, set `recaptureOnActivate := true` at the top of
  `ahk/edgescroll.ahk`. Both are unverified in play. The cause is in Wine 10's Mac driver, which does
  not restore focus and cursor clipping on reactivation. Wine 11 fixes that, but Wine 11 crashes both
  games (a WoW64 bug, `patches/WINE-BUG-REPORT.md`), and there is no registry setting for it.
- **Picture shifted down, clicks off.** macOS sometimes moves the borderless window below the
  menu bar a few seconds after launch (seen 2026-09-29: 0,66 3024x1898 instead of 0,0 3024x1964). The
  game still draws its full resolution, squeezed into the shorter window under a black strip, so
  clicks miss by up to a menu bar's height. `ahk/edgescroll.ahk` now puts the window back whenever
  it moves (a `re-pin` line in `ahk/edgescroll.log`); Ctrl+Alt+R does it too. `mac` lines in the same
  log show where macOS really has the window. Set `keepPinned := false` at the top of the script to
  turn it off.
- **Cursor turns into the Mac arrow, or the game drops away.** Not Wine, the game or AutoHotkey
  (2026-10-04, `scripts/cursor-test.sh` and the logs: every RotWK cursor converts, the game
  always sets its own, and every focus loss in that session was a Cmd-Tab). macOS does it: a
  quick shake of the mouse swaps any cursor for a big arrow (System Settings → Accessibility →
  Display → Pointer → *Shake mouse pointer to locate*), and a hot corner opens over the game
  (Desktop & Dock → Hot Corners; bottom right is Quick Note by default, and edge scrolling
  takes the pointer into corners). macOS 26 also logs `Cursor disabled: failed
  set_cursor_surface` about five times a minute while the game has focus. Turning the two
  settings off is your choice; the scripts don't change them.
- **No exclusive full-screen.** Under Wine's Mac driver it minimises and turns black on focus loss;
  the borderless window is the replacement.
- **30 FPS ceiling** (engine design), and big battles still drop below it
  ([PERFORMANCE.md](PERFORMANCE.md)).
- **Edge scrolling "did nothing"?** `ahk/edgescroll.log` records window geometry, focus and every
  key press.

## Don't change

- The `LARGEADDRESSAWARE` (4 GB) flag: on for RotWK and off for BFME2, as each ships. The
  installer sets it; `tools/pe_laa.py` changes it ([MEMORY-4GB.md](MEMORY-4GB.md)).
- The prefix's Windows version: the installer sets Windows 10, and Windows XP crashes wined3d at
  startup.
