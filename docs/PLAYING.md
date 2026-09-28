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
(`logs/gamepatch.log` for the game patch).

Before playing, set System Settings → Battery → Energy Mode to High Power. Low Power Mode visibly
hurts frame pacing.

## Keys

- **Ctrl+Alt+E** (Control+Option+E): edge scrolling on/off. A tooltip confirms. While the cursor
  is within 4 points of the window edge, the matching arrow key is held; nothing happens while a
  mouse button is down, so right-drag rotation works as usual. For a wider margin, pass it to the
  script (`edgescroll.ahk 8`) or edit `margin` at its top.
- **Ctrl+Alt+R**: gets the mouse back after Cmd-Tab (below).

## Settings

- **Resolution.** The installer sets `Resolution` in `Options.ini` to your display's size in points.
  `scripts/retina.sh on` switches Wine's Retina mode on and doubles it (e.g. `3024 1964` on a 14"
  MacBook Pro), rendering every physical pixel: sharper, smaller text, little GPU cost.
  `scripts/retina.sh off` goes back. `Resolution` must be a mode the display offers.
- **Detail.** The installer sets UltraHigh, which is what the performance numbers were measured
  at.
- **Frame rate.** The engine runs at 30 FPS, tied to the simulation. Unlocking it speeds the game
  up; don't.
- **Mouse wheel zoom** needs `UsePreciseScrolling = n` for Wine's Mac driver (the installer sets it).
- **Game patch switches** are in `gamepatch.ini` in the RotWK folder (1 = on). `GAMEPATCH=0` in the
  environment turns every patch off for one launch.
- **Mods** go in with `scripts/install-mod.sh <bfme2|rotwk> <folder|zip>`, which backs up what it
  replaces (`--revert` undoes it). Anything that changes INI files must be identical for everyone in
  a multiplayer game.

## Known issues

- **Mouse after Cmd-Tab.** Switching away and back can leave the 3D view ignoring the mouse and
  keyboard (Sikarugir issue #237). Press **Ctrl+Alt+R**; if that doesn't help, save and relaunch.
  To have it run on every switch back, set `recaptureOnActivate := true` at the top of
  `ahk/edgescroll.ahk`. Both are unverified in play. The cause is in Wine 10's Mac driver, which does
  not restore focus and cursor clipping on reactivation; Wine 11 fixes it, but Wine 11 crashes these
  games at match start (`patches/WINE-BUG-REPORT.md`), and there is no registry setting for it.
- **No exclusive full-screen.** Under Wine's Mac driver it minimises and turns black on focus loss;
  the borderless window is the replacement.
- **30 FPS ceiling** (engine design), and big battles still drop below it
  ([PERFORMANCE.md](PERFORMANCE.md)).
- **Edge scrolling "did nothing"?** `ahk/edgescroll.log` records window geometry, focus and every
  key press.

## Don't change

- The `LARGEADDRESSAWARE` (4 GB) flag: on for RotWK, as RotWK 2.02 ships it (the installer keeps it;
  the crash once blamed on it was Wine 11's, [MEMORY-4GB.md](MEMORY-4GB.md)); off for BFME2, as
  retail ships it. `tools/pe_laa.py --off` reverts.
- Keep the prefix at Windows 10 (`winecfg -v win10`); Windows XP crashes wined3d at startup.
