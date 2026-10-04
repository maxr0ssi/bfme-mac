"""The Captain's review sheet: King Dain (EA) beside the Captain of Erebor, close up, full length in
two of Dain's animations and at the RTS camera, the cloth in Erebor blue and in a red player's colour."""
import json

from .. import render as R
from .design import ANIMS, MASKS, MODEL, SKELETON, folder
from .hero import DONOR_MODEL


def review():
    d, src, work = folder()
    out = d / "renders"
    tex = json.loads((work / "textures.json").read_text())
    masks = {k: str(work / v) for k, v in MASKS.items()}
    ea, ours = src / (DONOR_MODEL.lower() + ".w3d"), work / (MODEL.lower() + ".w3d")
    skel = src / (SKELETON.lower() + ".w3d")
    idle, atk, run = (src / (a.lower() + ".w3d") for a in ("DUDain_IDLB", "DUDain_ATKB", "DUDain_RUNA"))
    meshes = ["COAT", "BODY", "HEAD", "SHIELD", "HELMET", "REDAXE"]
    blue, red = [R.ERE_BLUE, (0, 0, 0), (0, 0, 0)], [R.RED, (0, 0, 0), (0, 0, 0)]
    J = R.job
    rows = [
        [J("ea_close", "EA: KING DAIN", ea, skel, idle, meshes, tex, out, **R.close()),
         J("our_close", "OURS: CAPTAIN OF EREBOR", ours, skel, idle, meshes, tex, out, masks, blue, **R.close()),
         J("our_close_red", "OURS, A RED PLAYER", ours, skel, idle, meshes, tex, out, masks, red, **R.close(azimuth=-30))],
        [J("ea_full", "EA: IDLE", ea, skel, idle, meshes, tex, out, **R.full()),
         J("our_full", "OURS: IDLE", ours, skel, idle, meshes, tex, out, masks, blue, **R.full()),
         J("ea_atk", "EA: ATTACK", ea, skel, atk, meshes, tex, out, frame=22, **R.full(azimuth=-40)),
         J("our_atk", "OURS: ATTACK", ours, skel, atk, meshes, tex, out, masks, blue, frame=22, **R.full(azimuth=-40)),
         J("our_back", "OURS: BACK", ours, skel, idle, meshes, tex, out, masks, blue, **R.full(azimuth=200))],
        [J("ea_rts", "EA: RTS CAMERA", ea, skel, run, meshes, tex, out, frame=10, **R.rts()),
         J("our_rts", "OURS: RTS CAMERA", ours, skel, run, meshes, tex, out, masks, blue, frame=10, **R.rts()),
         J("our_rts_red", "OURS: RED PLAYER", ours, skel, run, meshes, tex, out, masks, red, frame=10, **R.rts())],
    ]
    R.run([j for r in rows for j in r], out)
    return R.sheet([[j["out"] for j in r] for r in rows], R.REVIEW / "captain_of_erebor.jpg",
                   "Captain of Erebor: King Dain's rig with the Erebor kit (EA left, ours right)")
