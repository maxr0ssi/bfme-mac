"""Night lights: a faction standard like house colour. Our windows and doors glow at night; EA's
leftover night geometry, placed on EA's old shapes, goes.

The engine side (read from EA's INI and models; nothing here changes it): a building's
BuildingBehavior names the sub-objects shown at night, `NightWindowName = N_Window N_Glow` (also
FireWindowName / GlowWindowName), and scripts hide them by name (CurDrawableHideSubObject("N_WINDOW")
while placing a building). EA's meshes for them are emissive, additive panes on the healthy model
(DBArchRnge_SKN.N_WINDOW on Gondor's gbnightwindows.tga), opaque night-only window frames with
additive glow cards 2.8 units out (DBMine_SKN, DBForge, EBBarracks_SKN: N_WINDOW + N_GLOW on
EXGlow02.tga), and leftovers under names no INI shows (DBArchRnge_D1.WINDOW_N01, Gondor's GBNight).
The engine looks sub-objects up by name and skips a name a model lacks (EA's own catapult, hall and
Erebor-tower expansions name a WINDOW_N01 their models do not have), but every mesh keeps its name
here all the same: the asset cache files each mesh by name, so the names and their order stay EA's.

Our side:
  - the recipe marks its real windows and doors: `night_lights(kit)` -> [Light] (Blender side, the
    design's coordinates; Light.rect / Light.arch), on the target and the `night_surfaces` meshes;
  - the style sets the look: `Style.night = NightLook(...)`: the faction's own texture (painted
    by sagekit/paint/night.py from the look's colour ramp; never another faction's sheet), glow
    offsets and halo size;
  - the pipeline's `night` step (after export; Blender: sagekit/blender/nightlights.py) casts each
    light onto our finished body: a pane a small offset proud of what it lights (flat on a wall or
    a window's panel, draped over rock, in the opening's plane for a doorway into the building) and
    a halo round it (light spilling on the stone), recorded in the target's own coordinates in
    work/night.json. A `base` recipe declares none unless its mesh is `always_shown`: a mesh shown per
    upgrade level would leave the night meshes (shown at every level) glowing in the air before it;
  - `carry(b, model, data)` (the hook) rebuilds a model's night meshes from every chain link's
    lights: panes into the INI's window meshes, halos into its glow meshes (into the window mesh
    when the model has none), in each mesh's bone frame, drawn with EA's additive night material
    (sagekit/formats/w3dlight.py). A night mesh with nothing to show - no lights, a state that
    drops them, a name no INI shows - becomes a stand-in: one tiny triangle on a black texel, so
    every name the INI and scripts use is still there and shows nothing;
  - the texture ships with the building (Ship), gets its asset-cache record, and each night mesh's
    cache object depends on it instead of EA's sheet (cache_ops); the checks hold every night
    triangle to our body's surface (sagekit/blender/nightlights.py); the render step adds night
    views, EA's night look against ours (renders/night/).

Where the hook is called:
  - Fixup (the healthy model) and Derive (the damaged-but-standing models: our body as it is);
  - the lifecycle step (construction / really damaged / rubble models: EA's _D2s of the mine, the
    siege works and the barracks carry N_WINDOW) in sagekit/blender/lifecycle.py, Build.run, right
    after `out = renamed(self.ws, out)` and before the file is written:
        from ..nightlights import carry                 # our night lights (sagekit/nightlights.py)
        out = carry(self.b, e["model"], out, keep=e["kind"] != "construction", pose=self.pose)
    keep=False drops the lights (a building site); `pose` places them at the state's match pose
    and keeps only those still lying on what the state keeps. The lifecycle checks then leave the
    night meshes out of "EA's other meshes byte-identical" (night_meshes(names_of(ws), data)).
"""
import json
import os
import re

from . import paths
from .formats.w3d import W3DFile
from .formats.w3dframes import IDENTITY, apply, compose, inverse, mesh_frames, rotate

NAME_FIELDS = re.compile(r"^\s*(NightWindowName|FireWindowName|GlowWindowName)\s*=\s*(.+)$", re.I)
OBJECT_LINE = re.compile(r"^\s*(Object|ChildObject|ObjectReskin)\s+(\S+)", re.I)
LEFTOVER = re.compile(r"^(N_|WINDOW_N\d)", re.I)      # EA's night naming, whether an INI shows it or not
NIGHT_TEXTURE = re.compile(r"night", re.I)             # every faction's night sheets (GBNight, gbnightwindows)


