"""Night lights inside Blender (host side and the standard: sagekit/nightlights.py).

  cast     the pipeline's night step: each of the recipe's lights cast onto our finished body (the
           geometry stage: the target and the `night_surfaces` meshes) along its outward normal.
           Its pane is its outline, flat, `offset` proud of what it lights: the wall its probes
           all land on; over a relief (a panel in its frame) the plane fitted through the probes;
           over a curved one (rock) draped cell by cell; across an opening into the building, the
           light's own plane (Caster.pane). Its halo is draped: a grid of `cell` rays, each cell
           kept where its corners land on one piece of surface (a depth jump over `step` ends a
           piece), cells on one plane merged into rectangles. Recorded in the target's own
           coordinates (work/night.json).
  render   the night view: moonlight and a dark sky, the night meshes drawn as the game draws them
           (additive ones emissive - texture x emissive colour, light only for the camera; EA's
           opaque night frames lit like the stone).
  checks   every shipped night triangle's corners within the look's tolerance of our surface, the
           triangle facing out of it (a free glow card, Light.glow: its centre within its span); night meshes draw the faction's texture only, which is
           shipped, registered and depended on; no other faction's night sheet anywhere.
"""
import json
import os

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import tessellate_polygon

from .. import nightlights as N
from ..workspace import Workspace
from ..formats.w3d import W3DFile
from ..formats.w3dlight import material
from ..paint.night import uv as motif_uv
from . import render, scene


