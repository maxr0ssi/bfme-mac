"""The old castle walls' shared pieces (oldwall_segment, oldwall_gate): EA's castle-wall section
(a 47.5-thick core, a 4.3 overhang on both faces, a walkway between two parapets) rebuilt in the
new Dwarven walls' profile (wall_segment/README.md), scaled to the old section. Blender side only.

Every piece is a function of `walk`, the section's walkway height: 51.91 in DBWallRamp2, 51.78 in
DBWallGate's wall stubs (EA's two models differ by 0.13), so the lines run on where they meet.

The section (per face; x is |x|, measured on EA's models):
    core face       23.77, from the core's foot up to the overhang (walk - 7.22)
    overhang        23.77 -> 28.1 in EA's; ours: a flat underside at walk - 7.22 carried by
                    stepped corbels, the rune band's face at 27.8 up to walk - 0.71
    coping          a bronze drip band at 28.1 (walk - 0.41 .. walk + 0.69), the coping face at
                    28.0 to walk + 4.69, a bronze chamfer, the top at walk + 5.09 (57.0 on the
                    segment, like the new walls), the walkway side at 23.77 (EA's parapet back)
    chevrons        the fortress's chevron_parapet on the coping, walk + 4.69 .. walk + 11.69
                    (56.6 .. 63.6 on the segment: EA's parapet top is 63.92)
    plinth          battered, foot 2.3 out of the core face, top 0.8 out at 5.8, 0 out at 6.3
"""
from mathutils import Vector as V

from sagekit.blender.geometry import loft, prism_uz, sweep

CORE_X = 23.77
BAND_X = 27.8
OUTER_X = 28.1                    # EA's parapet face: the section's outer limit
COPING_PATH = 26.9                # chevron / coping path; d out of it
WALK = 51.91                      # DBWallRamp2's walkway (EA's)


def clear_target(name):
    """Remove EA's placeholder faces from the target mesh. The three old castle-wall models are
    unfinished EA stand-ins painted from a 256 placeholder sheet that reads "Dwarven Wall"
    (DBWall.tga); every one of their volumes is rebuilt as new solids on the faction atlas instead
    (kept to EA's footprint and ends), so no face samples the placeholder."""
    import bmesh
    import bpy
    me = bpy.data.objects[name].data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=list(bm.verts), context="VERTS")
    bm.to_mesh(me)
    bm.free()
    me.update()


def coping(walk):
    """(x, z) profile of the coping (outer face first, walkway side last) and its edge tags."""
    w = walk
    prof = [(BAND_X, w - 0.71), (OUTER_X, w - 0.41), (OUTER_X, w + 0.69), (28.0, w + 0.79), (28.0, w + 4.69),
            (27.6, w + 5.09), (CORE_X, w + 5.09), (CORE_X, w - 0.71)]
    tags = ["trim", "trim", "trim", "stoneA", "trim", "top", "stoneA", None]
    return prof, tags


def box_x(s, x0, x1, y0, y1, z0, z1, tags, cap_lo, cap_hi):
    """A box on the s face, |x| x0..x1 (x1 outward), y0..y1, z0..z1: polygon in (y, z), extruded
    along the face normal. tags: [bottom, +y end, top, -y end]; cap_lo / cap_hi: the |x| x0 / x1 faces."""
    a, t, n = V((0, 0, 0)), V((0, 1, 0)), V((s, 0, 0))
    return prism_uz(a, t, n, [(y0, z0), (y1, z0), (y1, z1), (y0, z1)], x0, x1, tags, cap_hi, cap_lo)