class NightLook:
    """A faction's night lights. ramp: glow intensity 0..1 -> sRGB (0 must be black: additive);
    emissive: the material's colour (the texture carries the colour, so white); offset: how far a
    pane stands proud of the surface; halo: (across, up) size of the halo against its light's
    outline, halo_offset its distance from the surface; gain: per-motif brightness."""

    def __init__(self, texture, ramp, emissive=(255, 255, 255), size=256, offset=0.06, halo=(1.9, 1.45),
                 halo_offset=0.12, gain=None, cell=0.6, step=0.35):
        self.texture, self.ramp, self.emissive, self.size = texture, ramp, emissive, size
        self.offset, self.halo, self.halo_offset = offset, halo, halo_offset
        self.gain = gain or {}
        self.cell, self.step = cell, step          # drape grid (units); depth jump that ends a piece

    @property
    def tolerance(self):
        """How far from our surface a night triangle may lie (the checks)."""
        return max(self.offset, self.halo_offset) + 0.25


class Light:
    """A window or door of the design: an outline [(u, z)] on the plane through `a` spanned by `t`
    (along the wall) and `up` (default +z; a at z 0 like prism_uz), seen from its outward normal `n`.
    kind: the motif (window, door, slit); halo: a halo round it; reach: how far in front of the
    plane the surface may stand (the rays start there and search twice as deep)."""

    def __init__(self, a, t, n, outline, kind="window", halo=True, reach=4.0, up=(0.0, 0.0, 1.0), name=None):
        self.a, self.t, self.n, self.up = (tuple(float(c) for c in v) for v in (a, t, n, up))
        self.outline = [(float(u), float(z)) for u, z in outline]
        self.kind, self.halo, self.reach, self.name = kind, halo, reach, name

    def point(self, u, z):
        return tuple(self.a[i] + self.t[i] * u + self.up[i] * z for i in range(3))

    @classmethod
    def rect(cls, a, t, n, u0, u1, z0, z1, **kw):
        return cls(a, t, n, [(u0, z0), (u1, z0), (u1, z1), (u0, z1)], **kw)

    @classmethod
    def glow(cls, centre, size=24.0, t=(1.0, 0.0, 0.0), n=(0.0, 0.0, 1.0), name=None):
        """A free-hanging glow: a square card `size` across centred on `centre`, facing `n` (default
        up, as EA's: EA hangs a flat 24-unit card round each warm lantern - the forge's tree, the
        barracks' gable horns, the stable's horn ends, the mallorn's canopy). Not cast onto anything:
        it floats round a lantern of ours (or where EA's card was), drawn additively with the halo
        motif into the model's glow mesh (N_GLOW). The checks hold its centre, not its corners, to
        our surface (within `size`)."""
        up = tuple(n[(i + 1) % 3] * t[(i + 2) % 3] - n[(i + 2) % 3] * t[(i + 1) % 3] for i in range(3))
        h = size / 2
        return cls(centre, t, n, [(-h, -h), (h, -h), (h, h), (-h, h)], kind="glow", halo=False, up=up, name=name)

    @classmethod
    def arch(cls, a, t, n, u, half, z0, spring, apex, **kw):
        """A pointed arch: jambs |u'| <= half from z0 to spring, two arcs meeting at apex."""
        import math
        pts = [(u - half, z0), (u + half, z0)]
        k = 6
        for side in (1, -1):
            arc = [(u + side * half * math.cos(math.pi / 2 * i / k) ** 0.8, spring + (apex - spring) * math.sin(math.pi / 2 * i / k))
                   for i in range(k + 1)]
            pts += arc if side == 1 else arc[::-1][1:]
        return cls(a, t, n, pts[:-1] if pts[-1] == pts[0] else pts, **kw)


# ------------------------------------------------------------------------------------ names
def ini_names(b, install):
    """{MESH NAME: role} for the sub-objects the building's objects show at night ('pane', or
    'halo' for a glow mesh) - from the uncommented Night/Fire/GlowWindowName fields."""
    want = {o.lower() for o in b.objects(install)}
    files = sorted({d.file for ds in b.objects(install).values() for d in ds})
    from .formats.ini import strip
    out = {}
    for f in files:
        obj = None
        for raw in install.read(f).decode("latin-1").splitlines():
            m = OBJECT_LINE.match(raw)
            if m:
                obj = m.group(2).lower()
            m = NAME_FIELDS.match(strip(raw))
            if m and obj in want:
                for n in m.group(2).split():
                    out[n.upper()] = "halo" if "GLOW" in n.upper() else "pane"
    return out