# ------------------------------------------------------------------------------------ cast
class Caster:
    """Rays against our body in design space (the target's mesh space, or world axes for a
    world_space recipe), results in the target's mesh space."""

    def __init__(self, b, lk):
        tgt = bpy.data.objects[b.target]
        to_design = Matrix.Identity(4) if b.world_space else tgt.matrix_world.inverted()
        self.out = tgt.matrix_world.inverted() if b.world_space else Matrix.Identity(4)
        verts, polys = [], []
        for n in (b.target,) + tuple(b.night_surfaces):
            o = bpy.data.objects[n]
            m, off = to_design @ o.matrix_world, len(verts)
            verts += [m @ v.co for v in o.data.vertices]
            polys += [tuple(off + i for i in p.vertices) for p in o.data.polygons]
        self.bvh, self.lk = BVHTree.FromPolygons(verts, polys), lk

    def hit(self, L, u, z, backs=False):
        """(point, normal) where the light's ray at (u, z) meets a front face, or None. backs: a
        face turned away counts too, as facing the light (EA's archery door is a panel facing in)."""
        n = Vector(L.n)
        loc, nrm, _, _ = self.bvh.ray_cast(Vector(L.point(u, z)) + n * L.reach, -n, 2 * L.reach)
        if loc is None or abs(nrm.dot(n)) <= 0.05 or (nrm.dot(n) < 0 and not backs):
            return None
        return loc, (nrm if nrm.dot(n) > 0 else -nrm).normalized()

    def pane(self, L, off):
        """The light's outline as one flat polygon, `off` proud of what it lights: the plane its
        probes land on when they all land on one (a wall, battered or not); over a relief (a
        window's panel in its frame, rough rock), the plane fitted through the probes, moved out
        until two thirds of them are at or behind it (what stands further out, a mullion or a
        frame, hides the light) - or, where the outline's corners would stand off a curved
        surface (rock), draped over it; where most probes go through (an opening into the
        building), the light's own plane.
        -> (points, normals, (u, z) per point, triangles, 'flat' | 'relief' | 'draped' | 'open')."""
        outline, n = L.outline, Vector(L.n)
        us, zs = [p[0] for p in outline], [p[1] for p in outline]
        cu, cz = sum(us) / len(us), sum(zs) / len(zs)
        probes = [(cu + 0.9 * (u - cu), cz + 0.9 * (z - cz)) for u, z in outline] + [(cu, cz)]
        k = self.lk.cell
        probes += [(u, z) for u in frange(min(us), max(us), k) for z in frange(min(zs), max(zs), k) if inside((u, z), outline)]
        hits = [self.hit(L, u, z, backs=True) for u, z in probes]
        got = [h for h in hits if h]
        p0, n0 = got[-1] if got else (Vector(L.point(cu, cz)), n)
        if len(got) == len(hits) and all(h[1].dot(n0) > 0.999 and abs((h[0] - p0).dot(n0)) < 0.02 for h in got):
            how = "flat"
        elif len(hits) - len(got) > len(got):
            p0, n0, how = Vector(L.point(cu, cz)), n, "open"
        else:                                           # over a relief: the plane fitted through
            import numpy as np                          # it, in front of two thirds of it
            P = np.array([h[0] for h in got])
            c = P.mean(0)
            w = Vector(np.linalg.svd(P - c)[2][2]) if len(got) >= 3 else n
            n0 = (w if w.dot(n) > 0 else -w).normalized()
            n0 = n0 if n0.dot(n) > 0.7 else n           # a rough patch: stay square to the light
            ds = sorted(((h[0] - Vector(c)).dot(n0) for h in got), reverse=True)
            p0, how = Vector(c) + n0 * ds[len(ds) // 3], "relief"
            corners = [self.hit(L, cu + 0.95 * (u - cu), cz + 0.95 * (z - cz)) for u, z in outline]
            if all(corners) and max(abs((h[0] - p0).dot(n0)) for h in corners) > self.lk.tolerance - off:
                got = self.drape(L, outline, off, step=3 * self.lk.step)
                if got and got[4] <= 0.15 * (got[4] + got[5]):
                    return got[0], got[1], got[2], got[3], "draped"
        dn = n.dot(n0)
        pts = []
        for u, z in outline:                             # the ray at (u, z) meets the plane
            o = Vector(L.point(u, z)) + n * L.reach
            pts.append(o - n * ((o - p0).dot(n0) / dn) + n0 * off)
        tris = [tuple(t) for t in tessellate_polygon([[Vector((u, z, 0)) for u, z in outline]])]
        return pts, [n0] * len(pts), list(outline), tris, how

    def drape(self, L, outline, off, step=None):
        """Cells of the outline's box whose centre is inside it, each on one piece of surface (no
        depth jump over `step`); (points, normals, [(u, z)] per point, quads - coplanar runs
        merged, cells dropped, cells kept). None: nothing lands."""
        lk, step = self.lk, step or self.lk.step
        u0, u1 = min(p[0] for p in outline), max(p[0] for p in outline)
        z0, z1 = min(p[1] for p in outline), max(p[1] for p in outline)
        nu, nz = max(1, round((u1 - u0) / lk.cell)), max(1, round((z1 - z0) / lk.cell))
        du, dz = (u1 - u0) / nu, (z1 - z0) / nz
        grid = {(i, j): self.hit(L, u0 + i * du, z0 + j * dz) for i in range(nu + 1) for j in range(nz + 1)}
        label, dropped = {}, 0
        for i in range(nu):
            for j in range(nz):
                if not inside((u0 + (i + .5) * du, z0 + (j + .5) * dz), outline):
                    continue
                c = [grid[k] for k in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))]
                if any(h is None for h in c):
                    dropped += 1
                    continue
                n0 = c[0][1]
                if max(abs((h[0] - c[0][0]).dot(Vector(L.n))) for h in c) > step or any(h[1].dot(n0) < 0.5 for h in c):
                    dropped += 1
                    continue
                planar = all(h[1].dot(n0) > 0.999 and abs((h[0] - c[0][0]).dot(n0)) < 0.02 for h in c)
                label[i, j] = (round(n0.x, 3), round(n0.y, 3), round(n0.z, 3), round(n0.dot(c[0][0]), 2)) if planar \
                    else (i, j)
        if not label:
            return None
        pts, nrm, uz, quads, index = [], [], [], [], {}

        def vert(i, j):
            if (i, j) not in index:
                p, n = grid[i, j]
                index[i, j] = len(pts)
                pts.append(p + n * off)
                nrm.append(n)
                uz.append((u0 + i * du, z0 + j * dz))
            return index[i, j]
        for (i0, j0, i1, j1) in merged(label):
            quads.append((vert(i0, j0), vert(i1, j0), vert(i1, j1), vert(i0, j1)))
        return pts, nrm, uz, quads, dropped, len(label)


def frange(a, b, k):
    n = max(1, int((b - a) / k))
    return [a + (b - a) * (i + 0.5) / n for i in range(n)]


def inside(p, poly):
    """Point in polygon (even-odd)."""
    x, y, c = p[0], p[1], False
    for (ax, ay), (bx, by) in zip(poly, poly[1:] + poly[:1]):
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
            c = not c
    return c


