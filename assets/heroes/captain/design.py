"""The Captain of Erebor's model: King Dain's (DUDain_SKN) with the Erebor kit of the Create-a-Hero
dwarf (assets/cah/dwarf/serious.py), as SKEreborCpt_SKN.

  HELMET  Dain's crowned helm -> the Captain's blue-steel helm and pauldrons (kit.py; B_HEAD,
          BAT_UARML/R: the CaH dwarf's rig is Dain's, these bones stand where Dain's do)
  SHIELD  Dain's round shield -> the Shield of Erebor, fitted to Dain's shield (centre, face, size)
  REDAXE  Dain's red axe -> the Erebor war axe, fitted to Dain's axe (head, haft, reach)
  COAT    kept; its red cloth repainted Erebor blue through the Dwarven cloth ramp, and that cloth
          takes the player's colour in game (a unit house mask)
  BODY, HEAD  EA's, byte for byte (Dain's face, beard, mail and gilt)

The gear sheet is the CaH dwarf's serious sheet, painted again under our own name.
"""
import json
from pathlib import Path

from sagekit import paths
from sagekit.formats import w3dpose as P
from sagekit.formats.textures import compiled_path, sheet_member, write_dds
from sagekit.formats.w3d import W3DFile
from sagekit.game import Install

from assets.cah.dwarf import paint as DP
from assets.cah.dwarf import serious as SR
from assets.cah.kit.geom import add, cross, mul, norm, sub
from assets.cah.kit.paint import paint_sheet
from assets.dwarves.style import PALETTE

from .. import gear as G
from .. import imaging
from . import kit as K
from .hero import DONOR_MODEL, MODEL

SKELETON, DESIGN, DESIGN_SKELETON = "DUDain_SKL", "CHDW_TM_U_SKN", "CHDW_DW_U_SKL"
ANIMS = ("DUDain_IDLB", "DUDain_ATKB", "DUDain_RUNA", "DUDain_SPCA", "DUDain_ATNA")
CHECK_ANIM = "DUDain_ATKB"
GEAR_SHEET, COAT_SHEET = "skcapg.tga", "skcapc.tga"          # no longer than Dain's dudain.tga (renamed in place)
MASKS = {GEAR_SHEET: "hc_skcapg.tga", COAT_SHEET: "hc_skcapc.tga"}
RIG_BONES = ("B_HEAD", "BAT_UARML", "BAT_UARMR", "BAT_SPINE2")
EXPECTED = {}                                                  # filled from the first build (sources.json)
SHIELD_SCALE = 1.0                                             # of Dain's shield's radius
AXE_REACH = 1.0                                                # of Dain's axe's length
# vertex budgets (the CaH in-game caps; EA's Dain: helmet 626, shield 61, axe 269, 2552 in all)
BUDGET = {"helm": 1150, "pauldrons": 700, "shield": 600, "axe": 540}


def folder():
    d = Path(paths.BUILD) / "heroes" / "captain"
    return d, d / "src", d / "work"


def sources():
    d, src, work = folder()
    src.mkdir(parents=True, exist_ok=True)
    g, got = Install(), {}
    for name in (DONOR_MODEL, SKELETON, DESIGN, DESIGN_SKELETON) + ANIMS:
        data = g.read(g.model_path(name))
        (src / (name.lower() + ".w3d")).write_bytes(data)
        got[name.lower()] = G.sha(data)
    for tex in ("dudain.tga", "dudainbody.tga"):
        m = sheet_member(g, tex)
        (src / m.split("\\")[-1]).write_bytes(g.read(m))
    if EXPECTED and any(EXPECTED.get(k) != v for k, v in got.items()):
        raise SystemExit("captain: EA's sources are not the ones this design was drawn on: %s" %
                         sorted(k for k, v in got.items() if EXPECTED.get(k) != v))
    (d / "sources.json").write_text(json.dumps(got, indent=1) + "\n")
    return got


