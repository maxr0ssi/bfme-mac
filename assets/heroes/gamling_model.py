#!/usr/bin/env python3
"""Gamling's model: EA's unused, more detailed RUGamlingCH_SKN (929 vertices, RUGamling_new.tga with
EA's own house-colour mask) on the skeleton his Draw already animates (GUBoromir_SKL), armed with
EA's own Rohan sword and round shield taken from the model he draws today (RUGamling_SKN: its
triangles on B_SWORDBONE and B_SHIELD, with their UVs and sheet), as SKGamling_SKN.

EA's CH mesh stays byte for byte; the gear is one new sub-object, SKGAM_GEAR, on the same bones as
in EA's model, so it sits in the hand and on the arm in every one of Boromir's animations.

    python3 -m assets.heroes.gamling_model
"""
import json
from pathlib import Path

from sagekit import paths
from sagekit.formats import w3dpose as P
from sagekit.formats.textures import sheet_member
from sagekit.formats.w3d import W3DFile
from sagekit.game import Install

from . import gear as G

OLD, EA_MODEL, MODEL, SKELETON = "RUGamling_SKN", "RUGamlingCH_SKN", "SKGamling_SKN", "GUBoromir_SKL"
GEAR = "SKGAM_GEAR"
ANIMS = ("GUBoromir_IDLA", "GUBoromir_ATKA", "GUBoromir_ATKB", "GUBoromir_RUNA", "GUBoromir_HRNB")
CHECK_ANIM = "GUBoromir_ATKA"
GEAR_BONES = ({"B_SWORDBONE"}, {"B_SHIELD"})


def folder():
    d = Path(paths.BUILD) / "heroes" / "gamling"
    return d, d / "src", d / "work"


def build():
    d, src, work = folder()
    src.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    g, got = Install(), {}
    for name in (OLD, EA_MODEL, SKELETON) + ANIMS:
        data = g.read(g.model_path(name))
        (src / (name.lower() + ".w3d")).write_bytes(data)
        got[name.lower()] = G.sha(data)
    tex = {}
    for t in ("rugambling.tga", "rugamling_new.tga", "hc_rugamling_new.tga"):
        m = sheet_member(g, t)
        p = src / m.split("\\")[-1]
        p.write_bytes(g.read(m))
        tex[t] = str(p)
    sk = P.Skeleton((src / (SKELETON.lower() + ".w3d")).read_bytes())
    old = W3DFile((src / (OLD.lower() + ".w3d")).read_bytes())
    ea_bytes = (src / (EA_MODEL.lower() + ".w3d")).read_bytes()

    def draw(m):
        for bones in GEAR_BONES:
            G.surface_plate(m, old, sk, "RUROYALGUARD", lambda c, b, bones=bones: b <= bones, None, 0.0)
    draw.__name__ = "rohan_gear"
    gear = G.draw(old.meshes["RUROYALGUARD"], sk, draw, "RUGambling.tga", "RUGambling.tga")
    built = G.assemble(ea_bytes, EA_MODEL, MODEL, "RUGAMLINGCH_SKN", extra=[(GEAR, G.chunk_of(gear, GEAR))])
    out = work / (MODEL.lower() + ".w3d")
    out.write_bytes(built)
    report = G.check(ea_bytes, built, EA_MODEL, MODEL, sk, P.Animation((src / (CHECK_ANIM.lower() + ".w3d")).read_bytes()),
                     added=[GEAR], sheets=["RUGambling.tga"], wrapped=[GEAR])
    report.update(sources=got, gear_vertices=len(gear.verts))
    (d / "report.json").write_text(json.dumps(report, indent=1) + "\n")
    (work / "textures.json").write_text(json.dumps(tex, indent=1))
    print("PASS gamling: %s; EA's RUGAMLING_MESH byte for byte, %s added (EA's sword and shield, %d vertices); drift %.1e"
          % (out.name, GEAR, len(gear.verts), report["max_bone_drift"]))
    return report


def members():
    d, src, work = folder()
    return {"art\\w3d\\%s\\%s.w3d" % (MODEL.lower()[:2], MODEL.lower()): work / (MODEL.lower() + ".w3d")}


if __name__ == "__main__":
    build()