def merged(label):
    """Greedy rectangles (i0, j0, i1, j1) over grid cells with equal labels."""
    left, out = dict(label), []
    for (i, j) in sorted(label, key=lambda k: (k[1], k[0])):
        if (i, j) not in left:
            continue
        lab = left.pop((i, j))
        i1 = i + 1
        while left.get((i1, j)) == lab:
            left.pop((i1, j))
            i1 += 1
        j1 = j + 1
        while all(left.get((k, j1)) == lab for k in range(i, i1)):
            for k in range(i, i1):
                left.pop((k, j1))
            j1 += 1
        out.append((i, j, i1, j1))
    return out


def cast(b, ws):
    """Every light of the recipe onto our body -> work/night.json {names, lights, pane, halo}."""
    lk = N.look(b)
    rec = N.record(ws)
    c = Caster(b, lk)
    groups = {"pane": Group(), "halo": Group(), "glow": Group()}
    rec["lights"] = []
    for k, L in enumerate(b.night_lights(b.style.shapes())):
        info = {"name": L.name or "%s %d" % (L.kind, k), "kind": L.kind, "pane": 0, "halo": 0, "how": "", "dropped": 0}
        us, zs = [p[0] for p in L.outline], [p[1] for p in L.outline]
        box = (min(us), max(us), min(zs), max(zs))
        if L.kind == "glow":                            # a free card: cast onto nothing (Light.glow)
            pts = [Vector(L.point(u, z)) for u, z in L.outline]
            info["how"] = "free"
            info["pane"] = groups["glow"].add(c.out, pts, [Vector(L.n)] * 4, [motif("halo", box, x, lk) for x in L.outline],
                                              [(0, 1, 2, 3)], L.n)
            rec["lights"].append(info)
            continue
        pts, nrm, uz, tris, info["how"] = c.pane(L, lk.offset)
        info["pane"] = groups["pane"].add(c.out, pts, nrm, [motif(L.kind, box, x, lk) for x in uz], tris, L.n)
        if L.halo:
            cu, cz, hu, hz = (box[0] + box[1]) / 2, (box[2] + box[3]) / 2, (box[1] - box[0]) * lk.halo[0] / 2, \
                (box[3] - box[2]) * lk.halo[1] / 2
            ring = [(cu - hu, cz - hz), (cu + hu, cz - hz), (cu + hu, cz + hz), (cu - hu, cz + hz)]
            hb = (cu - hu, cu + hu, cz - hz, cz + hz)
            got = c.drape(L, ring, lk.halo_offset)
            if got:
                pts, nrm, uz, quads, d, _ = got
                info["halo"] = groups["halo"].add(c.out, pts, nrm, [motif("halo", hb, x, lk) for x in uz], quads, L.n)
                info["dropped"] += d
        rec["lights"].append(info)
    for role, g in groups.items():
        rec[role] = g.json()
    with open(ws.path("work", "night.json"), "w") as fh:
        json.dump(rec, fh)


def motif(kind, box, uz, lk):
    u0, u1, z0, z1 = box
    return motif_uv(kind, (uz[0] - u0) / max(u1 - u0, 1e-6), (uz[1] - z0) / max(z1 - z0, 1e-6), lk.size)


class Group:
    """Triangles of one role, vertices in the target's mesh space."""

    def __init__(self):
        self.v, self.n, self.uv, self.t = [], [], [], []

    def add(self, M, pts, nrm, uvs, polys, out):
        """polys (triangles or quads) wound to face `out` (the light's normal); returns triangles."""
        off, R = len(self.v), M.to_3x3()
        self.v += [list(M @ p) for p in pts]
        self.n += [list((R @ n).normalized()) for n in nrm]
        self.uv += [list(x) for x in uvs]
        k = 0
        for p in polys:
            for tri in ((p[0], p[1], p[2]),) + (((p[0], p[2], p[3]),) if len(p) == 4 else ()):
                a, b_, c = (Vector(pts[i]) for i in tri)
                if (b_ - a).cross(c - a).dot(Vector(out)) < 0:
                    tri = (tri[0], tri[2], tri[1])
                self.t.append([off + i for i in tri])
                k += 1
        return k

    def json(self):
        return {"v": self.v, "n": self.n, "uv": self.uv, "t": self.t}


# ------------------------------------------------------------------------------------ render
# the night: a dark blue sky, a cold moon from the camera's upper left
NIGHT_SKY, MOON = ((0.010, 0.014, 0.030), 1.0), ((0.62, 0.72, 1.0), 0.55)
GLOW = 2.2                  # emission strength of additive night meshes (texture x emissive colour)


