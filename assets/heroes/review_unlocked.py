"""The unlocked heroes' review sheet: Gamling on EA's unused detailed model with EA's own sword and
shield (SKGamling_SKN, assets/heroes/gamling_model.py) beside the model he drew before, close up, in
idle and attack and at the RTS camera; Damrod and Earnur as EA built them; with the portrait and
icon each now shows (Damrod's and Earnur's EA's own; Gamling's ours: EA left his commented out)."""
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
HEROES = {"Damrod": ("GUDamrod_SKN", "GUFaramir_SKL", "GUFaramir_IDLC", "GUFaramir_RUNA", "HPDamrodPortrait", "HIDamrodIcon"),
          "Earnur": ("GUIsildur_SKN", "GUAragorn_SKL", "GUAragorn_IDLA", "GUAragorn_RUNB", "HPEarnurPortrait", "HIEarnurIcon")}


def gamling_jobs():
    """Gamling, the model he drew before beside ours, at the same zoom."""
    import json
    from .gamling_model import EA_MODEL, GEAR, MODEL, OLD, SKELETON, folder
    d, src, work = folder()
    tex = json.loads((work / "textures.json").read_text())
    masks = {"rugamling_new.tga": tex.pop("hc_rugamling_new.tga")}
    blue = [R.ERE_BLUE, (0, 0, 0), (0, 0, 0)]
    old, new, skel = src / (OLD.lower() + ".w3d"), work / (MODEL.lower() + ".w3d"), src / (SKELETON.lower() + ".w3d")
    a = {k: src / ("guboromir_%s.w3d" % k) for k in ("idla", "atka", "runa")}
    showo, shown = ["RUROYALGUARD"], ["RUGAMLING_MESH", GEAR]
    J = R.job
    close = dict(part=["RUROYALGUARD"], dist=13.0, lift=6.8)
    closen = dict(part=["RUGAMLING_MESH"], dist=13.0, lift=6.8)
    return [J("G2_old_close", "GAMLING BEFORE (RUGamling_SKN)", old, skel, a["idla"], showo, tex, OUT, **R.close(**close)),
            J("G2_new_close", "GAMLING NOW (EA's RUGamlingCH_SKN + EA gear)", new, skel, a["idla"], shown, tex, OUT, masks, blue,
              **R.close(**closen)),
            J("G2_old_idle", "BEFORE: IDLE", old, skel, a["idla"], showo, tex, OUT, **R.full()),
            J("G2_new_idle", "NOW: IDLE", new, skel, a["idla"], shown, tex, OUT, masks, blue, **R.full()),
            J("G2_old_atk", "BEFORE: ATTACK", old, skel, a["atka"], showo, tex, OUT, frame=24, **R.full(azimuth=-40)),
            J("G2_new_atk", "NOW: ATTACK", new, skel, a["atka"], shown, tex, OUT, masks, blue, frame=24, **R.full(azimuth=-40)),
            J("G2_new_rts", "NOW: RTS CAMERA", new, skel, a["runa"], shown, tex, OUT, masks, blue, frame=8, **R.rts())]


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
    jobs += gamling_jobs()
    R.run(jobs, OUT)
    rows.append([j["out"] for j in jobs if j["name"].startswith("G2_")])
    for hero, (model, skel, idle, run, hp, hi) in HEROES.items():
        row = [str(OUT / ("%s_%s.png" % (hero, k))) for k in ("full", "close", "rts")]
        for img, size in ((hp, 192), (hi, 128)):
            path, ours = image_of(img, portraits.OUT)
            row.append(tile(path, "%s (%s)" % (img, "ours" if ours else "EA's"), size, OUT / ("t_%s.png" % img), mark=ours))
        rows.append(row)
    return R.sheet(rows, R.REVIEW / "heroes_unlocked.jpg",
                   "Unlocked for the Men: Gamling, Damrod, Earnur (EA's models; portraits and icons as shown in game)")
