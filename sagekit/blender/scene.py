"""Scene plumbing: the W3D add-on's import/export, clean scenes, the GPU."""
import os
import shutil
import tempfile

import bpy

from ..formats.w3d import W3DFile


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    for coll in (bpy.data.meshes, bpy.data.armatures, bpy.data.materials, bpy.data.images):
        for d in list(coll):
            if d.users == 0:
                coll.remove(d)


def import_w3d(path, skeletons=None):
    """Import a model. A skinned model's skeleton is a separate file the importer only looks for
    next to the model; if it is not there it is taken from `skeletons` (the extracted sources)."""
    clear()
    skl = W3DFile(path).skeleton()
    here = os.path.join(os.path.dirname(path), skl or "")
    if skl and not os.path.exists(here) and skeletons:
        tmp = tempfile.mkdtemp(prefix="sagekit-import-")
        shutil.copy(path, tmp)
        shutil.copy(os.path.join(skeletons, skl), tmp)
        path = os.path.join(tmp, os.path.basename(path))
    bpy.ops.import_mesh.westwood_w3d(filepath=path)
    plain_placeholders()


def plain_placeholders():
    """The importer stands in a 2048px COLOR_GRID image for every texture it cannot find. Filling
    a COLOR_GRID draws text, and Cycles filling several at once crashes Blender (a font race in
    blf_font_draw_buffer); a small plain image is never drawn with text."""
    for img in bpy.data.images:
        if img.source == "GENERATED" and img.generated_type != "BLANK":
            img.generated_type = "BLANK"
            img.generated_width = img.generated_height = 8
            img.generated_color = (0.5, 0.5, 0.5, 1.0)


def export_w3d(path, target=None):
    """Export mode HM (hierarchy + model) like the originals. The exporter names containers after
    the FILE, so `path` must be named like the original model (DBFORTRESS.w3d). For `target`, the
    bake-only ATLAS layer is removed first (the exporter splits vertices on every UV layer) and
    UVMap.001 (if any) made an identical copy of UVMap."""
    if target:
        me = bpy.data.objects[target].data
        if "ATLAS" in me.uv_layers:
            me.uv_layers.remove(me.uv_layers["ATLAS"])
        mirror_uv(me)
        me.uv_layers.active = me.uv_layers["UVMap"]
        me.uv_layers["UVMap"].active_render = True
    if "BakeGround" in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects["BakeGround"])
    bpy.ops.export_mesh.westwood_w3d(filepath=path, file_format="W3D", export_mode="HM")


def mirror_uv(me):
    """Copy UVMap into UVMap.001, the importer's second layer for a model with a normal-map pass
    (both passes must read the same UVs). A single-texture model has no second layer."""
    if "UVMap.001" in me.uv_layers:
        buf = [0.0] * (2 * len(me.loops))
        me.uv_layers["UVMap"].data.foreach_get("uv", buf)
        me.uv_layers["UVMap.001"].data.foreach_set("uv", buf)


def save(path):
    bpy.ops.wm.save_as_mainfile(filepath=path)


def use_gpu(scene):
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        scene.cycles.device = "GPU"
    except (KeyError, TypeError, AttributeError) as e:
        print("gpu unavailable, rendering on the CPU:", e)


def tri_count(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def bbox(me):
    cs = [v.co for v in me.vertices]
    return [min(c[i] for c in cs) for i in range(3)], [max(c[i] for c in cs) for i in range(3)]