def night_rig(res, spp, hidden):
    render.rig(res, spp, hidden)
    nt = bpy.context.scene.world.node_tree
    nt.nodes.clear()
    bg, out = nt.nodes.new("ShaderNodeBackground"), nt.nodes.new("ShaderNodeOutputWorld")
    bg.inputs[0].default_value = NIGHT_SKY[0] + (1.0,)
    bg.inputs[1].default_value = NIGHT_SKY[1]
    nt.links.new(bg.outputs[0], out.inputs[0])
    sun = bpy.data.objects["Sun"].data
    sun.color, sun.energy = MOON
    bpy.data.materials["GroundMat"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.05, 0.05, 0.05, 1)


def additive(obj, mesh, texmap):
    """Texture x emissive colour added to what is behind it, seen by the camera only."""
    mat = bpy.data.materials.new(obj.name + ".night")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    M = nt.nodes.new
    out, add, em, tr, lp, mix = (M(t) for t in ("ShaderNodeOutputMaterial", "ShaderNodeAddShader", "ShaderNodeEmission",
                                                "ShaderNodeBsdfTransparent", "ShaderNodeLightPath", "ShaderNodeMixRGB"))
    tex = M("ShaderNodeTexImage")
    name = next(t.lower() for t in mesh.textures)
    tex.image = bpy.data.images.load(texmap[name], check_existing=True)
    mix.blend_type, mix.inputs[0].default_value = "MULTIPLY", 1.0
    mix.inputs[2].default_value = material(mesh.bytes)["emissive"] + (1.0,)
    nt.links.new(tex.outputs[0], mix.inputs[1])
    nt.links.new(mix.outputs[0], em.inputs[0])
    strength = M("ShaderNodeMath")
    strength.operation, strength.inputs[1].default_value = "MULTIPLY", GLOW
    nt.links.new(lp.outputs["Is Camera Ray"], strength.inputs[0])
    nt.links.new(strength.outputs[0], em.inputs[1])
    nt.links.new(tr.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs[0])
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    obj.visible_shadow = False


def render_night(b, w3d_path, prefix, views, res, spp, skeletons, frame, texmap, house=None):
    """The model at night from the building's views: prefix<view>.png."""
    w3d = W3DFile(w3d_path)
    names = N.night_meshes(N.names_of(Workspace(b)), w3d.data)
    scene.import_w3d(w3d_path, skeletons)
    if house:
        render.add_house_colour(*house)
    night_rig(res, spp, tuple(n for n in b.bake_hidden if n not in names))
    for name, mesh in w3d.meshes.items():
        obj = bpy.data.objects.get(name)
        if obj is None or obj.hide_render or not mesh.textures or not all(t.lower() in texmap for t in mesh.textures):
            continue
        if name in names and material(mesh.bytes)["additive"]:
            additive(obj, mesh, texmap)
        else:
            render.game_material(obj, mesh, texmap)
    presets = render.views_for(b, bpy.data.objects[frame or b.target])
    for v in views:
        c = render.camera(v, *presets[v])
        sc = bpy.context.scene
        sc.camera, sc.render.filepath = c, prefix + v + ".png"
        bpy.ops.render.render(write_still=True)


