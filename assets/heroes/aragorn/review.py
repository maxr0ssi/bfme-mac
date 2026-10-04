"""Aragorn's review sheet: EA's level-8 Aragorn (the Return-of-the-King costume 2.02 swaps in at
level 8) before and after our armour, close up, full length in two animations and at the RTS
camera, the enamel in a blue and a red player's colour."""
import json

from .. import render as R
from .design import ARMOUR, EA_MODEL, MASK, MODEL, PLATES, PLATES_MASK, SHEET, SKELETON, TRIM, folder

EA_MESHES = ["OBJECT03", "ARAGORN", "CLOAK", "ANDURIL", "SCABBARD"]


def review():
    d, src, work = folder()
    out = d / "renders"
    tex = json.loads((work / "textures.json").read_text())
    masks = {SHEET: str(work / MASK), PLATES: str(work / PLATES_MASK), "guaragorn_rotk.tga": str(src / "hc_guaragornrotk.tga")}
    ea, ours = src / (EA_MODEL.lower() + ".w3d"), work / (MODEL.lower() + ".w3d")
    skel = src / (SKELETON.lower() + ".w3d")
    idle, atk, run = (src / (a.lower() + ".w3d") for a in ("GUAragorn_IDLA", "GUAragorn_ATKD", "GUAragorn_RUNB"))
    after = EA_MESHES + [ARMOUR, TRIM]
    blue, red = [R.ERE_BLUE, (0, 0, 0), (0, 0, 0)], [R.RED, (0, 0, 0), (0, 0, 0)]
    J = R.job
    close = dict(part=["ARAGORN"], dist=17.0, lift=4.5)
    rows = [
        [J("before_close", "EA: LEVEL 8 (BEFORE)", ea, skel, idle, EA_MESHES, tex, out, masks, blue, **R.close(**close)),
         J("after_close", "OURS: LEVEL 8 (AFTER)", ours, skel, idle, after, tex, out, masks, blue, **R.close(**close)),
         J("after_close_red", "OURS, A RED PLAYER", ours, skel, idle, after, tex, out, masks, red, **R.close(azimuth=-35, **close))],
        [J("before_full", "BEFORE: IDLE", ea, skel, idle, EA_MESHES, tex, out, masks, blue, **R.full()),
         J("after_full", "AFTER: IDLE", ours, skel, idle, after, tex, out, masks, blue, **R.full()),
         J("before_atk", "BEFORE: ATTACK", ea, skel, atk, EA_MESHES, tex, out, masks, blue, frame=14, **R.full(azimuth=-40)),
         J("after_atk", "AFTER: ATTACK", ours, skel, atk, after, tex, out, masks, blue, frame=14, **R.full(azimuth=-40)),
         J("after_back", "AFTER: BACK", ours, skel, idle, after, tex, out, masks, blue, **R.full(azimuth=200))],
        [J("before_rts", "BEFORE: RTS CAMERA", ea, skel, run, EA_MESHES, tex, out, masks, blue, frame=8, **R.rts()),
         J("after_rts", "AFTER: RTS CAMERA", ours, skel, run, after, tex, out, masks, blue, frame=8, **R.rts()),
         J("after_rts_red", "AFTER: RED PLAYER", ours, skel, run, after, tex, out, masks, red, frame=8, **R.rts())],
    ]
    R.run([j for r in rows for j in r], out)
    return R.sheet([[j["out"] for j in r] for r in rows], R.REVIEW / "aragorn_level8.jpg",
                   "Aragorn at level 8: EA's Return-of-the-King costume, before and after the King's armour")
