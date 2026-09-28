"""Pieces the stable and the forge share (and their level-up meshes), on top of the citadel's kit
(assets/men/shapes.py) and the production motifs (assets/men/barracks/motifs.py, imported, never
edited). Blender side: mathutils imports stay inside the functions, so the recipes load anywhere.

    mirrored        solids reflected through a vertical plane (y = c or x = c), re-oriented
    dormer          a gabled dormer on a roof slope: a stone front with a window, slate cheeks,
                    raking coping and a gilt knob; its back buried in the roof
    gable_dress     raking coping up a gable's rakes with pinnacles on its eave corners (and one
                    on the apex unless something else stands there)
    keystone        a raised keystone on an arch's crown
    archivolt       a voussoir ring with a raised keystone and moulded imposts round an arch
    cornice         motifs.cornice with the corona's top closed (under the leaning cymatium a strip
                    of it shows: the sky check sees in there)
    socle           a stepped stone base under a free-standing piece
    faces           (anchor, t, n) of a square's four faces
    drop_loose      EA's loose vertices removed from the target (Blender side; see its docstring)
    KeepFire        a paint layer: EA's own colours kept where its sheet paints fire (the forge's
                    coals would turn to white stone under the Recolour)
"""


def faces(cx, cy, half):
    """(anchor at the face's middle, t, n) of a square's four faces, t x n = -z."""
    from mathutils import Vector as V
    out = []
    for nx, ny in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        n = V((nx, ny, 0))
        out.append((V((cx + nx * half, cy + ny * half, 0)), V((-ny, nx, 0)), n))
    return out


def mirrored(solids, y0=None, x0=None):
    """The solids reflected through the plane y = y0 (or x = x0) (a copy; each re-oriented)."""
    from mathutils import Vector as V

    from sagekit.blender.geometry import Solid

    def f(p):
        return V((p.x, 2 * y0 - p.y, p.z)) if x0 is None else V((2 * x0 - p.x, p.y, p.z))
    out = []
    for s in solids:
        m = Solid()
        for pts, tag, keep in s.polys:
            m.polys.append([[f(p) for p in reversed(pts)], tag, keep])
        out.append(m.orient())
    return out


def dormer(kit, a, t, n, u, d_front, z0, z1, half, rise, d_back, glass="window", knob=True):
    """A gabled dormer standing out of a roof slope at u: its stone front (d_front, a pentagon from
    z0 to its eave z1 and apex z1 + rise, half wide) with an arched window, slate roof halves with
    a small overhang, moulded raking coping and a gilt knob on the apex. Everything runs back to
    d_back, which must lie inside the roof (the back and the foot are buried)."""
    from sagekit.blender.geometry import prism_uz

    from ..barracks.motifs import knob as knob_, window
    apex = z1 + rise
    body = [(u - half, z0), (u + half, z0), (u + half, z1), (u, apex), (u - half, z1)]
    out = [prism_uz(a, t, n, body, d_back, d_front, [None, "stoneA", "stoneA", "stoneA", "stoneA"], "stoneA", None)]
    over, th = 0.55, 0.5
    slope = rise / half
    for e in (-1, 1):
        ue = u + e * (half + over)
        ze = z1 - over * slope
        poly = [(u, apex), (ue, ze), (ue, ze + th), (u, apex + th)]
        if e < 0:
            poly = [(ue, ze), (u, apex), (u, apex + th), (ue, ze + th)]
            tags = ["stoneB", None, "slate", "trim"]
        else:
            tags = ["stoneB", "trim", "slate", None]
        out.append(prism_uz(a, t, n, poly, d_back, d_front + 0.35, tags, "course", None))
    wh = min(0.9, half * 0.42)
    f = a + n * d_front
    out += window(kit, f, t, n, u, wh, z0 + 0.9, z1 - wh - 0.45, glass=glass, w=0.35, d=0.3, key=True, sill=False,
                  back=-0.2)
    if knob:
        c = a + t * u + n * (d_front + 0.1)
        out += knob_(c.x, c.y, apex + th - 0.2, apex + th + 2.6, r=0.42)
    return out


