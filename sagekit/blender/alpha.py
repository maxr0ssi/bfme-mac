"""Cut-out alpha inside Blender and in the checks (the host side and the why: sagekit/alpha.py).

    bake_alpha(baker, ws)   bake pass 'alpha': EA's alpha through the ATLAS layer
    baked(canvas, ws)       that bake for the painter, or None
    checks(b, ws, r)        DXT5 exactly when expected; our cut-outs where EA's were, on a target
                            whose EA material shows alpha (alpha test or blend; sagekit/formats/w3dlight.py)
"""
import os
import subprocess

import numpy as np

from ..alpha import dds_fourcc, expected, path


def bake_alpha(baker, ws):
    """The 'alpha' bake pass (Baker in bake.py): the building's sheet's alpha for EA's faces, the
    faction atlas's for new faces (opaque if it has none), opaque on the atlas's `painted` regions
    (cloth is repainted: never EA's pixels). Removes a stale bake when the building has no alpha."""
    import bpy
    from .layout import TAG_ATTR
    out = os.path.join(baker.outdir, "alpha.npy")
    if not expected(ws):
        if os.path.exists(out):
            os.remove(out)
        return
    b = ws.b

    def image(p):
        if not os.path.exists(p):
            one = baker.node("ShaderNodeValue")
            one.outputs[0].default_value = 1.0
            return one.outputs[0]
        im = bpy.data.images.load(p, check_existing=True)
        im.colorspace_settings.name = "Non-Color"
        return baker.image(im, interp="Linear").outputs[0]
    baker.reset()
    a = image(path(ws.atlas_upscale))
    if b.two_sheets:
        a = baker.mixed(a, image(path(ws.master_upscale)), "FLOAT")
    regions = list(b.style.atlas.regions)
    for name in getattr(b.style.atlas, "painted", ()):
        at = baker.node("ShaderNodeAttribute", attribute_type="GEOMETRY", attribute_name=TAG_ATTR)
        eq = baker.node("ShaderNodeMath", operation="COMPARE")
        eq.inputs[1].default_value, eq.inputs[2].default_value = regions.index(name) + 1, 0.1
        baker.link(at.outputs["Fac"], eq.inputs[0])
        mx = baker.node("ShaderNodeMath", operation="MAXIMUM")
        baker.link(a, mx.inputs[0])
        baker.link(eq.outputs[0], mx.inputs[1])
        a = mx.outputs[0]
    baker.emit(a)
    baker.obj.data.materials[0] = baker.mat         # run() handed the mesh its own material back
    baker.bake("alpha", samples=16, channels=1)
    baker.obj.data.materials[0] = baker.orig_mat


def baked(canvas, ws):
    """The alpha bake (h, w), rows bottom-up like the colour, or None when the building has none."""
    return canvas.load("alpha")[..., 0] if expected(ws) and os.path.exists(os.path.join(canvas.dir, "alpha.npy")) else None


# ------------------------------------------------------------------------------------ checks
def read_alpha(dds):
    """(h, w) float alpha of a DDS's top mip, rows top-down."""
    w, h = (int(x) for x in subprocess.check_output(["magick", "identify", "-format", "%w %h", dds + "[0]"]).split())
    raw = subprocess.check_output(["magick", dds + "[0]", "-alpha", "extract", "-depth", "8", "gray:-"])
    return np.frombuffer(raw, np.uint8).reshape(h, w).astype(np.float32) / 255


def sample(img, uv):
    """Nearest-texel lookup of W3D texture coordinates in an image with rows top-down: the files'
    v runs up from the image's bottom row (the W3D add-on hands it to Blender unchanged and the
    renders match the game), repeating like the game's samplers."""
    h, w = img.shape
    x = np.floor(np.mod(uv[:, 0], 1.0) * w).astype(int).clip(0, w - 1)
    y = np.floor((1.0 - np.mod(uv[:, 1], 1.0)) * h).astype(int).clip(0, h - 1)
    return img[y, x]


def surviving(ea, ours):
    """[(EA triangle, our triangle's corners in EA's order)] for the triangles whose corners are the
    same points (to 0.001): EA's faces our body still carries, whatever the layout did to their UVs."""
    def corners(m, t):
        return [tuple(round(c, 3) for c in m.verts[i]) for i in t]
    mine = {}
    for t in ours.tris:
        mine.setdefault(tuple(sorted(corners(ours, t))), t)
    out = []
    for t in ea.tris:
        c = corners(ea, t)
        u = mine.get(tuple(sorted(c)))
        if u is not None:
            at = {p: i for p, i in zip(corners(ours, u), u)}
            out.append((t, [at[p] for p in c]))
    return out


