"""The fire standard's checks and marker renders (the standard itself: sagekit/fire.py).

checks(b, ws, r) - in the check suite (sagekit/blender/checks_suite.py), for a recipe with
fire_points only: the rig (its bones where the points are, no meshes, a box that collides with
nothing, filed in the build's asset.dat copy), each fire Draw module (EA's states mirrored in EA's
order, fire exactly where our intact body stands, none in rubble, construction or placement, the
rest of the INI as the other edits leave it), and every particle system defined by the game.

render(step) - after the render step: EA's healthy render with any fire bones EA's model has,
beside ours with a numbered marker per fire point (renders/fire/compare_<view>.png). Blender
cannot draw the game's particles; the markers show where they start. They are drawn over
everything (a point behind a wall still shows).
"""
import math
import os
import struct

from . import paths
from .fire import (KINDS, NO_FIRE, block, game_systems, mirror, plan, points, rig_file, rig_member, rig_name)
from .formats.ini import DRAW_RE, OBJECT_RE, apply_ops, strip
from .formats.w3d import BOX, W3DFile, chunks
from .taxonomy import states_of

COLOURS = {"chimney": "#ff5a1f", "furnace": "#ff2d2d", "forge": "#ffb000", "hearth": "#ff8c00",
           "crucible": "#ffe14a", "brazier": "#ff6ec7", "grate": "#c0ff3a", "embers": "#6ae0ff",
           "pyre": "#ff0080", "smoke": "#b0b0b0", "witchfire": "#7dff3a", "witchflame": "#3aff9a", "plume": "#6a6a6a",
           "coldfire": "#9fe8ff", "coldflame": "#4fb0ff"}
AUTO_VIEWS = {"rts": (2.2, 50, -38, 50), "close": (1.3, 24, -30, 45), "ingame": (5.0, 53, -62, 50)}  # blender/render.py's
EA_FIRE_BONES = ("FIRE", "SMOKE", "EMBER", "GLOW", "CHIMNEY", "FLAME", "TORCH")


def _ours(text, obj, tag):
    """[(flags, model, [(bone, system)])] of our Draw module `tag` in object `obj`, and its
    (first, last) line indices; None if absent."""
    lines, cur, depth, at, states, st = text.splitlines(), None, 0, None, [], None
    for i, raw in enumerate(lines):
        line = strip(raw)
        m = OBJECT_RE.match(line)
        if m and not raw[:1].isspace():
            cur = m.group(2)
            continue
        if not line:
            continue
        if not depth:
            m = DRAW_RE.match(line)
            if m and cur == obj and m.group(2) == tag:
                depth, at = 1, i
            continue
        key, _, val = (x.strip() for x in line.partition("="))
        if line.lower() == "end":
            depth -= 1
            if depth == 0:
                return states, (at, i)
        elif depth == 1 and key.lower() == "modelconditionstate":
            depth += 1
            st = (tuple(f for f in val.upper().split() if f != "NONE"), [None], [])
            states.append(st)
        elif depth == 2 and key.lower() == "model":
            st[1][0] = val
        elif depth == 2 and key.lower() == "particlesysbone":
            p = val.split()
            st[2].append((p[0].upper(), p[1]))
    return None


def _box_attributes(data):
    return [struct.unpack_from("<I", data, o + 12)[0] for t, o, s, _ in chunks(data, 0, len(data)) if t == BOX]