def gable_dress(kit, a, t, n, half, z_eave, z_apex, d0, d1, apex=True, corners=True, w=0.8,
                pin=(1.6, 3.4, 0.9), coping=True):
    """Moulded coping up both rakes of a gable centred at u = 0 on (a, t, n), `half` wide at its
    eaves (z_eave), its apex at z_apex, standing d0..d1 (coping=False: EA's own cornice kept); pinnacles (pedestal height, spirelet,
    half) on the eave corners and, if `apex`, on the apex."""
    from sagekit.blender.geometry import prism_uz
    out = []
    for e in ((-1, 1) if coping else ()):
        poly = [(0.0, z_apex), (e * half, z_eave), (e * (half + w), z_eave), (0.0, z_apex + w * 1.2)]
        if e < 0:
            poly.reverse()
        out.append(prism_uz(a, t, n, poly, d0, d1, ["stoneB"] * 4, "course", None))
    ph, sp, hw = pin
    m = (d0 + d1) / 2
    if corners:
        for e in (-1, 1):
            c = a + t * (e * (half + (w * 0.5 if coping else 0.0))) + n * m
            out += kit.pinnacle(c.x, c.y, z_eave - 0.3, z_eave - 0.3 + ph, half=hw, spire=sp)
    if apex:
        c = a + n * m
        z = z_apex + (0.4 if coping else -0.3)
        out += kit.pinnacle(c.x, c.y, z, z + ph, half=hw, spire=sp * 1.2)
    return out


def keystone(a, t, n, u, z0, z1, half0=0.6, half1=0.95, d0=-0.3, d1=0.8):
    """A raised keystone on an arch's crown at u: z0..z1, flaring from half0 to half1 wide."""
    from sagekit.blender.geometry import prism_uz
    return [prism_uz(a, t, n, [(u - half0, z0), (u + half0, z0), (u + half1, z1), (u - half1, z1)], d0, d1,
                     ["stoneB", "stoneB", "top", "stoneB"], "stoneA", None)]


def archivolt(kit, a, t, n, u, half, spring, rise, w=1.4, d=0.7, count=11, key=0.35, back=-0.3):
    """A ring of voussoirs w wide round an arch at u (its opening: half, springing, rise), d proud,
    a keystone rising `key` over the ring, and a moulded impost block at each springing."""
    from ..barracks.motifs import slab
    c = a + t * u
    out = kit.voussoirs(c, t, n, (half, rise, spring), (half + w, rise + w, spring), back, d, count=count,
                        key=(0.45 * w + 0.3, spring + rise + w + key, 0.3))
    for e in (-1, 1):
        u0, u1 = sorted((u + e * (half - 0.2), u + e * (half + w + 0.35)))
        out.append(slab(a, t, n, u0, u1, spring - 0.7, spring, back, d + 0.25, front="course"))
    return out


def cornice(a, t, n, u0, u1, z, depth=1.5, dentils=True, pitch=1.1, back=-0.25):
    """motifs.cornice (fillet, dentils, corona, cymatium; about 2.15 high), every solid closed on top."""
    from ..barracks.motifs import cornice as cornice_
    out = cornice_(a, t, n, u0, u1, z, depth=depth, dentils=dentils, pitch=pitch, back=back)
    for sol in out:
        for p in sol.polys:
            p[2] = p[2] or (p[0][0].z > z + 0.3 and all(abs(q.z - p[0][0].z) < 1e-4 for q in p[0]))
    return out


def socle(cx, cy, z0, half, steps=((1.4, "stoneB"), (1.0, "course"))):
    """A stepped square base centred on (cx, cy) from z0: each step (height, tag), narrowing."""
    from ..barracks.motifs import box
    out, z, h = [], z0, half
    for dz, tag in steps:
        out.append(box(cx - h, cx + h, cy - h, cy + h, z, z + dz, tag))
        z, h = z + dz, h * 0.8
    return out


def drop_loose(target):
    """Delete the vertices of the target mesh that no face uses (called from design(), which runs
    in the geometry step with EA's model in the scene). EA's forge body carries four (on the
    weapon platform's front edge); the checks hold the target to none, and `clear` removes faces
    only. Harmless: no face, bone or UV refers to them. -> how many."""
    import bmesh
    import bpy
    me = bpy.data.objects[target].data
    bm = bmesh.new()
    bm.from_mesh(me)
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
        bm.to_mesh(me)
        me.update()
    bm.free()
    return len(loose)


def KeepFire(box, hue=(0.0, 52.0), sat=(0.38, 0.55), val=(0.30, 0.45)):
    """A paint layer (Building.decals) keeping EA's colours on EA's faces inside `box` ((lo, hi)
    in design coordinates) whose painting is fire: warm, saturated and bright (the glowing coals of
    the forge bed). Built on first use: numpy lives on Blender's Python (men/paint.py)."""
    from ..paint import keep_layers
    return keep_layers()["KeepFire"](box, hue=hue, sat=sat, val=val)
