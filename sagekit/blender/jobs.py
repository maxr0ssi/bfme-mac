"""What each pipeline step does inside Blender. Every job takes the Building and string options;
paths come from sagekit.workspace so host and Blender agree on them."""
import os
import time

import bmesh
import bpy

from .. import workspace
from ..formats.w3d import W3DFile
from . import scene
from .layout import own_layout, take_faces


def _target(b):
    return bpy.data.objects[b.target]


def job_geometry(b, stage=None, cloth=None):
    """Original model + the building's design merged into its target mesh, then its own layout.
    stage, cloth: where the scene and the house cloth go instead of work/ (the preview's copies)."""
    ws = workspace.Workspace(b)
    stage, cloth = stage or ws.stage("geometry"), cloth or ws.house_cloth
    scene.import_w3d(ws.source_model, ws.src)
    obj = _target(b)
    meshes = [o.name for o in bpy.data.objects if o.type == "MESH"]
    before = {n: scene.tri_count(bpy.data.objects[n].data) for n in meshes}
    bb0 = scene.bbox(obj.data, obj.matrix_world if b.world_space else None)
    if b.clear:                             # a rebuilt body: EA's faces there go first (sagekit/clear.py)
        from .clear import apply
        print("CLEARED", apply(obj, b.clear, b.world_space), "of EA's faces")
    solids = b.design(b.style.shapes())
    if os.path.exists(cloth):
        os.remove(cloth)
    if ws.house:                            # cloth goes to the house-colour model (the player's colour)
        print("house colour:", take_faces(obj, solids, b.house_tags, cloth, b.world_space), "faces ->",
              ws.house["model"])
    from .capture import take_cloth         # a capturable building's dress cloth (sagekit/capture.py)
    take_cloth(b, obj, solids, ws)
    from .skintarget import add                 # a skinned target: new pieces on EA's bones (skinbody.py)
    from ..skinbody import skeleton
    sk = skeleton(ws) if W3DFile(ws.source_model).meshes[b.target].skinned else None
    added, stats = add(obj, solids, b.style.atlas, b.world_space, *((sk.pivots[0][0], sk.names) if sk else ()))
    bb1 = scene.bbox(obj.data, obj.matrix_world if b.world_space else None)
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
    scene.save(stage)


def job_preview(b, prefix, views="rts,close", res="1200x825", cloth=None):
    """The geometry stage and EA's model drawn fast in flat atlas-tag colours, and the checks that
    need no bake (sagekit/preview.py)."""
    from .preview import run
    run(b, workspace.Workspace(b), prefix, views.split(","), tuple(int(x) for x in res.split("x")), cloth)


def job_bake(b):
    from .bake import Baker, Sheet
    ws = workspace.Workspace(b)
    master = Sheet(ws.master_upscale, ws.master_normal, b.style.atlas) if b.two_sheets else None
    variants = {"var_" + mine[:-4].lower(): (ws.variant_upscale(ea),
                                             ws.upscale_of(b.style.master_variant(ea)) if master else None)
                for ea, mine in ws.variants.items()}
    baker = Baker(_target(b), b.tier.diffuse, ws.bake_dir, Sheet(ws.atlas_upscale, ws.atlas_normal, b.sheet_atlas),
                  master, variants, world=b.world_space)
    baker.run(hide=b.bake_hidden)
    from .alpha import bake_alpha
    bake_alpha(baker, ws)                   # EA's cut-out alpha, when its sheets have any (sagekit/alpha.py)


