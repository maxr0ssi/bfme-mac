"""HUD icon renders (sagekit/icons): every shot of every model in one Blender process.

Each model is drawn as the colour renders draw it (sagekit/blender/render.py: the textures its
W3D bytes name, the normal maps, the house colour) on a ground of EA's terrain under the same
sun, with a transparent sky: sagekit/icons/grade.py lays the parchment or the sky behind it.
A shot frames part of the model's box (`focus`) from a direction, at the distance where its
projection fills `fill` of the frame, its centre moved to `at` by lens shift.
"""
import json
import math

import bpy
import mathutils
import numpy as np

from ..formats.w3d import W3DFile
from . import render, scene


def ground(path, tile):
    """The rig's ground plane painted with a terrain texture, `tile` units a repeat, fading out with
    the distance from a point (set per shot by `fade`): EA's ground melts into the parchment sky
    instead of meeting it at a hard horizon."""
    g = bpy.data.objects["Ground"]
    mat = g.data.materials[0]
    nt = mat.node_tree
    N = nt.nodes.new
    bsdf = nt.nodes["Principled BSDF"]
    coord, mapping, tex = N("ShaderNodeTexCoord"), N("ShaderNodeMapping"), N("ShaderNodeTexImage")
    mapping.inputs["Scale"].default_value = (1.0 / tile, 1.0 / tile, 1.0)
    tex.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(coord.outputs["Object"], mapping.inputs[0])
    nt.links.new(mapping.outputs[0], tex.inputs[0])
    nt.links.new(tex.outputs[0], bsdf.inputs["Base Color"])
    sub, length, ramp = N("ShaderNodeVectorMath"), N("ShaderNodeVectorMath"), N("ShaderNodeMapRange")
    sub.name, ramp.name = "FadeCentre", "FadeRange"
    sub.operation, length.operation = "SUBTRACT", "LENGTH"
    nt.links.new(coord.outputs["Object"], sub.inputs[0])
    nt.links.new(sub.outputs[0], length.inputs[0])
    nt.links.new(length.outputs["Value"], ramp.inputs["Value"])
    ramp.inputs["To Min"].default_value, ramp.inputs["To Max"].default_value = 1.0, 0.0
    ramp.interpolation_type = "SMOOTHSTEP"
    nt.links.new(ramp.outputs["Result"], bsdf.inputs["Alpha"])
    fade((0, 0, 0), 1e5, 2e5)


def fade(centre, start, end):
    """The ground opaque within `start` of `centre` (on the ground), gone by `end`."""
    nt = bpy.data.objects["Ground"].data.materials[0].node_tree
    nt.nodes["FadeCentre"].inputs[1].default_value = (float(centre[0]), float(centre[1]), -0.05)
    ramp = nt.nodes["FadeRange"]
    ramp.inputs["From Min"].default_value, ramp.inputs["From Max"].default_value = float(start), float(end)


def points(names):
    """World-space vertices (posed) of the named mesh objects, (n, 3)."""
    dg = bpy.context.evaluated_depsgraph_get()
    out = []
    for n in names:
        o = bpy.data.objects.get(n)
        if o is None or o.type != "MESH":
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        co = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", co)
        m = np.array(ev.matrix_world, np.float32)
        co = co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
        out.append(co)
        ev.to_mesh_clear()
    if not out:
        raise SystemExit("no meshes to frame among %s" % ", ".join(names))
    return np.concatenate(out)


TALL = 1.4                          # a portrait whose silhouette stands 1.4 times its width is a tower
BODY, FOOT, TIP = 0.84, 0.92, -0.04 # a tower's body as tall as 0.84 of the frame, its foot 0.92 down, as
                                    # EA's; its spire's tip may run into the burnt edge, just past the top
SPIRE = 0.3                         # a spire: the rows at a tower's top thinner than 0.3 of its widest
FADE = (1.15, 2.6)                  # the ground fades from 1.15 to 2.6 times the building's reach
STAND, BASE = 0.05, 0.25            # of the height: what stands above the ground; the foot of the walls