def sheets():
    """The gear sheet (the CaH dwarf's tiles, our name), Dain's coat recoloured, both masks."""
    d, src, work = folder()
    (work / "paint").mkdir(parents=True, exist_ok=True)
    dds, cah_mask = paint_sheet(work, "skcapg", K.tiles(), DP.INLAY, "gear", DP.special)
    jobs = [dict(op="unit_mask", src=str(cah_mask), out=str(work / MASKS[GEAR_SHEET])),
            dict(op="recolour", src=str(src / "dudain.dds"), out=str(work / "skcapc.png"), mask=str(work / MASKS[COAT_SHEET]),
                 ramp=PALETTE.ramps["cloth"], hue=.07, soft=.04, sat=.3, gain=1.5, lift=.12)]
    res = imaging.run(jobs, work)
    write_dds(str(work / "skcapc.png"), str(work / "skcapc.dds"))
    return {GEAR_SHEET: str(work / "skcapg.dds"), COAT_SHEET: str(work / "skcapc.dds")}, res


def shield_place(w, sk):
    """Design (the CaH shield's own frame) -> Dain's shield: its centre, face and radius."""
    o = (-0.6, 4.78, 11.5)
    fx, fy = norm((0.143, 0.624, -0.776)), norm((0.99, -0.092, 0.109))
    face = mul(cross(fx, fy), -1)
    c = add(add(o, mul(fx, 1.7)), mul(face, 1.55))
    src = G.frame(c, face, (0, 0, 1))
    pts = G.rest_points(w, sk, "SHIELD")
    cen, axes = G.principal(pts)
    n = axes[2] if axes[2][1] > 0 else mul(axes[2], -1)            # the face looks out, away from the body
    radius = max(abs(G.dot(sub(p, cen), a)) for p in pts for a in axes[:2])
    back = min(G.dot(sub(p, cen), n) for p in pts)
    dst = G.frame(add(cen, mul(n, back + .15)), n, (0, 0, 1))
    return G.frame_map(src, dst, SHIELD_SCALE * radius / 2.95), dict(centre=cen, normal=n, radius=radius)


def axe_place(w, sk):
    """Design (the CaH axe: head at AXE_C + 2.05 AXE_D, blade toward AXE_B) -> Dain's axe."""
    pts = G.rest_points(w, sk, "REDAXE")
    cen, axes = G.principal(pts)
    along = axes[0]
    ts = [G.dot(sub(p, cen), along) for p in pts]
    lo, hi = min(ts), max(ts)
    spread = lambda a, b: max([G.dot(sub(p, cen), axes[1]) for p, t in zip(pts, ts) if a <= t <= b] or [0]) - \
        min([G.dot(sub(p, cen), axes[1]) for p, t in zip(pts, ts) if a <= t <= b] or [0])
    span = hi - lo
    if spread(hi - .3 * span, hi) < spread(lo, lo + .3 * span):     # the head is the end with the blades
        along, ts, lo, hi = mul(along, -1), [-t for t in ts], -hi, -lo
    head = add(cen, mul(along, hi - .16 * (hi - lo)))
    down = norm(sub((0, 0, -1), mul(along, G.dot((0, 0, -1), along))))
    src = G.frame(add(SR.AXE_C, mul(SR.AXE_D, 2.05)), SR.AXE_D, SR.AXE_B)
    dst = G.frame(head, along, down)
    return G.frame_map(src, dst, AXE_REACH * (hi - lo) / 10.6), dict(head=head, along=along, length=hi - lo)


