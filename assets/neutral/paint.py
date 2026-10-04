"""The neutral paint: EA's own colours, graded rather than recoloured (style.py)."""
import numpy as np

from sagekit.paint.imageio import to_srgb
from sagekit.paint.layers import Layer

W = np.array([0.3, 0.59, 0.11], np.float32)


class Grade(Layer):
    """EA's painted sheet as the base colour, every texel, with a little more contrast about a
    mid grey and a little more colour, so the timber, stone and shingle EA painted read apart at
    the RTS camera (EA's sheet is low in both: olive boards and grey stone sit within a few
    percent of each other). Highlights warm slightly, shadows cool: daylight on old wood."""

    def __init__(self, contrast=1.24, mid=0.40, saturation=1.34, warm=0.04, lift=0.03):
        self.contrast, self.mid, self.saturation, self.warm, self.lift = contrast, mid, saturation, warm, lift

    def apply(self, col, cv, pal):
        return self.grade(to_srgb(cv.load("atlas")).astype(np.float32)[..., :3])

    def grade(self, a):
        """sRGB texels (..., 3) graded (the flat-sheet form: assets/scenery/paint.py)."""
        a = self.mid + (a - self.mid) * self.contrast + self.lift
        lum = (a @ W)[..., None]
        a = lum + (a - lum) * self.saturation
        k = np.clip(lum - 0.45, -0.45, 0.55)
        a = a + self.warm * k * np.array([1.0, 0.25, -0.9], np.float32)
        return np.clip(a, 0, 1)
