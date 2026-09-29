"""One palette option on a faction's sheet, for `sagekit palettes` (sagekit/palettes.py): EA's
sheet upscaled 4x (Real-ESRGAN, when it is there), passed through the style's flat-sheet layers
with the style's palette swapped for `palettes[key]`, and written as a PNG at SIZE with EA's
alpha kept. Runs on Blender's bundled Python (numpy), no Blender needed:

    python3.11 -m sagekit.paint.palette <faction> <palette key> <in.dds> <out.png> [upscaler]
"""
import os
import subprocess
import sys

SIZE = 2048                                 # the recoloured sheet's size for the renders


def recolour(faction, key, src, out, upscaler=None):
    """EA's sheet `src` recoloured with palette `key` of the faction's style into `out` (PNG,
    EA's alpha kept)."""
    import tempfile

    import numpy as np

    from ..__main__ import _style
    from ..formats.textures import MAGICK
    from .sheets import SheetCanvas, keep_motifs, read_rgba, write_png
    style = _style(faction)
    style.palette = style.palettes[key]
    with tempfile.TemporaryDirectory() as tmp:
        png, up = os.path.join(tmp, "src.png"), os.path.join(tmp, "up.png")
        subprocess.check_call([MAGICK, src + "[0]", "-alpha", "off", png])
        if upscaler and os.path.exists(upscaler):
            subprocess.check_call([upscaler, "-i", png, "-o", up, "-n", "realesrgan-x4plus",
                                   "-m", os.path.join(os.path.dirname(upscaler), "models")],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            up = png
        subprocess.check_call([MAGICK, up, "-filter", "Lanczos", "-resize", "%dx%d!" % (SIZE, SIZE), up])
        rgb = read_rgba(up)[..., :3]
        cv = SheetCanvas(rgb[::-1].copy(), style.sheet_atlas(os.path.basename(src)))
        col = None
        for layer in style.sheet_layers():
            col = layer.apply(col, cv, style.palette)
        col = np.clip(keep_motifs(col, cv), 0, 1)[::-1]
        a = os.path.join(tmp, "a.png")
        subprocess.check_call([MAGICK, src + "[0]", "-alpha", "extract", "-filter", "Lanczos",
                               "-resize", "%dx%d!" % (SIZE, SIZE), a])
        alpha = read_rgba(a)[..., :1]
        write_png(np.concatenate([col, alpha], -1), out)


if __name__ == "__main__":
    recolour(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5] if len(sys.argv) > 5 else None)
