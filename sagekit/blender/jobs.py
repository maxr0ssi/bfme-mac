"""What each pipeline step does inside Blender. Every job takes the Building and string options;
paths come from sagekit.workspace so host and Blender agree on them."""
import time

import bmesh
import bpy

from .. import workspace
from ..formats.w3d import W3DFile
from . import scene
from .layout import add_solids, own_layout


def _target(b):
    return bpy.data.objects[b.target]


def job_geometry(b):
    """Original model + the building's design merged into its target mesh, then its own layout."""
    ws = workspace.Workspace(b)
    scene.import_w3d(ws.source_model)
    obj = _target(b)
    meshes = [o.name for o in bpy.data.objects if o.type == "MESH"]
    before = {n: scene.tri_count(bpy.data.objects[n].data) for n in meshes}
    bb0 = scene.bbox(obj.data)
    added, stats = add_solids(obj, b.design(b.style.shapes()), b.style.atlas)
    bb1 = scene.bbox(obj.data)
    print("TRIS before", before)
    print("TRIS after ", {n: scene.tri_count(bpy.data.objects[n].data) for n in meshes}, "added", added, stats)
    print("BBOX before", [round(x, 2) for x in bb0[0]], [round(x, 2) for x in bb0[1]])
    print("BBOX after ", [round(x, 2) for x in bb1[0]], [round(x, 2) for x in bb1[1]])
    print("Z growth %.1f%%" % (100 * (bb1[1][2] - bb1[0][2]) / (bb0[1][2] - bb0[0][2]) - 100))
    print("islands", own_layout(obj, b))
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    print("loose verts", sum(1 for v in bm.verts if not v.link_faces),
          "zero-area", sum(1 for f in bm.faces if f.calc_area() < 1e-6))
    bm.free()
    scene.save(ws.stage("geometry"))


def job_bake(b):
    from .bake import Baker
    ws = workspace.Workspace(b)
    Baker(_target(b), b.tier.diffuse, ws.bake_dir, ws.atlas_upscale, ws.atlas_normal, b.style.atlas).run(
        hide=b.bake_hidden)


def job_paint(b):
    from ..paint.canvas import Canvas
    from ..paint.painter import Painter
    ws = workspace.Workspace(b)
    t0 = time.time()

    def log(*a):
        print("[paint %5.1fs]" % (time.time() - t0), *a, flush=True)
    p = Painter(Canvas(ws.bake_dir, b.style.atlas, _target(b)), b.style.palette, b.style.layers(b), log)
    names = b.texture_names()
    diffuse, normal = names[b.style.atlas.texture], names[b.style.atlas.normal]
    p.write_diffuse(p.diffuse(), ws.tex_dir, diffuse[:-4].lower(), [b.tier.diffuse, b.tier.diffuse // 2])
    p.normal(ws.atlas_normal, ws.tex(normal[:-4].lower() + ".tga"))


def job_export(b):
    ws = workspace.Workspace(b)
    scene.export_w3d(ws.export_model, b.target)
    scene.save(ws.stage("export"))


def job_reference(b):
    """The untouched original through the same import + export: what 'unchanged' is compared to."""
    ws = workspace.Workspace(b)
    scene.import_w3d(ws.source_model)
    scene.export_w3d(ws.reference_export)


def job_render(b, w3d, prefix, views="rts,close", res="1600x1100", spp="64", **textures):
    """Render a shipped model like the game draws it. textures: lowercase name=file overrides."""
    from .render import render_views
    ws = workspace.Workspace(b)
    texmap = ws.texture_map()
    texmap.update({k.lower(): v for k, v in textures.items()})
    render_views(b, w3d, W3DFile(w3d), texmap, prefix, views.split(","), tuple(int(x) for x in res.split("x")), int(spp))


def job_checks(b):
    from .checks import run_checks
    ok = run_checks(b, workspace.Workspace(b))
    if not ok:
        raise SystemExit("checks failed")
