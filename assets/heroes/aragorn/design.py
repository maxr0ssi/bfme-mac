#!/usr/bin/env python3
"""Aragorn's level-8 armour: EA's GUAragorn_SKN as SKAragorn_SKN with two new sub-objects,
SKAR_KINGSARM and SKAR_KINGTRIM, hidden until level 8 (a SubObjectsUpgrade on EA's
Upgrade_ObjectLevel8, which Aragorn's MP level 8 already grants and 2.02 already uses to put him in
his Return-of-the-King costume: guaragorn_rotk.tga).

The King's plates follow EA's own surface: EA's triangles over the shoulders, chest and forearms,
lifted off the body along EA's normals and drawn with EA's Return-of-the-King sheet burnished
(EA's detail kept: the black tabard and its White Tree become a lacquered breastplate), each plate
rimmed in fine gold from the CaH Men's sheet (assets/cah/men_cg/paint.py, painted again under our
name). The lift and the rims change his outline a little at the RTS camera. Every EA mesh stays
EA's byte for byte; the plates take the player's colour where EA's sheet does (EA's mask, our name).

    python3 -m assets.heroes.aragorn.design
"""
import json
import math
from pathlib import Path

from sagekit import paths
from sagekit.formats import w3dpose as P
from sagekit.formats.textures import compiled_path, sheet_member, write_dds
from sagekit.formats.w3d import W3DFile
from sagekit.game import Install

from assets.cah.kit.geom import add, cross, mul, norm
from assets.cah.kit.paint import paint_sheet
from assets.cah.men_cg import body as MB
from assets.cah.men_cg import paint as MP
from assets.cah.men_cg.design import ANATOMY

from .. import gear as G
from .. import imaging

EA_MODEL, MODEL, SKELETON = "GUAragorn_SKN", "SKAragorn_SKN", "GUAragorn_SKL"
ARMOUR, TRIM = "SKAR_KINGSARM", "SKAR_KINGTRIM"
ANIMS = ("GUAragorn_IDLA", "GUAragorn_IDLE", "GUAragorn_ATKD", "GUAragorn_RUNB")
CHECK_ANIM = "GUAragorn_ATKD"
SHEET, MASK = "skaragornl8.tga", "hc_skaragornl8.tga"            # no longer than guaragorn_rotk.tga
PLATES, PLATES_MASK = "skaragorn_kng.tga", "hc_skaragorn_kng.tga"  # EA's sheet, burnished, and EA's mask
BONES = {"UARM_L": "BAT_UARML", "UARM_R": "BAT_UARMR", "SPINE": "BAT_RIBS", "HEAD": "BAT_HEAD"}
BUDGET = 1550                                                    # EA's Aragorn: 1613 vertices in all
T = MP


def folder():
    d = Path(paths.BUILD) / "heroes" / "aragorn"
    return d, d / "src", d / "work"


def sources():
    d, src, work = folder()
    src.mkdir(parents=True, exist_ok=True)
    g, got = Install(), {}
    for name in (EA_MODEL, SKELETON) + ANIMS:
        data = g.read(g.model_path(name))
        (src / (name.lower() + ".w3d")).write_bytes(data)
        got[name.lower()] = G.sha(data)
    for tex in ("guaragorn_rotk.tga", "guanduril.tga", "hc_guaragornrotk.tga"):
        m = sheet_member(g, tex)
        (src / m.split("\\")[-1]).write_bytes(g.read(m))
    (d / "sources.json").write_text(json.dumps(got, indent=1) + "\n")
    return got


def _forearm(sk, bone):
    r = sk.rest[sk.index(bone)]
    return (r[3], r[7], r[11]), norm((r[0], r[4], r[8]))


PLATE, CHEST = T.IRON, T.BLACKG                 # two tiles of the Men's sheet repainted for the King (tiles())


def tiles():
    """The CaH Men's tiles with two of ours: PLATE, Gondor steel at a darker value with a fine double
    engraved border; CHEST, the same steel with the White Tree engraved, not inlaid (subtle)."""
    from assets.cah.kit import ornament as O
    t = dict(T.TILES)
    t[PLATE] = ("steel", .5, .22, "uv", None, {"engrave": (O.border(14) + O.border(30), 2)})
    t[CHEST] = ("steel", .5, .22, "uv", None, {"engrave": (O.border(14) + T._tree(), 3)})
    return t


