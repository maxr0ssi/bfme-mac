"""The unlocked heroes' review sheet: Gamling, Damrod and Earnur as EA built them (their models are
EA's, unchanged), close up and at the RTS camera, with the portrait and icon each now shows
(Damrod's and Earnur's EA's own; Gamling's ours: EA left his commented out)."""
import subprocess
from pathlib import Path

from sagekit import paths
from sagekit.formats.textures import sheet_member
from sagekit.game import Install

from . import portraits
from . import render as R
from .review_roster import image_of, tile

OUT = Path(paths.BUILD) / "heroes" / "unlocked"
# hero: (model, skeleton, idle, run, portrait, icon, house mask of its sheet or None)
HEROES = {"Gamling": ("RUGamling_SKN", "GUBoromir_SKL", "GUBoromir_IDLA", "GUBoromir_RUNA", "HPGamling", "HIGamling"),
          "Damrod": ("GUDamrod_SKN", "GUFaramir_SKL", "GUFaramir_IDLC", "GUFaramir_RUNA", "HPDamrodPortrait", "HIDamrodIcon"),
          "Earnur": ("GUIsildur_SKN", "GUAragorn_SKL", "GUAragorn_IDLA", "GUAragorn_RUNB", "HPEarnurPortrait", "HIEarnurIcon")}


def review():
    from sagekit.formats.w3d import W3DFile
    g = Install()
    OUT.mkdir(parents=True, exist_ok=True)
    jobs, rows = [], []
    for hero, (model, skel, idle, run, hp, hi) in HEROES.items():
        files = {}
        for n in (model, skel, idle, run):
            try:
                data = g.read(g.model_path(n))
            except FileNotFoundError:
                continue
            files[n] = OUT / (n.lower() + ".w3d")
            files[n].write_bytes(data)
        w = W3DFile(str(files[model]))
        tex = {}
        for t in {t.lower() for m in w.meshes.values() for t in m.textures}:
            m = sheet_member(g, t)
            if m:
                p = OUT / m.split("\\")[-1]
                p.write_bytes(g.read(m))
                tex[t] = str(p)
        show = list(w.meshes)
        run_anim = files.get(run, files[idle])
        J = R.job
        jobs += [J("%s_full" % hero, "%s: EA'S MODEL" % hero.upper(), files[model], files[skel], files[idle], show, tex, OUT, **R.full()),
                 J("%s_close" % hero, "%s: CLOSE UP" % hero.upper(), files[model], files[skel], files[idle], show, tex, OUT,
                   **R.close(part=show[:1], dist=15.0, lift=6.5)),
                 J("%s_rts" % hero, "%s: RTS CAMERA" % hero.upper(), files[model], files[skel], run_anim, show, tex, OUT,
                   frame=8, **R.rts())]
    R.run(jobs, OUT)
    for hero, (model, skel, idle, run, hp, hi) in HEROES.items():
        row = [str(OUT / ("%s_%s.png" % (hero, k))) for k in ("full", "close", "rts")]
        for img, size in ((hp, 192), (hi, 128)):
            path, ours = image_of(img, portraits.OUT)
            row.append(tile(path, "%s (%s)" % (img, "ours" if ours else "EA's"), size, OUT / ("t_%s.png" % img), mark=ours))
        rows.append(row)
    return R.sheet(rows, R.REVIEW / "heroes_unlocked.jpg",
                   "Unlocked for the Men: Gamling, Damrod, Earnur (EA's models; portraits and icons as shown in game)")