def build():
    d, src, work = folder()
    work.mkdir(parents=True, exist_ok=True)
    got = sources()
    tex, imaging_report = sheets()
    ea_bytes = (src / (DONOR_MODEL.lower() + ".w3d")).read_bytes()
    w = W3DFile(ea_bytes)
    sk = P.Skeleton((src / (SKELETON.lower() + ".w3d")).read_bytes())
    dsk = P.Skeleton((src / (DESIGN_SKELETON.lower() + ".w3d")).read_bytes())
    rig = G.Rig(sk, dsk, RIG_BONES)
    tmpl = w.meshes["HELMET"]
    helm = G.draw(tmpl, rig, K.helm_captain, "dudain.tga", GEAR_SHEET, place=K.dain_fit,
                  budget=BUDGET["helm"])
    pauldrons = G.draw(tmpl, rig, K.pauldrons_captain, "dudain.tga", GEAR_SHEET, budget=BUDGET["pauldrons"])
    shield_fn, shield_info = shield_place(w, sk)
    shield = G.draw(w.meshes["SHIELD"], sk, SR.shield_erebor, "dudain.tga", GEAR_SHEET, place=shield_fn,
                    bone_map={"BAT_FARML": "B_SHIELD"}, budget=BUDGET["shield"])
    axe_fn, axe_info = axe_place(w, sk)
    axe = G.draw(w.meshes["REDAXE"], sk, SR.axe_erebor, "dudain.tga", GEAR_SHEET, place=axe_fn, bone_map={"B_HAND_R": "B_AXE"},
                 budget=BUDGET["axe"])
    G.merge(helm, pauldrons)
    replace = {"HELMET": G.chunk_of(helm, "HELMET"), "SHIELD": G.chunk_of(shield, "SHIELD"), "REDAXE": G.chunk_of(axe, "REDAXE")}
    built = G.assemble(ea_bytes, DONOR_MODEL, MODEL, "DUDAIN_SKN", replace=replace, retex={"COAT": [("dudain.tga", COAT_SHEET)]})
    out = work / (MODEL.lower() + ".w3d")
    out.write_bytes(built)
    anim = P.Animation((src / (CHECK_ANIM.lower() + ".w3d")).read_bytes())
    report = G.check(ea_bytes, built, DONOR_MODEL, MODEL, sk, anim, replaced=list(replace), retexed=["COAT"],
                     sheets=[GEAR_SHEET])
    report.update(sources=got, textures=tex, masks={k: str(work / v) for k, v in MASKS.items()}, imaging=imaging_report,
                  shield={k: [round(x, 3) for x in v] if isinstance(v, list) else round(v, 3) for k, v in shield_info.items()},
                  axe={k: [round(x, 3) for x in v] if isinstance(v, list) else round(v, 3) for k, v in axe_info.items()},
                  vertices={"HELMET": len(helm.verts), "SHIELD": len(shield.verts), "REDAXE": len(axe.verts)},
                  ea_vertices={n: len(m.verts) for n, m in w.meshes.items()})
    (d / "report.json").write_text(json.dumps(report, indent=1, default=str) + "\n")
    textures = {"dudainbody.tga": str(src / "dudainbody.dds"), "dudain.tga": str(src / "dudain.dds")}
    textures.update(tex)
    (work / "textures.json").write_text(json.dumps(textures, indent=1))
    print("PASS captain: %s; EA's BODY and HEAD byte for byte, COAT retextured, HELMET/SHIELD/REDAXE the Erebor kit "
          "(%d, %d, %d vertices; EA's %d, %d, %d); drift %.1e" % (
              out.name, len(helm.verts), len(shield.verts), len(axe.verts), len(w.meshes["HELMET"].verts),
              len(w.meshes["SHIELD"].verts), len(w.meshes["REDAXE"].verts), report["max_bone_drift"]))
    return report


def members():
    """{archive member: local file} this model ships."""
    d, src, work = folder()
    out = {"art\\w3d\\%s\\%s.w3d" % (MODEL.lower()[:2], MODEL.lower()): work / (MODEL.lower() + ".w3d")}
    for sheet in (GEAR_SHEET, COAT_SHEET):
        out[compiled_path(sheet, ".dds")] = work / (sheet[:-4] + ".dds")
        out[compiled_path(MASKS[sheet], ".tga")] = work / MASKS[sheet]
    return out


if __name__ == "__main__":
    build()
