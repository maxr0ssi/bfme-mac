#!/bin/zsh
# scripts/window-watch.sh <game pid> [log] — log the game window's real macOS frame next to Wine's.
# The play scripts start it in the background. ahk/edgescroll.ahk logs the window rect Wine believes
# in; this logs the frame the window server actually has (CGWindowList, no permission needed), its
# layer (Wine raises a full-screen window above the menu bar), and the screen's menu-bar and notch
# heights, into the same file (default ahk/edgescroll.log), tagged "mac", once at start and on every
# change. Read-only; polls once a second; exits when the game's window has been gone for 10 s, or
# after 15 minutes if it never appears.
set -eu
BFME_ROOT="${0:A:h:h}"
[[ "${1:-}" == <-> ]] || { echo "usage: window-watch.sh <game pid> [log]"; exit 2; }
log="${2:-$BFME_ROOT/ahk/edgescroll.log}"
exec osascript -l JavaScript - "$1" 2>>"$log" <<'JS'
ObjC.import('AppKit'); ObjC.import('CoreGraphics');
function run(argv) {
  var pid = parseInt(argv[0], 10), last = '', seen = false, gone = 0, waited = 0;
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function log(msg) { var d = new Date(); console.log(pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds()) + ' mac: ' + msg); }
  function rect(x, y, w, h, s) { return Math.round(x * s) + ',' + Math.round(y * s) + ' ' + Math.round(w * s) + 'x' + Math.round(h * s); }
  while (true) {
    var scr = $.NSScreen.screens.objectAtIndex(0), f = scr.frame, v = scr.visibleFrame, s = scr.backingScaleFactor;
    var top = 0; try { top = scr.safeAreaInsets.top; } catch (e) {}
    var list = ObjC.deepUnwrap(ObjC.castRefToObject($.CGWindowListCopyWindowInfo($.kCGWindowListOptionAll | $.kCGWindowListExcludeDesktopElements, 0))) || [];
    var game = null, menubar = 0;
    list.forEach(function (w) {
      var b = w.kCGWindowBounds || {};
      if (w.kCGWindowOwnerName === 'Window Server' && w.kCGWindowName === 'Menubar') menubar = b.Height;
      // by pid (the play script execs wine), title, or a Wine owner name; the largest wins
      var mine = w.kCGWindowOwnerPID === pid || String(w.kCGWindowName || '').indexOf('The Lord of the Rings') >= 0
        || /wine|lotrbfme/i.test(String(w.kCGWindowOwnerName || ''));
      var score = b.Width * b.Height + (w.kCGWindowIsOnscreen ? 1e9 : 0);   // on screen first
      if (mine && (!game || score > game.score)) game = { b: b, w: w, score: score };
    });
    var line = 'screen ' + rect(0, 0, f.size.width, f.size.height, s) + ' px (x' + s + '), menu bar ' + Math.round(menubar * s)
      + ' px, notch ' + Math.round(top * s) + ' px, usable ' + rect(0, f.size.height - v.origin.y - v.size.height, v.size.width, v.size.height, s) + '; ';
    if (game) {
      var b = game.b;
      line += 'game window ' + rect(b.X, b.Y, b.Width, b.Height, s) + ' px, layer ' + game.w.kCGWindowLayer + (game.w.kCGWindowIsOnscreen ? '' : ', off screen');
      seen = true; gone = 0;
    } else {
      line += 'no game window';
      if (seen && ++gone >= 10) { log('game window gone, stopping'); return; }
      if (!seen && ++waited >= 900) { log('no game window after 15 min, stopping'); return; }
    }
    if (line !== last) { log(line); last = line; }
    delay(1);
  }
}
JS