def night_meshes(names, data):
    """{MESH NAME: role, or None for a leftover (a night mesh no INI shows)} in a model."""
    out = {}
    for n in W3DFile(data).meshes:
        if n in names:
            out[n] = names[n]
        elif LEFTOVER.match(n):
            out[n] = None
    return out


def names_of(ws):
    """The INI's night names as the night step recorded them ({} before it ran)."""
    return record(ws).get("names", {})


def day_hidden(b, data):
    """Meshes a day render leaves out: the recipe's bake_hidden and the model's night meshes (the
    game hides them by day; a stand-in or a leftover shows nothing anyway)."""
    from .workspace import Workspace
    return tuple(b.bake_hidden) + tuple(night_meshes(names_of(Workspace(b)), data))


def model_member(b, model):
    """The archive path EA model `model` of the building ships at."""
    from .game import Install
    return Install.model_path(b.shipped_name(model))


def record(ws):
    p = ws.path("work", "night.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def look(b):
    return getattr(b.style, "night", None)


def chain(b):
    out = [b]
    while out[0].base:
        out.insert(0, out[0].base_building())
    return out


# ------------------------------------------------------------------------------------ the hook
def carry(b, model, data, keep=True, pose=None, install=None):
    """`data` (EA model `model` as it is about to ship) with its night meshes rebuilt from our
    design: every chain link's lights, taken from its target's coordinates into this model (the
    healthy frame, or through the derived body's frame for a re-rigged state). keep=False: every
    night mesh a stand-in. pose: the lifecycle step's pose the state model is built at
    (Skeleton.pose(), sagekit/formats/w3dpose.py): the night meshes are placed through their bones
    at that pose and a light stays only where every corner lies on what the posed model keeps (any
    of its other meshes, within the look's tolerance). Idempotent; a faction without a NightLook
    keeps EA's."""
    from .formats.w3dlight import lit_mesh
    from .formats.w3dmesh import replace_meshes
    from .paint.night import BLACK_UV
    from .workspace import Workspace
    lk = look(b)
    if lk is None:
        return data
    found = night_meshes(names_of(Workspace(b)), data)
    if not found:
        return data
    install = install or _install()
    w = W3DFile(data)
    if pose is None:
        frames, surface = mesh_frames(data, lambda f: install.read(install.model_path(f[:-4]))), None
    else:
        frames, surface = posed(data, pose, found)
    tris = {"pane": [], "halo": [], "glow": []}        # model space: (3 points, 3 normals, 3 uvs)
    for x in chain(b) if keep else ():
        rec = record(Workspace(x))
        F = _link_frame(x, model, install)
        for role in tris if F else ():
            g = rec.get(role) or {}
            for ids in g.get("t", []):
                tri = (tuple(apply(F, g["v"][i]) for i in ids), tuple(rotate(F[0], g["n"][i]) for i in ids),
                       tuple(tuple(g["uv"][i]) for i in ids))
                if surface is None or (_near(_centre(tri[0]), surface, _span(tri[0])) if role == "glow" else
                                       all(_near(p, surface, lk.tolerance) for p in tri[0])):
                    tris[role].append(tri)
    tris["halo"] += tris.pop("glow")                   # glow cards: into the glow meshes, as EA's
    if not any(r == "halo" for r in found.values()):
        tris["pane"] += tris.pop("halo")               # EA's archery range: one mesh for both
    new = {}
    for mesh, role in found.items():
        ea = w.meshes[mesh]
        got = tris.get(role) or [] if role and not ea.skinned else []
        back = inverse(frames.get(mesh, IDENTITY))
        if got:
            verts, normals, uvs, faces = [], [], [], []
            for pts, nrm, uv in got:
                faces.append(tuple(range(len(verts), len(verts) + 3)))
                verts += [apply(back, p) for p in pts]
                normals += [rotate(back[0], q) for q in nrm]
                uvs += list(uv)
        else:                                          # a stand-in: shows nothing, keeps the name
            p = ea.verts[0] if ea.verts else (0.0, 0.0, 0.0)
            verts = [p, (p[0] + 0.05, p[1], p[2]), (p[0], p[1], p[2] + 0.05)]
            normals, uvs, faces = [(0.0, -1.0, 0.0)] * 3, [BLACK_UV] * 3, [(0, 1, 2)]
        new[mesh] = lit_mesh(mesh, ea.container, verts, normals, uvs, faces, lk.texture, lk.emissive, like=ea.bytes)
    out = replace_meshes(data, new)
    if W3DFile(out).object_names() != w.object_names():
        raise ValueError("%s: night meshes changed the object names" % model)
    return out


def _centre(pts):
    return tuple(sum(p[i] for p in pts) / len(pts) for i in range(3))


def _span(pts):
    import math
    return max(math.dist(p, q) for p in pts for q in pts)


def glow_cards(b, model, install=None):
    """[[corner points]] of every chain link's glow-card triangles in `model`'s model space (as
    carry places them in the healthy and derived models): the checks hold these to our surface by
    their centre, not their corners."""
    from .workspace import Workspace
    install = install or _install()
    out = []
    for x in chain(b):
        g = record(Workspace(x)).get("glow") or {}
        F = _link_frame(x, model, install) if g.get("t") else None
        out += [[apply(F, g["v"][i]) for i in ids] for ids in g.get("t", [])] if F else []
    return out


def posed(data, pose, found):
    """({mesh: model-space frame at the pose}, [(p0, p1, p2)] triangles of the other meshes the
    pose shows) for a lifecycle model."""
    from .formats import w3dpose as P
    _, _, bones = P.hlod(data)
    world, vis = pose
    frames = {}
    for n in W3DFile(data).meshes:
        m = world[bones.get(n, 0)]
        frames[n] = ((tuple(m[0:3]), tuple(m[4:7]), tuple(m[8:11])), (m[3], m[7], m[11]))
    surface = []
    for n, mesh in W3DFile(data).meshes.items():
        if n in found:
            continue
        at = P.mesh_frames(mesh, bones, None, pose)
        pts = [P.point(M, v) if shown else None for (M, shown), v in zip(at, mesh.verts)]
        surface += [tuple(pts[i] for i in t) for t in mesh.tris if all(pts[i] for i in t)]
    return frames, surface


def _install():
    from .game import Install
    return Install()


def _link_frame(x, model, install):
    """Frame taking link x's target coordinates into `model`'s model space: the healthy one, or
    for a derived model through the mesh that carries x's body there (None: x's body is not in it)."""
    read = lambda f: install.read(install.model_path(f[:-4]))           # noqa: E731
    healthy = install.read(install.model_path(x.source))
    hf = mesh_frames(healthy, read)[x.target]
    if model.lower() == x.source.lower():
        return hf
    bodies = x.derived_bodies(install)
    key = next((m for m in bodies if m.lower() == model.lower()), None)
    if key is None:
        return hf                                      # a lifecycle model: its pieces stand as healthy
    mesh = bodies[key]
    ea = install.read(install.model_path(key))
    M = x.bodies_in(install, key).get(mesh)
    return compose(mesh_frames(ea, read)[mesh], M) if M else None


def _near(p, surface, tol):
    """Whether point p lies within tol of any of the triangles (coarse box test, then exact)."""
    for a, b, c in surface:
        if any(p[i] < min(a[i], b[i], c[i]) - tol or p[i] > max(a[i], b[i], c[i]) + tol for i in range(3)):
            continue
        if _point_tri(p, a, b, c) <= tol:
            return True
    return False


def _point_tri(p, a, b, c):
    """Distance from p to triangle abc (Ericson, Real-Time Collision Detection 5.1.5)."""
    import math

    def sub(x, y):
        return [x[i] - y[i] for i in range(3)]

    def dot(x, y):
        return sum(x[i] * y[i] for i in range(3))
    ab, ac, ap = sub(b, a), sub(c, a), sub(p, a)
    d1, d2 = dot(ab, ap), dot(ac, ap)
    if d1 <= 0 and d2 <= 0:
        return math.dist(p, a)
    bp = sub(p, b)
    d3, d4 = dot(ab, bp), dot(ac, bp)
    if d3 >= 0 and d4 <= d3:
        return math.dist(p, b)
    vc = d1 * d4 - d3 * d2
    if vc <= 0 <= d1 and d3 <= 0:
        v = d1 / (d1 - d3)
        return math.dist(p, [a[i] + v * ab[i] for i in range(3)])
    cp = sub(p, c)
    d5, d6 = dot(ab, cp), dot(ac, cp)
    if d6 >= 0 and d5 <= d6:
        return math.dist(p, c)
    vb = d5 * d2 - d1 * d6
    if vb <= 0 <= d2 and d6 <= 0:
        w = d2 / (d2 - d6)
        return math.dist(p, [a[i] + w * ac[i] for i in range(3)])
    va = d3 * d6 - d5 * d4
    if va <= 0 and d4 - d3 >= 0 and d5 - d6 >= 0:
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        return math.dist(p, [b[i] + w * (c[i] - b[i]) for i in range(3)])
    den = 1 / (va + vb + vc)
    v, w = vb * den, vc * den
    return math.dist(p, [a[i] + ab[i] * v + ac[i] * w for i in range(3)])


# ------------------------------------------------------------------------------------ texture
def faction_texture(b):
    """The faction's night texture, painted into build/assets/<faction>/_night/ (redone when the
    style or the painter is newer); None without a NightLook."""
    import sys
    lk = look(b)
    if lk is None:
        return None
    out = os.path.join(paths.BUILD, b.style.faction, "_night", lk.texture[:-4].lower() + ".dds")
    deps = [sys.modules[type(b.style).__module__].__file__, os.path.join(paths.REPO, "sagekit", "paint", "night.py")]
    if not os.path.exists(out) or os.path.getmtime(out) < max(os.path.getmtime(p) for p in deps):
        from .paint.night import paint
        paint(lk, out)
        print("  painted %s" % os.path.relpath(out, paths.REPO))
    return out


def shipped_models(ws):
    root, out = ws.path("out", "art", "w3d"), []
    for d, _, names in os.walk(root):
        out += [os.path.join(d, f) for f in sorted(names) if f.lower().endswith(".w3d")]
    return out


def uses(ws):
    """[(model file, CONTAINER.MESH)] of the shipped night meshes drawing the faction's texture."""
    lk = look(ws.b)
    if lk is None:
        return []
    out = []
    for p in shipped_models(ws):
        for n, m in W3DFile(p).meshes.items():
            if lk.texture.lower() in (t.lower() for t in m.textures):
                out.append((os.path.basename(p).lower(), "%s.%s" % (m.container.upper(), n)))
    return out


def ship(ws):
    """Ship step hook: [(texture, ".dds")] to ship (placed in work/tex/), if any model draws it."""
    import shutil
    if not uses(ws):
        return []
    lk = look(ws.b)
    shutil.copy2(faction_texture(ws.b), ws.tex(lk.texture[:-4].lower() + ".dds"))
    return [(lk.texture, ".dds")]


def texture_map(ws):
    """{night texture: file} for the renders: the shipped copy, else the faction's painted one."""
    lk = look(ws.b)
    if lk is None:
        return {}
    p = ws.shipped_texture(lk.texture, ".dds")
    p = p if os.path.exists(p) else os.path.join(paths.BUILD, ws.b.style.faction, "_night", lk.texture[:-4].lower() + ".dds")
    return {lk.texture.lower(): p} if os.path.exists(p) else {}


def cache_ops(b):
    """Building.cache_ops entries: the texture's record (copied from a sheet the night meshes drew)
    and each shipped night mesh's object depending on it instead of the colour sheets its EA record
    lists (EA's records do not always name the sheet the mesh draws: EBBarracks_SKN.N_WINDOW draws
    dbminea.tga, its record lists dbfortress1.tga). Normal maps stay listed: they carry no colour."""
    from .game import Install
    from .workspace import Workspace
    ws = Workspace(b)
    lk, found = look(b), uses(ws)
    if not found:
        return []
    g = Install()
    ea_of = {b.shipped_name(m).lower() + ".w3d": m for m in [b.source] + ws.derived + ws.lifecycle}
    mine, ops = lk.texture.lower(), []
    for f, obj in found:
        m = ea_of.get(f)
        ea = W3DFile(g.read(g.model_path(m))).meshes.get(obj.split(".")[-1]) if m and g.has_model(m) else None
        dep = next((d for d in (c.dependencies(f, obj) for c in g.asset_caches().values()) if d is not None), None)
        sheets = [t.lower() for t in (dep or [])] or [t.lower() for t in (ea.textures if ea else [])]
        sheets = [t for t in sheets if t != mine and "_nrm" not in t and t.endswith((".tga", ".dds"))]
        if sheets and not ops:
            ops.append(("texture", mine, sheets[0], None, None))
        ops += [("texture", mine, t, f, obj) for t in sheets] if dep else []
    return ops


# ------------------------------------------------------------------------------------ the step
def run(step):
    """The pipeline's night step (after export): the INI's night names, the faction texture, and
    the recipe's lights cast onto our finished body (Blender) -> work/night.json."""
    b, ws, g = step.b, step.ws, step.p.install
    names = ini_names(b, g)
    rec = {"names": names, "lights": [], "pane": {}, "halo": {}}
    declared = type(b).night_lights is not _base_night_lights()
    if declared and b.per_level:                       # the night meshes show at every upgrade level
        from .pipeline import StepFailed
        raise StepFailed("%s: a `base` recipe's mesh is shown per upgrade level, the night meshes at every "
                         "level - its lights would glow in the air before the upgrade; light the base's body "
                         "(or set always_shown for a mesh drawn at every level)" % b.id)
    if look(b) is None:
        print("  %s has no NightLook: EA's night meshes stay" % b.style.faction)
    elif declared:
        faction_texture(b)
        with open(ws.path("work", "night.json"), "w") as fh:
            json.dump(rec, fh)                         # the job reads the names
        step.blender("night", blend=ws.stage("geometry"))
        rec = record(ws)
        for x in rec["lights"]:
            print("  %-14s %-6s pane %2d triangles (%s), halo %3d (%d cells off the surface)" % (
                x["name"], x["kind"], x["pane"], x["how"], x["halo"], x["dropped"]))
    else:
        faction_texture(b)
        print("  no lights declared (night meshes of this link: stand-ins, unless a base link lights them)")
    rec["names"] = names
    with open(ws.path("work", "night.json"), "w") as fh:
        json.dump(rec, fh)
    print("  night sub-objects (INI): %s" % (", ".join("%s (%s)" % kv for kv in sorted(names.items())) or "none"))


def _base_night_lights():
    from .building import Building
    return Building.night_lights


# ------------------------------------------------------------------------------------ renders
def render(step, views=None, res="1400x960", spp="48"):
    """Night views of the healthy and derived models with night meshes: EA's (as the installed
    faction draws it: recoloured sheets, EA's night meshes) against ours ->
    renders/night/compare_[<model>_]<view>.png."""
    from .formats.w3d import W3DFile as F
    b, ws, g = step.b, step.ws, step.p.install
    names = names_of(ws)
    views = views or ",".join(v for v in (b.views or ("rts", "close")) if v in ("rts", "close", "ingame")) or "rts,close"
    r = ws.path("renders", "night")
    os.makedirs(r, exist_ok=True)
    pairs = [("", b.source, ws.shipped_model, b.target)] + [
        (m.lower() + "_", m, ws.out(g.model_path(b.shipped_name(m))), body) for m, body in ws.derived_bodies.items() if body]
    for tag, model, ours, body in pairs:
        ea = ws.path("work", "ref", "night_" + model.lower() + ".w3d")
        os.makedirs(os.path.dirname(ea), exist_ok=True)
        with open(ea, "wb") as fh:
            fh.write(g.read(g.model_path(model)))
        if not os.path.exists(ours) or not (night_meshes(names, F(ea).data) or night_meshes(names, F(ours).data)):
            continue
        for who, path in (("orig", ea), ("new", ours)):
            step.blender("night_render", log_as="night_%s%s" % (tag, who), w3d=path, prefix=os.path.join(r, who + "_" + tag),
                         views=views, res=res, spp=spp, frame=body, **step.references(path, recoloured=True))
        for v in views.split(","):
            pair = []
            for who, text in (("orig", "EA at night (as installed)"), ("new", "%s at night" % b.id)):
                src, dst = os.path.join(r, "%s_%s%s.png" % (who, tag, v)), os.path.join(r, "_%s_%s%s.png" % (who, tag, v))
                step.tool(["magick", src, "-font", step.FONT, "-gravity", "NorthWest", "-fill", "#f2ead8", "-undercolor",
                           "#0008", "-pointsize", "30", "-annotate", "+16+12", " %s%s " % (text, " - " + model if tag else ""), dst])
                pair.append(dst)
            out = os.path.join(r, "compare_%s%s.png" % (tag, v))
            step.tool(["magick", pair[0], "-size", "10x%s" % res.split("x")[1], "xc:#141414", pair[1], "+append", out])
            print("  " + os.path.relpath(out, paths.REPO))
