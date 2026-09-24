"""Scene plumbing: the W3D add-on's import/export, clean scenes, the GPU."""
import bpy


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    for coll in (bpy.data.meshes, bpy.data.armatures, bpy.data.materials, bpy.data.images):
        for d in list(coll):
            if d.users == 0:
                coll.remove(d)


def import_w3d(path):
    clear()
    bpy.ops.import_mesh.westwood_w3d(filepath=path)


def export_w3d(path, target=None):
    """Export mode HM (hierarchy + model) like the originals. The exporter names containers after
    the FILE, so `path` must be named like the original model (DBFORTRESS.w3d). For `target`, the
    bake-only ATLAS layer is removed first (the exporter splits vertices on every UV layer) and
    UVMap.001 made an identical copy of UVMap."""
    if target:
        me = bpy.data.objects[target].data
        if "ATLAS" in me.uv_layers:
            me.uv_layers.remove(me.uv_layers["ATLAS"])
        buf = [0.0] * (2 * len(me.loops))
        me.uv_layers["UVMap"].data.foreach_get("uv", buf)
        me.uv_layers["UVMap.001"].data.foreach_set("uv", buf)
        me.uv_layers.active = me.uv_layers["UVMap"]
        me.uv_layers["UVMap"].active_render = True
    if "BakeGround" in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects["BakeGround"])
    bpy.ops.export_mesh.westwood_w3d(filepath=path, file_format="W3D", export_mode="HM")


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