def job_paint(b):
    from ..paint.canvas import Canvas
    from ..paint.painter import Painter
    ws = workspace.Workspace(b)
    t0 = time.time()

    def log(*a):
        print("[paint %5.1fs]" % (time.time() - t0), *a, flush=True)
    p = Painter(Canvas(ws.bake_dir, b.style.atlas, _target(b), b.world_space), b.style.palette, b.style.layers(b), log)
    col = p.diffuse()
    from .alpha import baked
    alpha = baked(p.cv, ws)                 # EA's cut-outs (DXT5), or None (DXT1)
    p.write_diffuse(col, ws.tex_dir, b.own_diffuse[:-4].lower(), [b.tier.diffuse, b.tier.diffuse // 2], alpha)
    for mine in ws.variants.values():
        p.write_diffuse(p.variant(col, "var_" + mine[:-4].lower()), ws.tex_dir, mine[:-4].lower(), [b.tier.diffuse // 2],
                        alpha)
    if b.own_normal:
        p.normal(ws.atlas_normal, ws.tex(b.own_normal[:-4].lower() + ".tga"))


def job_export(b):
    ws = workspace.Workspace(b)
    from .capture import split              # a capturable building's dress: meshes of their own
    split(b)
    from .skintarget import export          # a skinned target: its skin export too (skinbody.py)
    if not export(ws, b):
        scene.export_w3d(ws.export_model, b.target)
    scene.save(ws.stage("export"))


def job_capture_render(b, out, house="", res="1200x860", spp="48"):
    """The capture dress review renders (sagekit/blender/capture.py)."""
    from .capture import render_review
    render_review(b, out, house, res, spp)


def job_render(b, w3d, prefix, views="rts,close", res="1600x1100", spp="64", frame=None, **textures):
    """Render a shipped model like the game draws it. textures: lowercase name=file overrides;
    frame: the mesh the automatic views frame (a derived model's body)."""
    from .render import render_views
    ws = workspace.Workspace(b)
    texmap = ws.texture_map()
    texmap.update({k.lower(): v for k, v in textures.items()})
    house = None                            # the new building's cloth, in its house-colour model
    if os.path.basename(prefix).startswith("new") and ws.house:
        from ..game import Install
        from ..house import root, shipped
        _, out = shipped(b.style.faction)
        path = out and os.path.join(out, *Install.model_path(ws.house["model"]).split("\\"))
        own = ws.house_cloth if os.path.exists(ws.house_cloth) else None
        house = (path, own, os.path.join(root(b.style.faction), "src")) if path and os.path.exists(path) else None
    render_views(b, w3d, W3DFile(w3d), texmap, prefix, views.split(","), tuple(int(x) for x in res.split("x")), int(spp),
                 ws.src, house, frame)


def job_checks(b):
    from .checks import run_checks
    ok = run_checks(b, workspace.Workspace(b))
    if not ok:
        raise SystemExit("checks failed")


def job_lifecycle(b):
    """EA's construction / really damaged / rubble models rebuilt around our body (sagekit/lifecycle.py)."""
    from .lifecycle import run
    run(b, workspace.Workspace(b))


def job_lifecycle_render(b, model, who, out, res="1100x760", spp="48", **textures):
    """EA's lifecycle model or ours at the frames the player sees (sagekit/blender/lifecycle_render.py)."""
    from .lifecycle_render import render_model
    render_model(b, model, who, out, res, spp, **textures)


def job_night(b):
    """The recipe's night lights cast onto our finished body (sagekit/nightlights.py)."""
    from .nightlights import cast
    cast(b, workspace.Workspace(b))


def job_night_render(b, w3d, prefix, views="rts,close", res="1400x960", spp="48", frame=None, **textures):
    """A model at night: moonlight, the night meshes lit (sagekit/blender/nightlights.py)."""
    from .nightlights import render_night
    ws = workspace.Workspace(b)
    texmap = ws.texture_map()
    texmap.update({k.lower(): v for k, v in textures.items()})
    render_night(b, w3d, prefix, views.split(","), tuple(int(x) for x in res.split("x")), int(spp), ws.src, frame, texmap)


def job_icons(b, spec):
    """HUD icon renders: every model and shot the spec (JSON) lists (sagekit/blender/icon.py)."""
    from .icon import run
    run(spec)
