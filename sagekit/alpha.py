"""Cut-out alpha, end to end.

The Elven, Isengard, Mordor and Angmar master sheets (EBFortress, IBFortress, MBFortress,
KBFortressB...) are DXT3/DXT5 with alpha: leaves, tracery and railings cut out of the sheet (1-8% of
the blocks; EBFortress's mean alpha is 0.98). The building pipeline used to see only their colour:
the upscale decoded with `-alpha off` and the painter wrote DXT1, so every hole would come back
solid. Now:

  extract  `upscale()` writes src/<sheet>_x4_alpha.png next to the colour upscale: the sheet's
           alpha resized like it (Lanczos; Real-ESRGAN sees colour only). Only when some texel is
           below opaque: a DXT3/5 sheet that is opaque throughout (DBStatue, EBBarracks) is DXT1 in
           all but name and gets no file, and no DXT1 building sheet of the game has punch-through
           alpha - so the Dwarven outputs are unchanged, bit for bit.
  bake     sagekit/blender/alpha.py bakes pass 'alpha': the sheet's alpha through the ATLAS layer for EA's
           faces, the faction atlas's for new faces (opaque if it has none), opaque on the atlas's
           `painted` regions (cloth: repainted, never EA's pixels).
  paint    the baked alpha, filled like the colour, written with it as DXT5 (painter.write_diffuse);
           the state variants (damaged, snow) take the same alpha, so the silhouette never changes.
  checks   sagekit/blender/alpha.py: our shipped texture is DXT5 exactly when an alpha bake exists, and wherever
           EA's triangles survive in our body, our alpha agrees with EA's at the same points.

Whether a mesh shows its alpha is the mesh's business (legacy shaders' alpha test, the FX shaders'
AlphaTestEnable); the pipeline keeps EA's shader chunks, so keeping the alpha keeps the look.
"""
import os
import subprocess
import tempfile

ALPHA_SUFFIX = "_alpha.png"
OPAQUE = 254 / 255                  # below this a texel is not opaque (DXT3's 4-bit steps included)


def path(upscale_png):
    """The alpha image beside a colour upscale (src/<sheet>_x4.png -> src/<sheet>_x4_alpha.png)."""
    return upscale_png[:-4] + ALPHA_SUFFIX


def fourcc(dds_bytes):
    return dds_bytes[84:88].decode("latin-1")


def upscale(dds_bytes, upscale_png, factor, ext=".dds"):
    """Write the sheet's alpha at the upscale's size when the sheet has any; remove a stale one.
    ext: the sheet's format, ".dds" or ".tga" (EA's TGA-only sheets: 32 bits carry alpha)."""
    out = path(upscale_png)
    has = dds_bytes[16] == 32 if ext == ".tga" else fourcc(dds_bytes) in ("DXT3", "DXT5")
    if not has:                                         # DXT1: no building sheet uses punch-through
        if os.path.exists(out):
            os.remove(out)
        return None
    if os.path.exists(out):
        return out
    with tempfile.TemporaryDirectory() as tmp:
        dds = os.path.join(tmp, "s" + ext)
        with open(dds, "wb") as fh:
            fh.write(dds_bytes)
        lo = float(subprocess.check_output(["magick", dds + "[0]", "-alpha", "extract", "-format", "%[fx:minima]", "info:"]))
        if lo >= OPAQUE:
            return None
        subprocess.check_call(["magick", dds + "[0]", "-alpha", "extract", "-filter", "Lanczos",
                               "-resize", "%d%%" % (100 * factor), "-depth", "8", out])
    return out


def expected(ws):
    """Does this building's own texture carry alpha? When the sheet it was painted from, or the
    faction atlas its new faces are mapped onto, has an alpha upscale."""
    b = ws.b
    have = os.path.exists(path(ws.atlas_upscale))
    return have or (b.two_sheets and os.path.exists(path(ws.master_upscale)))


def dds_fourcc(ws):
    return "DXT5" if expected(ws) else "DXT1"


def extra_bytes(b):
    """What DXT5 adds to the building's diffuse over the DXT1 the budget assumes (0 until extract
    has seen its sheets), so the memory budget counts it."""
    from . import paths
    from .formats.textures import dds_size, full_chain
    from .workspace import Workspace
    if not os.path.isdir(os.path.join(paths.work_dir(b.id), "src")) or not expected(Workspace(b)):
        return 0
    d = b.tier.diffuse
    return dds_size(d, d, full_chain(d), "DXT5") - dds_size(d, d, full_chain(d))
