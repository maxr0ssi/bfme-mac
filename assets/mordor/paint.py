"""Mordor's paint layers (built on first use: sagekit.paint needs numpy, on Blender's Python; this
module must import anywhere).

    MordorRecolour  EA's sheet split into six materials, each painted through its own ramp of the
                    palette by EA's luminance (every crack, rivet and rust fleck survives):

        stone   the smooth slabs (MordorAtlas.materials "stone"): basalt
        rock    rough rock and crags ("rock"), and the rock round the lava vein
        wood    the roof pyres' sticks ("wood"): charred timber
        fire    the lava vein and crumbs and the pyres' tips ("lava", "wood", by colour), and elsewhere only strongly
                saturated, bright red-orange texels (EA's rust flecks stay metal)
        trim    the brightest metal texels: lit blade edges, rims and ribs
        iron    everything else: plate, blades, spikes and frames
        slit    only when the palette has a "slit" ramp: the dark insides of the windows and slots
                ("slit" rects), lit through that ramp, darkest texel brightest (a glow, not paint)
        steel   only when the palette has a "steel" ramp: the brightest metal texels on the blades
                ("blade" rects: the spike rows, the blade finials, the crest and crown blades), where
                EA's sheet has its pale steel; the rest of those blades stays iron and trim

    Rock wins over stone where the rects overlap; lava over both. Rects are read in the sheet's
    own pixels on a flat sheet and through the baked atlas coordinates (auv) on a building.
"""
import functools

# (gain, lift) from EA's luminance to the ramp's position: each material's range on MBFortress
# (p10..p90 of the texels the body uses, measured 2026-09-30) lands on about 0.15..0.85 of its
# ramp; trim's 0.40..0.75 on 0.18..0.95; fire on 0.35..1 (it glows)
TONES = {"stone": (1.82, 0.03), "rock": (2.8, -0.14), "wood": (1.6, 0.05), "iron": (1.82, 0.03),
         "trim": (2.2, -0.7), "fire": (1.8, 0.2), "slit": (-2.4, 1.0), "steel": (1.3, -0.17)}
TRIM = (0.40, 0.56)                         # EA's luminance over which a metal texel is trim
LAVA_FIRE = ((0.45, 0.75), (0.18, 0.35))    # saturation and value ramps of the lava inside its rects
LOOSE_FIRE = ((0.72, 0.85), (0.45, 0.60))   # the same outside them: only true glow, not rust
SLIT = (0.16, 0.30)                         # EA's luminance over which a texel in a slit rect is lit less
STEEL = (0.48, 0.62)                        # EA's luminance over which a metal texel in a blade rect is steel


@functools.lru_cache(maxsize=None)
def mordor_layers():
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

    class MordorRecolour(Layer):
        def __init__(self, tones=None, trim=TRIM, steel=STEEL):
            self.tones = dict(TONES, **(tones or {}))
            self.trim, self.steel = trim, steel

        def weights(self, cv, slits=False, steel=False):
            def compute():
                H, S, V = hsv(sheet_rgb(cv))
                mats = getattr(cv.atlas, "materials", {})
                lava, rock, stone, wood = (rect_weight(cv, mats.get(k, ())) for k in ("lava", "rock", "stone", "wood"))
                glow = np.clip(lava + wood, 0, 1)
                red = ((H <= 45) | (H >= 345)).astype(np.float32)
                (s0, s1), (v0, v1) = LAVA_FIRE
                fire_in = glow * red * smooth(S, s0, s1) * smooth(V, v0, v1)
                (s0, s1), (v0, v1) = LOOSE_FIRE
                fire = fire_in + (1 - glow) * red * smooth(S, s0, s1) * smooth(V, v0, v1)
                slit = 0.0
                if slits:
                    slit = rect_weight(cv, mats.get("slit", ())) * (1 - smooth(cv.lum, *SLIT)) * (1 - fire)
                rest = 1 - fire - slit
                rough = np.clip(rock + lava, 0, 1)
                wood = wood * (1 - rough) * rest
                rock, stone = rough * rest, stone * (1 - rough) * rest
                metal = np.clip(rest - rock - stone - wood, 0, 1)
                lum = np.clip(cv.lum, 0, 1)
                bright = smooth(lum, *self.trim)
                w = dict(stone=stone, rock=rock, wood=wood, fire=fire, iron=metal * (1 - bright), trim=metal * bright)
                if steel:
                    s = rect_weight(cv, mats.get("blade", ())) * smooth(lum, *self.steel) * metal
                    w.update(trim=w["trim"] - s, steel=s)
                return dict(w, slit=slit) if slits else w
            key = ("mordor_weights", id(self), slits, steel)
            return cv.memo(key, compute) if hasattr(cv, "memo") else compute()

        def apply(self, col, cv, pal):
            L = np.clip(cv.lum, 0, 1)
            w = self.weights(cv, slits="slit" in pal.ramps, steel="steel" in pal.ramps)
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

    return dict(MordorRecolour=MordorRecolour)