def checks(b, ws, r):
    pts = points(b)
    if not pts:
        return
    from .formats.assetcache import AssetCache
    from .formats.w3dframes import mesh_frames, model_box
    from .formats.w3dpose import Skeleton, point
    from .game import Install
    g = Install()
    r.section("fire: the rig %s, its Draw modules, EA's particle systems (sagekit/fire.py)" % rig_name(b))
    path, name = ws.out(rig_member(b)), rig_name(b).upper()
    r.check("fire rig %s shipped" % rig_file(b), os.path.exists(path), path)
    if not os.path.exists(path):
        return
    w = W3DFile(path)
    sk = Skeleton(w.data)
    want = ["ROOTTRANSFORM"] + [bone for bone, _, _ in pts]
    r.check("rig: the root and one bone per fire point (%d)" % len(pts), sk.names == want, " ".join(sk.names))
    off = max(math.dist(point(m, (0, 0, 0)), xyz) for m, (_, xyz, _) in zip(sk.rest[1:], pts)) if len(sk.rest) > 1 else 1e9
    r.check("rig: every bone at its fire point in model space", off < 1e-3, "worst %.5f units off" % off)
    r.check("rig: no meshes, one box, names %s / %s.OB" % (name, name),
            not w.meshes and w.object_names() == ["H:" + name, "B:" + name + ".OB", "L:" + name], str(w.object_names()))
    attrs = _box_attributes(w.data)
    r.check("rig: its box is oriented and collides with nothing", attrs == [1], str([hex(a) for a in attrs]))
    body = W3DFile(ws.shipped_model)
    read = lambda f: g.read(g.model_path(f[:-4]))           # noqa: E731
    frames = mesh_frames(body.data, read)
    boxes = [model_box(m, frames[n]) for n, m in body.meshes.items() if m.verts and not m.skinned]
    lo = [min(bx[i] for bx in boxes) - 3 for i in range(3)]
    hi = [max(bx[i + 3] for bx in boxes) + 3 for i in range(3)]
    away = [bone for bone, xyz, _ in pts if not all(lo[i] <= xyz[i] <= hi[i] for i in range(3))]
    r.check("every fire point on the building (its box + 3 units)", not away, ", ".join(away))

    caches = [AssetCache(p) for p in ws.caches()]
    home = next((c for c in caches if c.has_model(rig_file(b))), None)
    r.check("rig filed in the build's asset.dat copy", home is not None, ", ".join(ws.caches()))
    if home is not None:
        stale = home.stale_entries(path, rig_file(b))
        deps = home.dependencies(rig_file(b), name) or []
        r.check("rig record matches the file; its HLOD depends on H*%s and %s.OB" % (name, name),
                not stale and sorted(deps) == sorted(["h*" + name.lower(), name.lower() + ".ob"]),
                "%d stale; %s" % (len(stale), deps))

    from .fire_systems import names as own_names
    known = game_systems(g)
    used = {s for _, _, kind in pts for s in KINDS[kind]}
    ea = {s for s in used if s.lower() not in own_names()}
    r.check("particle systems defined by the game (%d): %s" % (len(ea), ", ".join(sorted(ea))),
            all(s.lower() in known for s in ea), ", ".join(s for s in ea if s.lower() not in known))
    if used - ea:
        own_checks(g, ws, r, sorted(used - ea), known)
    ops = b.ini_ops(g, ws.variants)
    for d in plan(b, g):
        member = d["file"]
        shipped = open(ws.out(member), encoding="latin-1", newline="").read() if os.path.exists(ws.out(member)) else ""
        found = _ours(shipped, d["object"], d["tag"])
        where = "%s %s" % (d["object"], d["tag"])
        r.check("%s in %s" % (where, member.split("\\")[-1]), found is not None, "")
        if found is None:
            continue
        states, (a, z) = found
        _, ea = mirror(g.read(member).decode("latin-1"), d["object"], d["after"])
        r.check("%s: EA's %d states of %s, in order, NONE first (no default state)" % (where, len(ea), d["after"]),
                [s[0] for s in states] == [f for f, _ in ea] and not states[0][0], "")
        expect = sorted((bone, s) for bone, _, kind in pts for s in KINDS[kind])
        wrong, burning = [], []
        for (flags, model, lines), (_, burns), (_, ea_model) in zip(states, d["states"], ea):
            label = " ".join(flags) or "NONE"
            if burns:
                burning.append(label)
                ok = model[0] == rig_name(b) and sorted((x, y) for x, y in lines) == [(x.upper(), y) for x, y in expect]
            else:
                ok = (model[0] or "").lower() == "none" and not lines
            if not ok or (lines and (states_of(flags) & NO_FIRE or (ea_model or "none").lower() == "none")):
                wrong.append(label)
        r.check("%s: fire where our body stands (%s), none elsewhere" % (where, ", ".join(burning)), not wrong,
                "wrong: " + ", ".join(wrong) if wrong else "")
        rest = [op for op in ops.get(member, []) if op[0] != "fire_draw"]
        lines = shipped.splitlines(keepends=True)
        a = a - 1 if a and not lines[a - 1].strip() else a              # (the blank line before it)
        r.check("%s: the rest of %s as the other edits leave it" % (where, member.split("\\")[-1]),
                "".join(lines[:a] + lines[z + 1:]) == apply_ops(g.read(member).decode("latin-1"), rest), "")
        r.check("%s: as sagekit/fire.py writes it" % where,
                [x.strip() for x in lines[found[1][0]:z + 1]] == [x.strip() for x in block(b, d)], "")
        r.info("%s: particle systems per burning state" % where, "%d on %d bones" % (len(expect), len(pts)))


def own_checks(g, ws, r, used, known):
    """Our own particle systems (sagekit/fire_systems.py): none named like EA's, the shipped
    particle INI EA's with exactly our blocks added after their bases, each defined once."""
    import re

    from .fire_systems import HEAD_RE, MEMBER, OWN, ops
    from .formats.ini import apply_ops
    r.check("our particle systems (%s) not named like any of EA's" % ", ".join(used),
            not any(s.lower() in known for s in OWN), ", ".join(s for s in OWN if s.lower() in known))
    path = ws.out(MEMBER)
    r.check("%s shipped" % MEMBER.split("\\")[-1], os.path.exists(path), path)
    if not os.path.exists(path):
        return
    shipped = open(path, encoding="latin-1", newline="").read()
    r.check("%s: EA's with our %d systems added, nothing else changed" % (MEMBER.split("\\")[-1], len(OWN)),
            shipped == apply_ops(g.read(MEMBER).decode("latin-1"), [ops(g)]), "")
    counts = {n: len(re.findall(HEAD_RE % re.escape(n), shipped, re.I | re.M)) for n in OWN}
    r.check("each of ours defined once", all(c == 1 for c in counts.values()), str(counts))