# ------------------------------------------------------------------------------------ checks
def checks(b, ws, r):
    """Night lights: shipped night triangles on our surface's visible side, the faction's texture
    only (healthy and derived models; the lifecycle models: texture and stand-ins)."""
    lk = N.look(b)
    names = N.names_of(ws)
    if lk is None:
        return
    r.section("night lights (sagekit/nightlights.py): %s, tolerance %.2f" % (lk.texture, lk.tolerance))
    foreign = []
    for p in N.shipped_models(ws):
        for n, m in W3DFile(p).meshes.items():
            foreign += ["%s %s %s" % (os.path.basename(p), n, t) for t in m.textures
                        if N.NIGHT_TEXTURE.search(t) and t.lower() != lk.texture.lower()]
    r.check("no shipped mesh draws another night sheet", not foreign, "; ".join(foreign[:6]))
    uses = N.uses(ws)
    if uses:
        from ..formats.assetcache import AssetCache
        from ..formats.textures import dds_info, full_chain
        path = ws.shipped_texture(lk.texture, ".dds")
        i = dds_info(path) if os.path.exists(path) else None
        r.check("%s shipped: %d, DXT1, full mips" % (lk.texture, lk.size),
                i is not None and (i["width"], i["fourcc"], i["mips"]) == (lk.size, "DXT1", full_chain(lk.size)),
                "missing" if i is None else "%dx%d %s %d mips" % (i["width"], i["height"], i["fourcc"], i["mips"]))
        caches = [AssetCache(c) for c in ws.caches()]
        r.check("%s registered in the caches" % lk.texture, any(c.has_texture(lk.texture) for c in caches), "")
        for model, obj in uses:
            dep = next((d for d in (c.dependencies(model, obj) for c in caches) if d is not None), None)
            if dep is not None:
                r.check("%s %s depends on %s" % (model, obj, lk.texture.lower()), lk.texture.lower() in dep, str(dep))
    models = [(b.source, ws.shipped_model)] + [(m, ws.out(N.model_member(b, m))) for m in ws.derived + ws.lifecycle]
    for model, path in models:
        if not os.path.exists(path):
            continue
        data = open(path, "rb").read()
        found = N.night_meshes(names, data)
        if not found:
            continue
        f = W3DFile(data)
        wrong = [n for n in found if [t.lower() for t in f.meshes[n].textures] != [lk.texture.lower()]]
        r.check("%s: night meshes draw %s only (%s)" % (model, lk.texture, ", ".join(found)), not wrong, str(wrong))
        if model in ws.lifecycle:
            continue                                    # posed models: carry() kept only lights on kept faces
        far, back, hidden, total = on_surface(ws, data, found, lk.tolerance, N.glow_cards(b, model))
        r.check("%s: %d night triangles within %.2f of our surface" % (model, total, lk.tolerance), not far,
                "%d off it, e.g. at %s" % (len(far), far[:3]) if far else "")
        r.check("%s: night triangles face out of the surface they lie on" % model, not back,
                "%d face into it, e.g. at %s" % (len(back), back[:3]) if back else "")
        r.info("%s: night triangles hidden inside frames and mullions" % model, "%d of %d" % (hidden, total))


def on_surface(ws, data, found, tol, cards=()):
    """([centre of each triangle with a corner farther than tol from the model's other meshes],
    [... facing into the surface nearest its centre], triangles whose centre is inside a solid - the
    first face straight out in front of it faces away: the part of a pane a frame or a mullion
    hides, not wrong - and all non-stand-in night triangles), in model space. cards: the glow
    cards' triangles (Light.glow, model space): free-hanging, each held by its centre, which must
    lie within the card's own span of our surface (it hangs round a lantern of ours)."""
    from mathutils.kdtree import KDTree
    kd = KDTree(max(1, 3 * len(cards)))
    for i, p in enumerate(q for c in cards for q in c):
        kd.insert(p, i)
    kd.balance()
    from ..formats.w3dframes import apply, mesh_frames

    def skl(name):
        p = os.path.join(ws.src, name)
        return open(p, "rb").read() if os.path.exists(p) else None
    f, frames = W3DFile(data), mesh_frames(data, skl)
    verts, polys = [], []
    for n, m in f.meshes.items():
        if n in found or m.skinned or n in ws.b.bake_hidden:
            continue
        off = len(verts)
        verts += [Vector(apply(frames[n], v)) for v in m.verts]
        polys += [tuple(off + i for i in t) for t in m.tris]
    bvh = BVHTree.FromPolygons(verts, polys)
    far, back, hidden, total = [], [], 0, 0
    for n in found:
        m = f.meshes[n]
        if len(m.tris) <= 1 or m.skinned:
            continue                                    # a stand-in
        for t in m.tris:                                # every corner: a pane spanning an opening
            P = [Vector(apply(frames[n], m.verts[i])) for i in t]       # is pinned at its rim
            fn = (P[1] - P[0]).cross(P[2] - P[0]).normalized()
            total += 1
            near, c = [bvh.find_nearest(p) for p in P], sum(P, Vector()) / 3
            at = tuple(round(x, 1) for x in c)
            if cards and all(kd.find(p)[2] < 0.01 for p in P):          # a glow card: by its centre
                span = max((a - b).length for a in P for b in P)
                hit = bvh.find_nearest(c)
                if hit[0] is None or hit[3] > span:
                    far.append(at)
                continue
            if any(x[0] is None or x[3] > tol for x in near):
                far.append(at)
                continue
            loc, sn, _, _ = bvh.find_nearest(c)
            _, hn, _, _ = bvh.ray_cast(c + fn * 1e-3, fn, 50.0)
            if fn.dot(sn) < -0.2:
                back.append(at)                         # facing into its surface
            elif hn is not None and hn.dot(fn) > 0:
                hidden += 1                             # inside a frame or a mullion: not seen
    return far, back, hidden, total