def run(kit, y0, y1, walk=WALK, foot=-47.605, corbels=(), banners=(), plinth=(None, None), relief=None, chev=None):
    """The section along y0..y1 on both faces: core, plinth, overhang band, corbels, coping,
    chevrons, banners. Ends are open (end caps drawn: the neighbour's section meets them).
      corbels  y centres of the corbels under the overhang
      banners  (y centre, z_top, width, length) hung on the core face under the corbels
      plinth   (y0, y1) of the plinth, default the run
      relief   y centre of a statue pilaster on each face, or None
      chev     (y0, y1) of the chevron parapet, default the run"""
    out = []
    w, bz = walk, walk - 7.22
    py0, py1 = plinth[0] if plinth[0] is not None else y0, plinth[1] if plinth[1] is not None else y1
    # core: the lower part hides behind the plinth, the upper shows the core face
    out.append(prism_uz(V((0, 0, 0)), V((0, 1, 0)), V((1, 0, 0)),
                        [(y0, foot), (y1, foot), (y1, 6.3), (y0, 6.3)], -CORE_X, CORE_X,
                        [None, "stoneB", None, "stoneB"], None, None))
    out.append(prism_uz(V((0, 0, 0)), V((0, 1, 0)), V((1, 0, 0)),
                        [(y0, 6.3), (y1, 6.3), (y1, w), (y0, w)], -CORE_X, CORE_X,
                        [None, "stoneB", "top", "stoneB"], "stoneA", "stoneA"))
    for s in (1, -1):
        n = V((s, 0, 0))
        # battered plinth, down to the core's foot (the wall stands on any slope)
        prof = [(CORE_X, foot), (CORE_X + 2.3, foot), (CORE_X + 2.3, 0.8), (CORE_X + 0.8, 5.8), (CORE_X, 6.3)]
        out += sweep([(s * 0.001, py0), (s * 0.001, py1)], [(x - 0.001, z) for x, z in prof],
                     [None, "stoneB", "stoneA", "top", None])[0]
        # overhang band: flat underside, rune band on its face (Erebor-blue enamel, gold runes)
        out.append(box_x(s, CORE_X, BAND_X, y0, y1, bz, w - 0.71, ["stoneB", "stoneB", None, "stoneB"], None, "rune"))
        # coping and chevron parapet
        prof, tags = coping(w)
        out += sweep([(s * 0.001, y0), (s * 0.001, y1)], [(x - 0.001, z) for x, z in prof], tags)[0]
        c0, c1 = chev or (y0, y1)
        a = V((s * COPING_PATH, c0, 0))
        out += kit.chevron_parapet(a, V((0, 1, 0)), n, c1 - c0, d0=CORE_X + 0.2 - COPING_PATH,
                                   d1=28.0 - COPING_PATH, dz=w - WALK)
        # stepped corbels under the overhang: three blocks, each further out
        for yc in corbels:
            for k, (z0, z1, x1) in enumerate(((bz - 5.6, bz - 3.6, CORE_X + 1.5), (bz - 3.6, bz - 1.8, CORE_X + 2.8),
                                             (bz - 1.8, bz, BAND_X - 0.05))):
                hw = 1.35 - 0.1 * k
                out.append(box_x(s, CORE_X, x1, yc - hw, yc + hw, z0, z1,
                                 ["stoneB", "stoneB", None if k == 2 else "top", "stoneB"], None, "stoneB"))
        # statue pilaster in the middle of the face, standing on the plinth
        if relief is not None:
            out += pilaster(s, relief, bz - 6.0)
        # banners in the bays
        for yc, z_top, width, length in banners:
            out += kit.banner(V((s * CORE_X, 0, 0)), V((0, s, 0)), n, s * yc, z_top, width, length, d=0.05)
    return out