def silhouette(pts):
    """A portrait's building as it rises from the ground: the vertices higher than STAND of its
    height (bibs, decals, rubble and the bottom steps lie flat and leave the frame to the ground),
    those of the lowest quarter also dropped to the ground, where its walls meet it."""
    z0, h = float(pts[:, 2].min()), float(np.ptp(pts[:, 2]))
    up = pts[pts[:, 2] > z0 + STAND * h]
    if len(up) < 8:
        return pts
    foot = up[up[:, 2] < z0 + BASE * h].copy()
    foot[:, 2] = z0
    return np.concatenate([up, foot])


def tower_body(p):
    """Which of a tower's projected points are its body: those below the run of rows at its top
    thinner than SPIRE of its widest row (the spire)."""
    y0, h = p[:, 1].min(), max(float(np.ptp(p[:, 1])), 1e-9)
    rows = np.minimum(((p[:, 1] - y0) / h * 40).astype(int), 39)
    width = np.zeros(40)
    for r in np.unique(rows):
        width[r] = np.ptp(p[rows == r, 0])
    return rows <= np.nonzero(width >= SPIRE * width.max())[0].max()


def frame(shot, pts):
    """A camera framing the focus part of `pts` as the shot says: a portrait by its silhouette, a
    tower (tall, framed whole) as EA's: its body BODY tall, its foot at FOOT; also the framed part's
    centre and how far the building reaches from it on the ground."""
    pts = pts[pts[:, 2] >= -0.5]                # what stands above the ground (no buried upgrade levels)
    portrait = shot.get("kind") == "portrait"
    if portrait:
        pts = silhouette(pts)
    lo, hi = pts.min(0), pts.max(0)
    f = np.array(shot["focus"], np.float32)
    flo, fhi = lo + (hi - lo) * f[:, 0], lo + (hi - lo) * f[:, 1]
    inside = np.all((pts >= flo - 1e-3) & (pts <= fhi + 1e-3), 1)
    sel = pts[inside] if inside.sum() >= 8 else np.array([[x, y, z] for x in (flo[0], fhi[0])
                                                          for y in (flo[1], fhi[1]) for z in (flo[2], fhi[2])])
    centre = (sel.min(0) + sel.max(0)) / 2
    e, a = math.radians(shot["elev"]), math.radians(shot["azim"])
    d = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
    fx = shot["lens"] / 36.0                    # sensor 36 mm, square frame
    fwd = -d
    right = np.cross(fwd, [0, 0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)

    def project(dist):
        rel = sel - (centre + d * dist)
        z = rel @ fwd
        if np.any(z <= 0.05):
            return None
        return np.stack([rel @ right / z * fx + 0.5, rel @ up / z * fx + 0.5], 1)

    fill, at = shot["fill"], shot["at"]
    probe = project(10.0 * float(np.ptp(sel, 0).max()) + 1.0)
    span = np.ptp(probe, 0)
    whole = not shot["frame"] and np.all(f == [[0, 1], [0, 1], [0, 1]])
    tall = portrait and whole and span[1] > TALL * span[0]     # a part the table picks keeps its fill
    body = tower_body(probe) if tall else None

    def over(p):
        """Too big: the larger side past `fill`; a tower's body past BODY or its spire past TIP."""
        if not tall:
            return np.ptp(p, 0).max() > fill
        b, foot = p[body], p[:, 1].min()
        return max(b[:, 1].max() - foot, np.ptp(b[:, 0])) > BODY or p[:, 1].max() - foot > FOOT - TIP

    near, far = 0.0, 1.0
    while project(far) is None or over(project(far)):
        far *= 2
    for _ in range(40):
        mid = (near + far) / 2
        p = project(mid)
        if p is None or over(p):
            near = mid
        else:
            far = mid
    p = project(far)
    c = (p.min(0) + p.max(0)) / 2
    cam = render.camera("IconCam", tuple(centre), far, shot["elev"], shot["azim"], shot["lens"])
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.sensor_width = 36.0
    cam.data.shift_x = float(c[0] - at[0])
    cam.data.shift_y = float(p[:, 1].min() - (1.0 - FOOT) if tall else c[1] - (1.0 - at[1]))
    cam.data.clip_start = 0.1
    reach = max(float(np.max(np.hypot(pts[:, 0] - centre[0], pts[:, 1] - centre[1]))),
                0.6 * float(np.ptp(pts[:, 2])))       # a tower stands on ground, not a dot of it
    return cam, centre, reach


def purge():
    """Everything out of the file: the importer reuses data of a model imported before by name
    (DBUndrMine after the hearth failed on a material index)."""
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.armatures, bpy.data.actions,
                 bpy.data.cameras, bpy.data.lights):
        for d in list(coll):
            coll.remove(d)