def agreement(ea_mesh, ea_img, our_mesh, our_img, grid=6):
    """(points compared, points whose cut-out state differs): barycentric sample points of every
    surviving triangle, seen at EA's UVs in EA's sheet and at ours in our texture."""
    pairs = surviving(ea_mesh, our_mesh)
    bary = np.array([(i, j, grid - i - j) for i in range(1, grid) for j in range(1, grid - i)] + [(grid / 3,) * 3],
                    np.float32) / grid
    ua, ub = np.array(ea_mesh.uv, np.float32), np.array(our_mesh.uv, np.float32)
    cut = kept = opaque = lost = shrunk = 0
    for ta, tb in pairs:
        ea_uv, our_uv = ua[list(ta)], ub[tb]
        if np.ptp(ea_uv, 0).max() * ea_img.shape[0] > 2 * np.ptp(our_uv, 0).max() * our_img.shape[0]:
            shrunk += 1                     # EA's face runs across the sheet (EBStable's tiles twice in u):
            continue                        # its texels average to a grey in ours as in the game's mips
        a, b = sample(ea_img, bary @ ea_uv) < 0.5, sample(our_img, bary @ our_uv) < 0.5
        cut, kept = cut + int(a.sum()), kept + int((a & b).sum())
        opaque, lost = opaque + int((~a).sum()), lost + int((~a & b).sum())
    return cut, kept, opaque, lost, len(pairs) - shrunk, shrunk


def checks(b, ws, r):
    """Checks-suite section: our texture is DXT5 exactly when alpha is expected, and on the faces
    our body keeps from EA's its cut-outs are where EA's were."""
    from ..formats.textures import dds_info
    from ..formats.w3d import W3DFile
    want = dds_fourcc(ws)
    mine = ws.shipped_texture(b.own_diffuse, ".dds")
    r.section("alpha (sagekit/alpha.py): EA's cut-outs carried over")
    got = dds_info(mine)["fourcc"] if os.path.exists(mine) else "missing"
    r.check("%s is %s (%s)" % (os.path.basename(mine), want, "EA's sheet has alpha" if want == "DXT5" else "no alpha in EA's sheets"),
            got == want, got)
    if want != "DXT5":
        return
    ea_img, our_img = read_alpha(ws.atlas_dds), read_alpha(mine)
    ea, ours = W3DFile(ws.source_model).meshes[b.target], W3DFile(ws.shipped_model).meshes[b.target]
    cut, kept, opaque, lost, tris, shrunk = agreement(ea, ea_img, ours, our_img)
    ea_cut = [sample(ea_img, np.array(ea.uv, np.float32)[list(t)].mean(0, keepdims=True))[0] < 0.5 for t in ea.tris]
    r.info("EA's %s" % os.path.basename(ws.atlas_dds), "%.2f%% of texels cut out; %d of EA's %d triangles centred on a cut-out"
           % (100 * float((ea_img < 0.5).mean()), sum(ea_cut), len(ea.tris)))
    if not tris:
        r.info("alpha against EA's", "none of EA's triangles survives in our body: nothing to compare")
        return
    # sample points inside the kept triangles, each seen at EA's UVs and at ours; a texel's edge can
    # fall either side after the relayout and DXT5, hence the margins
    if shrunk:
        r.info("alpha: faces left out", "%d of EA's faces sample their sheet at more than twice our density" % shrunk)
    from ..formats.w3dlight import material
    mode = material(ea.bytes)["alpha"]
    if not mode:                        # EA's own material ignores the alpha (NormalMapped.fx with
        r.info("alpha: %s draws with alpha test off (EA's material)" % b.target,   # AlphaTestEnable off):
               "no hole shows in the game, EA's or ours; cut-outs %d of %d points, solid %d of %d points opened"
               % (kept, cut, lost, opaque))                                        # nothing to hold
        return
    r.check("EA's cut-outs are cut out in ours on the %d triangles our body keeps (>= 90%%)" % tris,
            kept >= 0.9 * cut, "%d of %d points" % (kept, cut))
    r.check("and EA's solid texels solid in ours (>= 99%)", lost <= 0.01 * opaque, "%d of %d points opened" % (lost, opaque))