# ------------------------------------------------------------------------------------ renders
def project(view, p, size):
    """Pixel (x, y) of model-space point p in a render of `size` (w, h) from `view` (target,
    distance, elevation, azimuth, lens), Blender's camera as sagekit/blender/render.py sets it
    (sensor 36 mm across the wider side, -Z at the target, +Y up); None behind the camera."""
    t, dist, elev, azim, lens = view
    e, a = math.radians(elev), math.radians(azim)
    c = [t[i] + dist * v for i, v in enumerate((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))]
    f = _unit([t[i] - c[i] for i in range(3)])
    rt = _unit([f[1], -f[0], 0.0])                             # f x +Z
    up = [rt[1] * f[2] - rt[2] * f[1], rt[2] * f[0] - rt[0] * f[2], rt[0] * f[1] - rt[1] * f[0]]
    d = [p[i] - c[i] for i in range(3)]
    z = sum(d[i] * f[i] for i in range(3))
    if z <= 0:
        return None
    k = lens / 36.0 * max(size)
    return (size[0] / 2 + k * sum(d[i] * rt[i] for i in range(3)) / z, size[1] / 2 - k * sum(d[i] * up[i] for i in range(3)) / z)


def _unit(v):
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def views(b, ws, install):
    if b.views:
        return dict(b.views)
    from .formats.w3dframes import mesh_frames, model_box
    data = open(ws.shipped_model, "rb").read()
    box = model_box(W3DFile(data).meshes[b.target], mesh_frames(data, lambda f: install.read(install.model_path(f[:-4])))[b.target])
    centre = [(box[i] + box[i + 3]) / 2 for i in range(3)]
    diag = math.dist(box[:3], box[3:])
    return {n: (centre, k * diag, e, a, lens) for n, (k, e, a, lens) in AUTO_VIEWS.items()}


def ea_fire_bones(b, install):
    """[(bone, model-space point)] of EA's healthy model's bones named like fire (FIRE, SMOKE, ...)."""
    from .formats.w3dpose import Skeleton, point
    data = install.read(install.model_path(b.source))
    skl = W3DFile(data).skeleton()
    sk = Skeleton(install.read(install.model_path(skl[:-4])) if skl else data)
    return [(n, point(m, (0, 0, 0))) for n, m in zip(sk.names, sk.rest) if any(k in n for k in EA_FIRE_BONES)]


def render(step):
    b, ws, g = step.b, step.ws, step.p.install
    pts = points(b)
    if not pts:
        return
    r, out = ws.path("renders"), ws.path("renders", "fire")
    os.makedirs(out, exist_ok=True)
    ea = ea_fire_bones(b, g)
    for v, view in views(b, ws, g).items():
        new, orig = os.path.join(r, "new_%s.png" % v), os.path.join(r, "orig_%s.png" % v)
        if not (os.path.exists(new) and os.path.exists(orig)):
            continue
        size = tuple(int(x) for x in step.tool(["magick", "identify", "-format", "%w %h", new]).split())
        rad = max(6, size[0] // 180)
        sides = []
        for img, marks, text in ((orig, [(n, xyz, None) for n, xyz in ea], "EA: %d fire bones in %s" % (len(ea), b.source)),
                                 (new, pts, "%s: %d fire points (rig %s)" % (b.id, len(pts), rig_name(b)))):
            cmd = ["magick", img, "-strokewidth", "2"]
            for i, (bone, xyz, kind) in enumerate(marks):
                q = project(view, xyz, size)
                if q is None:
                    continue
                x, y = q
                cmd += ["-fill", COLOURS.get(kind, "#ffffff"), "-stroke", "#000000",
                        "-draw", "circle %.1f,%.1f %.1f,%.1f" % (x, y, x + rad, y),
                        "-stroke", "none", "-fill", "#ffffff", "-font", step.FONT, "-pointsize", str(rad * 2),
                        "-draw", "text %.1f,%.1f '%s'" % (x + rad + 2, y - rad, bone[-2:] if kind else bone)]
            dst = os.path.join(out, "%s_%s.png" % ("orig" if img == orig else "new", v))
            cmd += ["-font", step.FONT, "-gravity", "NorthWest", "-fill", "#f2ead8", "-undercolor", "#0008",
                    "-pointsize", "30", "-annotate", "+16+12", " %s " % text]
            x = 16
            for k in (KINDS if img == new else ()):          # the legend, each kind in its colour
                if any(p[2] == k for p in pts):
                    cmd += ["-gravity", "SouthWest", "-fill", COLOURS[k], "-annotate", "+%d+14" % x, " %s " % k]
                    x += 30 + 17 * len(k)
            cmd.append(dst)
            step.tool(cmd)
            sides.append(dst)
        dst = os.path.join(out, "compare_%s.png" % v)
        step.tool(["magick", sides[0], "-size", "10x%d" % size[1], "xc:#141414", sides[1], "+append", dst])
        print("  " + os.path.relpath(dst, paths.REPO))