def kings_armour(w, sk):
    """(plates, trims): plates lifted off EA's own surface along EA's normals, each vertex on the bone
    EA's skin gives it, drawn with EA's own sheet burnished (EA's detail, read as plate: the black
    tabard with its White Tree becomes a lacquered breastplate); and fine gold rims round each plate.
    Shoulder plates over both shoulders, a breastplate, vambraces on both forearms."""
    def forearm(side):
        o, ax = _forearm(sk, "BAT_FARM" + side)
        return lambda c, bones: bones <= {"BAT_FARM" + side, "B_HAND" + side} and \
            .6 <= sum((c[k] - o[k]) * ax[k] for k in range(3)) <= 2.4

    torso = {"BAT_RIBS", "BAT_UARML", "BAT_UARMR", "BAT_HEAD"}
    parts = [(lambda c, bones: bones <= torso and c[1] > 2.4 and c[2] > 16.1, .17),
             (lambda c, bones: bones <= torso and c[1] < -2.4 and c[2] > 16.1, .17),
             (lambda c, bones: bones <= torso and c[0] > .3 and 15.0 < c[2] < 17.8 and abs(c[1]) <= 2.4, .1),
             (forearm("L"), .1), (forearm("R"), .1)]
    loops = []

    def plates(m):
        loops.clear()
        for keep, off in parts:
            loops.extend(G.surface_plate(m, w, sk, "ARAGORN", keep, None, off))

    def trims(m):
        for loop in loops:
            G.rim(m, loop, .038, T.GOLD)
    plates.__name__, trims.__name__ = "kings_plates", "kings_trims"
    return plates, trims


def sheet():
    """The CaH Men's serious tiles under our name (the trims) and its unit house mask; EA's Return-of-
    the-King sheet burnished for the plates, with EA's own house mask under our name."""
    d, src, work = folder()
    (work / "paint").mkdir(parents=True, exist_ok=True)
    dds, cah_mask = paint_sheet(work, SHEET[:-4], tiles(), MP.INLAY, "gear", MP.special,
                                ramps=dict(MP.RAMPS, **MP.FUN_RAMPS), fill=MP.FILL)
    res = imaging.run([dict(op="unit_mask", src=str(cah_mask), out=str(work / MASK)),
                       dict(op="polish", src=str(src / "guaragorn_rotk.dds"), out=str(work / "skaragorn_kng.png"),
                            contrast=1.3, lift=.04, saturation=.15)], work)
    write_dds(str(work / "skaragorn_kng.png"), str(work / (PLATES[:-4] + ".dds")), alpha=True)
    (work / PLATES_MASK).write_bytes((src / "hc_guaragornrotk.tga").read_bytes())
    return str(dds), res


def build():
    d, src, work = folder()
    work.mkdir(parents=True, exist_ok=True)
    got = sources()
    dds, imaging_report = sheet()
    ea_bytes = (src / (EA_MODEL.lower() + ".w3d")).read_bytes()
    w = W3DFile(ea_bytes)
    sk = P.Skeleton((src / (SKELETON.lower() + ".w3d")).read_bytes())
    tmpl = w.meshes["ARAGORN"]
    plates_fn, trims_fn = kings_armour(w, sk)
    plates = G.draw(tmpl, sk, plates_fn, "guaragorn_rotk.tga", PLATES)
    trims = G.draw(tmpl, sk, trims_fn, "guaragorn_rotk.tga", SHEET, budget=BUDGET - len(plates.verts))
    sizes = [len(plates.verts), len(trims.verts)]
    built = G.assemble(ea_bytes, EA_MODEL, MODEL, "GUARAGORN_SKN",
                       extra=[(ARMOUR, G.chunk_of(plates, ARMOUR)), (TRIM, G.chunk_of(trims, TRIM))])
    out = work / (MODEL.lower() + ".w3d")
    out.write_bytes(built)
    anim = P.Animation((src / (CHECK_ANIM.lower() + ".w3d")).read_bytes())
    report = G.check(ea_bytes, built, EA_MODEL, MODEL, sk, anim, added=[ARMOUR, TRIM], sheets=[SHEET, PLATES], wrapped=[ARMOUR])
    report.update(sources=got, sheet=dds, mask=str(work / MASK), imaging=imaging_report, armour_vertices=sum(sizes),
                  parts=sizes, ea_vertices=sum(len(m.verts) for m in w.meshes.values()))
    (d / "report.json").write_text(json.dumps(report, indent=1, default=str) + "\n")
    textures = {"guaragorn_rotk.tga": str(src / "guaragorn_rotk.dds"), "guanduril.tga": str(src / "guanduril.dds"), SHEET: dds,
                PLATES: str(work / (PLATES[:-4] + ".dds"))}
    (work / "textures.json").write_text(json.dumps(textures, indent=1))
    print("PASS aragorn: %s; EA's five meshes byte for byte, %s and %s added (%d + %d vertices); drift %.1e" % (
        out.name, ARMOUR, TRIM, sizes[0], sizes[1], report["max_bone_drift"]))
    return report


def members():
    d, src, work = folder()
    return {"art\\w3d\\%s\\%s.w3d" % (MODEL.lower()[:2], MODEL.lower()): work / (MODEL.lower() + ".w3d"),
            compiled_path(SHEET, ".dds"): work / (SHEET[:-4] + ".dds"), compiled_path(MASK, ".tga"): work / MASK,
            compiled_path(PLATES, ".dds"): work / (PLATES[:-4] + ".dds"), compiled_path(PLATES_MASK, ".tga"): work / PLATES_MASK}


if __name__ == "__main__":
    build()
