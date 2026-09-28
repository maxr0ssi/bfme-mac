"""The walls group's paint layer (built on first use: sagekit.paint needs numpy, on Blender's Python;
this module must import anywhere). Owned by the walls group; added through Building.decals().

    MortarBoost  EA's own mortar joints and cracks made crisp again on the white stone: the
                 recolour lifts EA's dark ashlar to white limestone and its joints fade with it,
                 so the normal map's bevelled blocks read as soft pillows (smeared, stretched
                 stone). Texels darker than their neighbourhood in EA's sheet (a high-pass of
                 the sheet's luminance, per texel of our layout) darken toward the palette's
                 groove colour and sink a little in the normal map. It follows EA's joints
                 exactly: nothing new is drawn, EA's blocks just read as EA drew them.
"""
import functools


@functools.lru_cache(maxsize=None)
def wall_layers():
    import numpy as np

    from sagekit.paint.fields import smooth
    from sagekit.paint.layers import Layer

    def box(a, r):
        """Box blur of a 2D array (edge-clamped), radius r texels."""
        p = np.pad(a, r + 1, mode="edge").astype(np.float64)
        c = p.cumsum(0).cumsum(1)
        k = 2 * r + 1
        s = c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]
        return (s / (k * k))[:a.shape[0], :a.shape[1]].astype(np.float32)

    class MortarBoost(Layer):
        def __init__(self, radius=4, lo=0.015, hi=0.09, strength=0.65, depth=0.14):
            self.radius, self.lo, self.hi, self.strength, self.depth = radius, lo, hi, strength, depth

        def mask(self, cv):
            def compute():
                cov = cv.covm
                lum = cv.lum * cov
                mean = box(lum, self.radius) / np.maximum(box(cov, self.radius), 1e-3)
                m = smooth(mean - cv.lum, self.lo, self.hi) * cov * cv.w_stone
                return m.astype(np.float32)
            return cv.memo(("mortarboost", id(self)), compute)

        def apply(self, col, cv, pal):
            g = (self.strength * self.mask(cv))[..., None]
            return col * (1 - g) + np.array(pal["groove"], np.float32) * g

        def height(self, cv, ds):
            return ds(-self.depth * self.mask(cv))

    return MortarBoost
