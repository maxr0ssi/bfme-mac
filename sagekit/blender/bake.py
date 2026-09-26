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
    var_*      EA's variant sheets (damaged, snow, stonework) through the ATLAS layer   linear RGB
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


class Sheet:
    """One source sheet: its upscale, normal map (or None) and Atlas (mask hints)."""

    def __init__(self, png, nrm, atlas):
        self.png, self.nrm, self.atlas = png, nrm, atlas


class Baker:
    """sheet: what the target mesh's original faces were painted from; master (None when it is the
    same sheet): the faction atlas the new faces are mapped onto. variant_pngs: {pass name:
    (sheet variant png, master variant png or None)}."""

    def __init__(self, obj, res, outdir, sheet, master=None, variant_pngs=None, world=False):
        self.variant_pngs = variant_pngs or {}
        self.world = world                  # pos/nrm in world axes (Building.world_space)
        self.obj, self.res, self.outdir = obj, res, outdir
        self.sheet, self.master = sheet, master
        self.atlas_png, self.atlas_nrm, self.atlas = sheet.png, sheet.nrm, sheet.atlas
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
        # REPEAT like the game's samplers: some originals tile past [0,1] (DBBunker's shield panels
        # run to u -0.37, v -0.56) and EXTEND smeared the sheet's edge texels over those faces
        n = self.node("ShaderNodeTexImage", image=img, interpolation=interp, extension="REPEAT")
        self.link(self.node("ShaderNodeUVMap", uv_map=uv).outputs[0], n.inputs[0])
        return n

    def is_new(self):
        at = self.node("ShaderNodeAttribute", attribute_type="GEOMETRY", attribute_name=TAG_ATTR)
        gt = self.node("ShaderNodeMath", operation="GREATER_THAN")
        gt.inputs[1].default_value = 0.5
        self.link(at.outputs["Fac"], gt.inputs[0])
        return gt.outputs[0]

    def mixed(self, sheet_socket, master_socket, kind="RGBA"):
        """Old faces from the building's sheet, new faces from the faction atlas."""
        m = self.node("ShaderNodeMix", data_type=kind)
        ins = [i for i in m.inputs if i.enabled]
        self.link(self.is_new(), ins[0])
        self.link(sheet_socket, ins[1])
        self.link(master_socket, ins[2])
        return [o for o in m.outputs if o.enabled][0]

    def sheet_image(self, sheet_img, master_img=None, interp="Cubic"):
        a = self.image(sheet_img, interp=interp).outputs[0]
        return a if master_img is None else self.mixed(a, self.image(master_img, interp=interp).outputs[0])

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
        load = lambda p: bpy.data.images.load(p, check_existing=True)   # noqa: E731
        src = load(self.atlas_png)
        msrc = load(self.master.png) if self.master else None
        self.reset()
        self.emit(self.sheet_image(src, msrc))
        self.bake("atlas", samples=16)
        for name, (png, mpng) in sorted(self.variant_pngs.items()):     # EA's damaged / snow / stonework sheets
            self.reset()
            self.emit(self.sheet_image(load(png), load(mpng) if mpng else None))
            self.bake(name, samples=16)
        mimgs = self._mask_images(msrc, self.master.atlas) if self.master else [None] * 3
        for i, (img, mimg) in enumerate(zip(self._mask_images(src, self.atlas), mimgs)):
            self.reset()
            self.emit(self.sheet_image(img, mimg, interp="Linear"))
            self.bake("mask%d" % (i + 1), samples=16)
        self.reset()
        self.emit(self.node("ShaderNodeUVMap", uv_map="ATLAS").outputs[0])
        self.bake("auv", channels=2)
        self.reset()
        if self.world:
            self.emit(self.node("ShaderNodeNewGeometry").outputs["Position"])
        else:
            self.emit(self.node("ShaderNodeTexCoord").outputs["Object"])
        self.bake("pos")
        self.reset()
        if self.world:
            self.emit(self.node("ShaderNodeNewGeometry").outputs["True Normal"])
        else:
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
        if self.atlas_nrm is None:            # the sheet has no normal map: none is shipped
            self.obj.data.materials[0] = self.orig_mat
            print("bake done (no normal map)", flush=True)
            return
        normal = dict(kind="NORMAL", res=self.res // 2, normal_space="TANGENT",
                      normal_r="POS_X", normal_g="POS_Y", normal_b="POS_Z")
        self.reset()
        self.shade(self._detail_normal(self.atlas_nrm, self.master.nrm if self.master else None))
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

    def _detail_normal(self, nrm, master_nrm=None):
        """The shading normal of the original normal map(s) through the ATLAS layer."""
        def one(path):
            nm = self.node("ShaderNodeNormalMap", space="TANGENT", uv_map="ATLAS")
            self.link(self.image(self._gl_normal_image(path)).outputs[0], nm.inputs["Color"])
            return nm.outputs[0]
        a = one(nrm)
        return a if master_nrm is None else self.mixed(a, one(master_nrm), "VECTOR")

    def _mask_images(self, src, atlas):
        """A sheet's material masks as three RGB float images (sagekit/paint/masks.py order); a
        sheet without hints keeps only coherent metal (see masks.compute)."""
        w, h = src.size
        a = np.empty(w * h * 4, np.float32)
        src.pixels.foreach_get(a)
        ms = masks.compute(a.reshape(h, w, 4)[..., :3], atlas, coherent=not atlas.mask_hints)
        out = []
        for k in range(3):
            px = np.ones((h, w, 4), np.float32)
            for c in range(3):
                px[..., c] = ms[3 * k + c]
            im = bpy.data.images.new("mask%d_%s" % (k + 1, atlas.texture or "sheet"), w, h, alpha=False, float_buffer=True)
            im.colorspace_settings.name = "Non-Color"
            im.pixels.foreach_set(px.ravel())
            out.append(im)
        return out

    def _gl_normal_image(self, path):
        """An original normal map with red flipped to Blender's convention (see imageio)."""
        src = bpy.data.images.load(path, check_existing=True)
        src.colorspace_settings.name = "Non-Color"
        w, h = src.size
        a = np.empty(w * h * 4, np.float32)
        src.pixels.foreach_get(a)
        a = imageio.game_to_gl(a.reshape(h, w, 4))
        gl = bpy.data.images.new("nrm_gl_" + os.path.basename(path), w, h, alpha=False, float_buffer=True)
        gl.colorspace_settings.name = "Non-Color"
        gl.pixels.foreach_set(a.ravel())
        return gl
