"""Bake the G-buffers the painter needs into the target mesh's own layout (UVMap), as .npy files
(float32, rows bottom-up like Blender's pixel buffers):

    atlas      the upscaled original sheet seen through the ATLAS layer        linear RGB
    mask1..3   the sheet's material masks (sagekit/paint/masks.py), 3 per image
    auv        the ATLAS coordinates (wood grain runs along them)                uv
    pos, nrm   object-space position, geometric (flat) normal                    xyz
    cov        island coverage without margin                                     1 ch
    tag        face tag / 100 (0 original face, else 1 + atlas region index)     1 ch
    ao_s/ao_l  ambient occlusion at 2.5 and 18 units                              1 ch
    bevel      convex/concave edges: 1 - dot(bevelled normal, flat normal)       1 ch
    ndet       the original normal map re-expressed in the new tangent space     3 ch (GL)
    nbev       bevelled-edge normals in the new tangent space                     3 ch (GL)
The normal passes are at half resolution (the normal map's size).
"""
import os
import time

import bpy
import numpy as np

from ..paint import imageio, masks
from .layout import TAG_ATTR
from .scene import use_gpu

TAG_SCALE = 100.0


class Baker:
    def __init__(self, obj, res, outdir, atlas_png, atlas_nrm, atlas):
        self.obj, self.res, self.outdir = obj, res, outdir
        self.atlas_png, self.atlas_nrm, self.atlas = atlas_png, atlas_nrm, atlas
        os.makedirs(outdir, exist_ok=True)
        sc = bpy.context.scene
        sc.render.engine = "CYCLES"
        use_gpu(sc)
        me = obj.data
        me.uv_layers.active = me.uv_layers["UVMap"]
        if "BakeGround" not in bpy.data.objects:        # occludes the underside like the terrain
            gm = bpy.data.meshes.new("BakeGround")
            s = 1500
            gm.from_pydata([(-s, -s, -0.02), (s, -s, -0.02), (s, s, -0.02), (-s, s, -0.02)], [], [(0, 1, 2, 3)])
            sc.collection.objects.link(bpy.data.objects.new("BakeGround", gm))
        w = bpy.data.worlds.get("BakeWorld") or bpy.data.worlds.new("BakeWorld")
        sc.world = w
        w.use_nodes = True
        w.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
        self.orig_mat = me.materials[0]
        self.mat = bpy.data.materials.new("BAKE")
        self.mat.use_nodes = True
        me.materials[0] = self.mat
        self.nt = self.mat.node_tree

    # ------------------------------------------------------------------ node helpers
    def reset(self):
        self.nt.nodes.clear()
        return self.nt.nodes.new("ShaderNodeOutputMaterial")

    def node(self, kind, **props):
        n = self.nt.nodes.new(kind)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def link(self, a, b):
        self.nt.links.new(a, b)

    def image(self, img, uv="ATLAS", interp="Cubic"):
        n = self.node("ShaderNodeTexImage", image=img, interpolation=interp, extension="EXTEND")
        self.link(self.node("ShaderNodeUVMap", uv_map=uv).outputs[0], n.inputs[0])
        return n

    def emit(self, socket):
        e = self.node("ShaderNodeEmission")
        self.link(socket, e.inputs[0])
        self.link(e.outputs[0], self.nt.nodes["Material Output"].inputs[0])

    def shade(self, normal_socket):
        bs = self.node("ShaderNodeBsdfDiffuse")
        self.link(normal_socket, bs.inputs["Normal"])
        self.link(bs.outputs[0], self.nt.nodes["Material Output"].inputs[0])

    def bake(self, name, res=None, kind="EMIT", samples=1, margin=8, channels=3, **kw):
        t = time.time()
        res = res or self.res
        im = bpy.data.images.new(name, res, res, alpha=False, float_buffer=True)
        im.colorspace_settings.name = "Non-Color"
        n = self.node("ShaderNodeTexImage", image=im)
        for x in self.nt.nodes:
            x.select = False
        n.select = True
        self.nt.nodes.active = n
        sc = bpy.context.scene
        sc.cycles.samples = samples
        for o in bpy.context.view_layer.objects:
            o.select_set(o == self.obj)
        bpy.context.view_layer.objects.active = self.obj
        sc.render.bake.margin = margin
        sc.render.bake.margin_type = "EXTEND"
        bpy.ops.object.bake(type=kind, margin=margin, margin_type="EXTEND", use_clear=True,
                            target="IMAGE_TEXTURES", **kw)
        a = np.empty(res * res * 4, np.float32)
        im.pixels.foreach_get(a)
        np.save(os.path.join(self.outdir, name + ".npy"), a.reshape(res, res, 4)[..., :channels])
        bpy.data.images.remove(im)
        print("baked %-6s %dx%d %s  %.1fs" % (name, res, res, kind, time.time() - t), flush=True)

    # ------------------------------------------------------------------ passes
    def run(self, hide=()):
        for o in bpy.data.objects:
            if o.name in hide:
                o.hide_render = True
        src = bpy.data.images.load(self.atlas_png, check_existing=True)
        self.reset()
        self.emit(self.image(src).outputs[0])
        self.bake("atlas", samples=16)
        for i, img in enumerate(self._mask_images(src)):
            self.reset()
            self.emit(self.image(img, interp="Linear").outputs[0])
            self.bake("mask%d" % (i + 1), samples=16)
        self.reset()
        self.emit(self.node("ShaderNodeUVMap", uv_map="ATLAS").outputs[0])
        self.bake("auv", channels=2)
        self.reset()
        self.emit(self.node("ShaderNodeTexCoord").outputs["Object"])
        self.bake("pos")
        self.reset()
        vt = self.node("ShaderNodeVectorTransform", vector_type="NORMAL", convert_from="WORLD", convert_to="OBJECT")
        self.link(self.node("ShaderNodeNewGeometry").outputs["True Normal"], vt.inputs[0])
        self.emit(vt.outputs[0])
        self.bake("nrm")
        self.reset()
        rgb = self.node("ShaderNodeRGB")
        rgb.outputs[0].default_value = (1, 1, 1, 1)
        self.emit(rgb.outputs[0])
        self.bake("cov", margin=0, channels=1)
        self.reset()
        at = self.node("ShaderNodeAttribute", attribute_type="GEOMETRY", attribute_name=TAG_ATTR)
        div = self.node("ShaderNodeMath", operation="DIVIDE")
        div.inputs[1].default_value = TAG_SCALE
        self.link(at.outputs["Fac"], div.inputs[0])
        self.emit(div.outputs[0])
        self.bake("tag", channels=1)
        for name, dist in (("ao_s", 2.5), ("ao_l", 18.0)):
            self.reset()
            ao = self.node("ShaderNodeAmbientOcclusion", samples=32)
            ao.inputs["Distance"].default_value = dist
            self.emit(ao.outputs["AO"])
            self.bake(name, samples=48, channels=1)
        self.reset()
        self.emit(self._bevel_delta().outputs[0])
        self.bake("bevel", samples=16, channels=1)
        normal = dict(kind="NORMAL", res=self.res // 2, normal_space="TANGENT",
                      normal_r="POS_X", normal_g="POS_Y", normal_b="POS_Z")
        self.reset()
        nm = self.node("ShaderNodeNormalMap", space="TANGENT", uv_map="ATLAS")
        self.link(self.image(self._gl_normal_image()).outputs[0], nm.inputs["Color"])
        self.shade(nm.outputs[0])
        self.bake("ndet", samples=16, **normal)
        self.reset()
        bv = self.node("ShaderNodeBevel", samples=16)
        bv.inputs["Radius"].default_value = 0.55
        self.shade(bv.outputs[0])
        self.bake("nbev", samples=32, **normal)
        self.obj.data.materials[0] = self.orig_mat
        print("bake done", flush=True)

    def _bevel_delta(self):
        bv = self.node("ShaderNodeBevel", samples=16)
        bv.inputs["Radius"].default_value = 0.45
        dp = self.node("ShaderNodeVectorMath", operation="DOT_PRODUCT")
        self.link(bv.outputs[0], dp.inputs[0])
        self.link(self.node("ShaderNodeNewGeometry").outputs["True Normal"], dp.inputs[1])
        inv = self.node("ShaderNodeMath", operation="SUBTRACT")
        inv.inputs[0].default_value = 1.0
        self.link(dp.outputs["Value"], inv.inputs[1])
        return inv

    def _mask_images(self, src):
        """The sheet's material masks as three RGB float images (sagekit/paint/masks.py order)."""
        w, h = src.size
        a = np.empty(w * h * 4, np.float32)
        src.pixels.foreach_get(a)
        ms = masks.compute(a.reshape(h, w, 4)[..., :3], self.atlas)
        out = []
        for k in range(3):
            px = np.ones((h, w, 4), np.float32)
            for c in range(3):
                px[..., c] = ms[3 * k + c]
            im = bpy.data.images.new("mask%d" % (k + 1), w, h, alpha=False, float_buffer=True)
            im.colorspace_settings.name = "Non-Color"
            im.pixels.foreach_set(px.ravel())
            out.append(im)
        return out

    def _gl_normal_image(self):
        """The original normal map with red flipped to Blender's convention (see imageio)."""
        src = bpy.data.images.load(self.atlas_nrm, check_existing=True)
        src.colorspace_settings.name = "Non-Color"
        w, h = src.size
        a = np.empty(w * h * 4, np.float32)
        src.pixels.foreach_get(a)
        a = imageio.game_to_gl(a.reshape(h, w, 4))
        gl = bpy.data.images.new("nrm_gl", w, h, alpha=False, float_buffer=True)
        gl.colorspace_settings.name = "Non-Color"
        gl.pixels.foreach_set(a.ravel())
        return gl