def pilaster(s, yc, top):
    """A dwarf-statue relief on the core face between a stepped base and a bronze capital."""
    hw = 3.2
    return [
        box_x(s, CORE_X - 0.5, CORE_X + 2.0, yc - hw - 0.6, yc + hw + 0.6, 0.0, 9.5, [None, "stoneB", "top", "stoneB"], None, "stoneB"),
        box_x(s, CORE_X - 0.5, CORE_X + 1.4, yc - hw, yc + hw, 9.5, top - 3.0, [None, "stoneB", None, "stoneB"], None, "statue"),
        box_x(s, CORE_X - 0.5, CORE_X + 1.8, yc - hw - 0.4, yc + hw + 0.4, top - 3.0, top - 1.8, ["stoneB", "trim", "top", "trim"],
              None, "trim"),
        box_x(s, CORE_X - 0.5, CORE_X + 1.2, yc - hw + 0.6, yc + hw - 0.6, top - 1.8, top, [None, "stoneB", "top", "stoneB"],
              None, "tri|a"),
    ]


def stair(y_top, y_foot, z_top, half, steps, kit=None):
    """A Dwarven stair down EA's ramp (from the walkway z_top at y_top to the ground at y_foot,
    |x| <= half + 2.2): a flight of `steps` treads between two sloping side walls with bronze
    copings, and a stepped newel with a gilded point at the foot of each wall. y_foot may be
    below y_top (a ramp running to -y)."""
    sg = 1 if y_foot > y_top else -1
    run_ = abs(y_foot - y_top) / steps
    rise = z_top / steps
    a, t, n = V((0, 0, 0)), V((0, sg, 0)), V((1, 0, 0))     # u = distance down the ramp (along sg*y)
    u0 = sg * y_top
    L = abs(y_foot - y_top)
    poly = [(u0, 0.0), (u0 + L, 0.0)]
    for i in reversed(range(steps)):
        h = z_top - (i + 0.5) * rise
        poly += [(u0 + (i + 1) * run_, h), (u0 + i * run_, h)]
    tags = [None, "stoneB"]
    for i in reversed(range(steps)):
        tags += ["top", "stoneB"]
    tags[-1] = None                                      # the back edge, against the core's end
    out = [prism_uz(a, t, n, poly, -half, half, tags, None, None)]
    for sx in (1, -1):
        x0, x1 = sorted((sx * half, sx * (half + 2.2)))
        # the side walls end inside the newel at the foot
        f0 = u0 + L - 3.0
        uf = f0 + 1.5
        hf = 2.2 + (u0 + L - uf) * z_top / L
        wall = [(u0, 0.0), (uf, 0.0), (uf, hf), (u0, z_top + 2.2)]
        out.append(prism_uz(a, t, n, wall, x0, x1, [None, None, None, "stoneB"], "stoneA", "stoneA"))
        cap = [(u0, z_top + 2.2), (uf, hf), (uf, hf + 0.8), (u0, z_top + 3.0)]
        out.append(prism_uz(a, t, n, cap, x0 - 0.2 if sx > 0 else x0, x1 if sx > 0 else x1 + 0.2,
                            ["trim", None, "top", "trim"], "trim", "trim"))
        # the newel at the foot
        c = sx * (half + 1.1)
        out.append(prism_uz(a, t, n, [(f0, 0.0), (u0 + L, 0.0), (u0 + L, 5.4), (f0, 5.4)], c - 1.25, c + 1.25,
                            [None, "stoneB", "top", "stoneB"], "stoneB", "stoneB"))
        out.append(prism_uz(a, t, n, [(f0 + 0.4, 5.4), (u0 + L - 0.4, 5.4), (u0 + L - 0.4, 6.3), (f0 + 0.4, 6.3)],
                            c - 0.95, c + 0.95, [None, "trim", "top", "trim"], "trim", "trim"))
        um = f0 + 1.5
        top = [V((c - 0.9, sg * (um - 1.1), 6.3)), V((c + 0.9, sg * (um - 1.1), 6.3)),
               V((c + 0.9, sg * (um + 1.1), 6.3)), V((c - 0.9, sg * (um + 1.1), 6.3))]
        out.append(loft([top, [V((c, sg * um, 9.4))] * 4], ["trim"], cap0=("top", False), cap1=("top", False)))
    return out