def dress(path, texmap, before):
    """Game materials on the meshes `path` added to the scene since `before` (a second model's
    copies of a name carry Blender's .001 suffix)."""
    w3d = W3DFile(path)
    for o in set(bpy.data.objects) - before:
        mesh = w3d.meshes.get(base(o)) if o.type == "MESH" else None
        if mesh is not None and not o.hide_render and mesh.textures and all(t.lower() in texmap for t in mesh.textures):
            render.game_material(o, mesh, texmap)


def place(objs, offset, rotz):
    """Turn a second model's objects `rotz` degrees about the origin and move them."""
    m = mathutils.Matrix.Translation(offset) @ mathutils.Matrix.Rotation(math.radians(rotz), 4, "Z")
    roots = [o for o in objs if o.parent not in objs]
    world = {o: m @ o.matrix_world for o in roots}
    for o, w in world.items():
        o.matrix_world = w


def base(o):
    """An object's name as the model names it (before our ~ tag and Blender's .001)."""
    return o.name.split("~")[0].split(".")[0]


def set_aside(k):
    """Tag every object's name, so the next import's names are free: the importer finds a mesh's
    armature and the house step its cloth by name, and a second copy of a model (the wall segments
    either side of a hub) would hang on the first one's."""
    for o in bpy.data.objects:
        if "~" not in o.name:
            o.name = "%s~%d" % (o.name, k)


def model(item):
    from .. import registry
    for bid in [item["building"]] + [x["building"] for x in item["extras"]]:
        registry.load(bid)                  # a recipe may mend the importer for its model (the Undermine)
    purge()
    scene.import_w3d(item["w3d"], item["skeletons"])
    if item.get("house"):
        render.add_house_colour(*item["house"])
    own = [o for o in bpy.data.objects if o.type == "MESH"]
    dress(item["w3d"], item["texmap"], set())
    for o in own:
        if o.name in item["hidden"]:
            o.hide_render = True
    for k, x in enumerate(item["extras"]):  # neighbours EA's portrait shows (the walls beside a hub)
        set_aside(k)
        before = set(bpy.data.objects)
        scene.add_w3d(x["w3d"], x["skeletons"])
        if x.get("house"):
            render.add_house_colour(*x["house"])
        new = set(bpy.data.objects) - before
        for o in new:
            if o.type == "MESH" and o.name in x["hidden"]:
                o.hide_render = True
        dress(x["w3d"], x["texmap"], before)
        place(new, x["offset"], x["rotz"])
    first = item["shots"][0]
    render.rig(tuple(first["res"]), first["samples"], ())
    ground(item["ground"], item["tile"])
    sc = bpy.context.scene
    sc.render.film_transparent = True
    sc.render.image_settings.color_mode = "RGBA"
    g = bpy.data.objects["Ground"]
    shown = {o: o.hide_render for o in bpy.data.objects if o.type == "MESH" and o is not g}
    for shot in item["shots"]:
        for o, hide in shown.items():
            o.hide_render = hide or base(o) in shot["hide"]
        g.hide_render = not shot["ground"]
        names = [o.name for o in own if not o.hide_render and (not shot["frame"] or base(o) in shot["frame"])]
        cam, centre, reach = frame(shot, points(names))
        fade(centre, *((reach * FADE[0], reach * FADE[1]) if shot.get("kind") == "portrait" else (1e5, 2e5)))
        sc.camera = cam
        sc.render.resolution_x, sc.render.resolution_y = shot["res"]
        sc.cycles.samples = shot["samples"]
        sc.render.filepath = shot["out"]
        bpy.ops.render.render(write_still=True)
        print("ICON", shot["out"], flush=True)


def run(spec):
    for item in json.load(open(spec))["models"]:
        model(item)
