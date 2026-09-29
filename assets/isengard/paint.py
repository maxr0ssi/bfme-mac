"""Isengard's paint layers (built on first use: sagekit.paint needs numpy, on Blender's Python;
this module must import anywhere).

    IsengardRecolour  EA's sheet split into six materials and each painted through its own ramp of
                      the palette, by EA's luminance (every rib, rivet and crack survives):

        stone   the smooth wall panels (IsengardAtlas.materials "stone"): Orthanc's black stone
        rock    rough rock, earth, granite and cobbles ("rock")
        wood    planks, posts and crates ("wood")
        mark    the pale texels of the White Hand banner ("mark"); its dark field is stone
        fire    glowing coals and embers, wherever they are (orange, saturated, bright)
        silver  the brightest metal texels: the plates' lit rims, ribs and spike edges, polished
                silver-white (the palette's "silver" ramp)
        iron    everything else: the plates, ribs, spikes and frames

    Rects are read in the sheet's own pixels on a flat sheet and through the baked atlas
    coordinates (auv) on a building, so a new face sampling the panel region is stone too.
"""
import functools

# (gain, lift) from EA's luminance to the ramp's position: each material's range on IBFortress
# (p10..p90, measured 2026-09-28) lands on about 0.15..0.85 of its ramp
TONES = {"stone": (2.4, -0.25), "rock": (1.9, -0.03), "wood": (1.25, 0.14), "iron": (1.37, 0.095),
         "mark": (1.0, 0.0), "fire": (1.0, 0.0), "silver": (1.6, -0.35)}
SILVER = (0.40, 0.56)                       # EA's luminance over which a metal texel turns silver-white


@functools.lru_cache(maxsize=None)
def isengard_layers():
    import numpy as np

    from sagekit.paint.fields import hsv, ramp, smooth
    from sagekit.paint.layers import Layer, sheet_rgb

    def rect_weight(cv, rects):
        """1 inside the atlas rects (sheet pixels, y down): by pixel on a flat sheet (rows bottom-up),
        through the baked atlas coordinates on a building."""
        size = float(cv.atlas.size)
        if hasattr(cv, "load"):
            auv = np.mod(cv.load("auv"), 1.0)
            x, y = auv[..., 0] * size, (1 - auv[..., 1]) * size
        else:
            h, w = cv.lum.shape
            x = (np.arange(w, dtype=np.float32)[None, :] + 0.5) * size / w * np.ones((h, 1), np.float32)
            y = size - (np.arange(h, dtype=np.float32)[:, None] + 0.5) * size / h * np.ones((1, w), np.float32)
        m = np.zeros(x.shape, np.float32)
        for x0, y0, x1, y1 in rects:
            m = np.maximum(m, ((x >= x0) & (x < x1) & (y >= y0) & (y < y1)).astype(np.float32))
        return m

    class IsengardRecolour(Layer):
        def __init__(self, tones=None, ember=((0.0, 55.0), (0.45, 0.6), (0.30, 0.45)), silver=SILVER):
            self.tones = dict(TONES, **(tones or {}))
            self.silver = silver
            self.ember = ember                  # hue range, saturation and value ramps of the coals

        def weights(self, cv):
            def compute():
                H, S, V = hsv(sheet_rgb(cv))
                mats = getattr(cv.atlas, "materials", {})
                stone, rock, wood, mark = (rect_weight(cv, mats.get(k, ())) for k in ("stone", "rock", "wood", "mark"))
                (h0, h1), (s0, s1), (v0, v1) = self.ember
                fire = ((H >= h0) & (H <= h1) | (H >= 345)).astype(np.float32) * smooth(S, s0, s1) * smooth(V, v0, v1)
                pale = mark * smooth(V, 0.45, 0.6) * (1 - smooth(S, 0.25, 0.4))
                rest = 1 - fire
                stone = np.clip(stone + mark * (1 - pale), 0, 1) * rest
                rock, wood = rock * rest * (1 - stone), wood * rest * (1 - stone)
                white = pale * rest
                metal = np.clip(rest - stone - rock - wood - white, 0, 1)
                bright = smooth(np.clip(cv.lum, 0, 1), *self.silver) if self.silver else 0.0
                return dict(stone=stone, rock=rock, wood=wood, mark=white, fire=fire, iron=metal * (1 - bright),
                            silver=metal * bright)
            return cv.memo(("isengard_weights", id(self)), compute) if hasattr(cv, "memo") else compute()

        def apply(self, col, cv, pal):
            L = np.clip(cv.lum, 0, 1)
            w = self.weights(cv)
            out = np.zeros(L.shape + (3,), np.float32)
            for m, wm in w.items():
                g, k = self.tones[m]
                out += wm[..., None] * ramp(np.clip(L * g + k, 0, 1), pal[m])
            out = out / np.maximum(sum(w.values()), 1e-4)[..., None]
            painted = getattr(cv, "painted", 0.0)
            if col is None or not np.any(painted):
                return out
            p = np.asarray(painted, np.float32)[..., None]
            return out * (1 - p) + col * p

    return dict(IsengardRecolour=IsengardRecolour)
