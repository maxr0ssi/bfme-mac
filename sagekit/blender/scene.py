"""Scene plumbing: the W3D add-on's import/export, clean scenes, the GPU."""
import os
import shutil
import sys
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
    """Import a model into a clean scene (a skinned one's skeleton: beside_skeleton)."""
    clear()
    add_w3d(path, skeletons)


def beside_skeleton(path, skeletons=None):
    """A skinned model's skeleton is a separate file the importer only looks for next to the model:
    if it is not there, the path of a temporary copy with the skeleton from `skeletons` (the
    extracted sources) beside it; else `path`."""
    skl = W3DFile(path).skeleton()
    here = os.path.join(os.path.dirname(path), skl or "")
    if not skl or os.path.exists(here) or not skeletons or not os.path.exists(os.path.join(skeletons, skl)):
        return path
    tmp = tempfile.mkdtemp(prefix="sagekit-import-")
    shutil.copy(path, tmp)
    shutil.copy(os.path.join(skeletons, skl), tmp)
    return os.path.join(tmp, os.path.basename(path))


def add_w3d(path, skeletons=None):
    """Import a model into the scene as it is (a house-colour model beside its building)."""
    path = beside_skeleton(path, skeletons)
    try:
        bpy.ops.import_mesh.westwood_w3d(filepath=path)
    except RuntimeError as e:               # the add-on reports FX material properties it has no
        if "not implemented" not in str(e):     # socket for (EA's DBWallGateN_A: bumpHeight) as an
            raise                               # error after importing everything: carry on
        print("WARN import %s: %s" % (os.path.basename(path), str(e).strip()), flush=True)
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
    """Cycles on the GPU: Metal on the Mac (every device), else the first of OptiX, CUDA, HIP and
    oneAPI with a device (its devices only; the A100 offload: OptiX). SAGEKIT_CYCLES_DEVICE picks
    one (e.g. CUDA)."""
    if sys.platform != "darwin" or os.environ.get("SAGEKIT_CYCLES_DEVICE"):
        return _use_gpu_other(scene)
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        scene.cycles.device = "GPU"
    except (KeyError, TypeError, AttributeError) as e:
        print("gpu unavailable, rendering on the CPU:", e)


def _use_gpu_other(scene):
    kinds = [os.environ["SAGEKIT_CYCLES_DEVICE"].upper()] if os.environ.get("SAGEKIT_CYCLES_DEVICE") else \
        ["OPTIX", "CUDA", "HIP", "ONEAPI"]
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
    except (KeyError, AttributeError) as e:
        print("gpu unavailable, rendering on the CPU:", e)
        return
    for kind in kinds:
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
        except (TypeError, AttributeError, ValueError):
            continue
        gpus = [d for d in prefs.devices if d.type == kind]
        if not gpus:
            continue
        for d in prefs.devices:
            d.use = d.type == kind
        scene.cycles.device = "GPU"
        if not _use_gpu_other.__dict__.get("said"):
            print("cycles on %s: %s" % (kind, ", ".join(d.name for d in gpus)), flush=True)
            _use_gpu_other.said = True
        return
    print("gpu unavailable (%s), rendering on the CPU" % "/".join(kinds))


def tri_count(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def bbox(me, mw=None):
    """(min, max) of a mesh's vertices, in world axes when given its object's matrix."""
    cs = [mw @ v.co if mw is not None else v.co for v in me.vertices]
    return [min(c[i] for c in cs) for i in range(3)], [max(c[i] for c in cs) for i in range(3)]
