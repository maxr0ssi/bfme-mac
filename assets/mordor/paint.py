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


@functools.lru_cache(maxsize=None)
def mordor_sheet_layers():
    """MordorSheetRecolour: MordorRecolour for the buildings whose EA faces paint from a sheet of
    their own (assets/mordor/atlas_sheets.py SHEETS). On a building EA's faces (tag 0) take that
    sheet's material rects, tones and ramps through their own UVs, new faces MBFortress's as before;
    on a flat sheet with a table (`own_sheet`) its rects. Rects in the table's order (the first
    material listed whose rect a texel falls in wins; slits lie over the rest); fire by colour only in glow and lava rects and, strongly saturated
    and bright, outside every rect; slits lit where dark; the rest of the sheet iron or trim. With no
    table it is MordorRecolour, bit for bit (the citadel's paths never reach the tables)."""
    import numpy as np

    from sagekit.paint.fields import hsv, ramp, smooth
    from sagekit.paint.layers import sheet_rgb

    from .atlas_sheets import RAMP_OF

    base = mordor_layers()["MordorRecolour"]
    MATERIALS = ("glow", "lava", "blade", "bone", "flesh", "hide", "accent", "brass", "cloth", "wood", "trim",
                 "iron", "mud", "rock", "stone")

    def rects(cv, atlas, rs):
        """1 inside the rects (atlas's sheet px, y down): by pixel on a flat sheet (rows bottom-up),
        through the baked atlas coordinates on a building."""
        size = float(atlas.size)
        if hasattr(cv, "load"):
            auv = np.mod(cv.load("auv"), 1.0)
            x, y = auv[..., 0] * size, (1 - auv[..., 1]) * size
        else:
            h, w = cv.lum.shape
            x = (np.arange(w, dtype=np.float32)[None, :] + 0.5) * size / w * np.ones((h, 1), np.float32)
            y = size - (np.arange(h, dtype=np.float32)[:, None] + 0.5) * size / h * np.ones((1, w), np.float32)
        m = np.zeros(x.shape, np.float32)
        for x0, y0, x1, y1 in rs:
            m = np.maximum(m, ((x >= x0) & (x < x1) & (y >= y0) & (y < y1)).astype(np.float32))
        return m

    class MordorSheetRecolour(base):
        def __init__(self, sheet_atlas=None, **kw):
            super().__init__(**kw)
            self.sheet_atlas = sheet_atlas

        def own(self, cv, atlas, pal):
            """The weights of texels read on a sheet with a table (those the palette has ramps for)."""
            H, S, V = hsv(sheet_rgb(cv))
            lum = np.clip(cv.lum, 0, 1)
            mats = atlas.materials
            left = np.ones(lum.shape, np.float32)
            got = {k: 0.0 for k in MATERIALS}
            for k, rs in mats.items():
                if k != "slit":
                    r = rects(cv, atlas, rs)
                    got[k] = got[k] + r * left
                    left = left * (1 - r)
            red = ((H <= 45) | (H >= 345)).astype(np.float32)
            (s0, s1), (v0, v1) = LAVA_FIRE
            lava = got["lava"] * red * smooth(S, s0, s1) * smooth(V, v0, v1)
            warm = ((H <= 60) | (H >= 345)).astype(np.float32)
            glow = got["glow"] * warm * smooth(S, 0.25, 0.45) * smooth(V, 0.55, 0.8)
            (s0, s1), (v0, v1) = LOOSE_FIRE
            loose = left * red * smooth(S, s0, s1) * smooth(V, v0, v1)
            fire = lava + glow + loose
            dark = rects(cv, atlas, mats.get("slit", ())) * (1 - smooth(lum, *SLIT)) * (1 - fire)
            slit = dark if "slit" in pal.ramps else 0.0
            keep = 1 - dark
            harad = 1.0 if "paint" in atlas.ramps else 0.0      # red texels war-paint, yellow ones gold
            paint = got["accent"] * harad * smooth(S, 0.55, 0.7) * ((H <= 20) | (H >= 330))
            brass = got["brass"] + got["accent"] * harad * smooth(S, 0.3, 0.45) * ((H >= 42) & (H <= 90))
            metal = got["iron"] + got["glow"] - glow + left - loose
            edge = smooth(lum, *self.trim)
            steel = got["blade"] * smooth(lum, *self.steel) if "steel" in pal.ramps else 0.0
            blade = got["blade"] - steel
            w = dict(fire=fire, stone=got["stone"], rock=got["rock"] + got["lava"] - lava, mud=got["mud"],
                     wood=got["wood"], cloth=got["cloth"] + got["accent"] - paint - (brass - got["brass"]),
                     bone=got["bone"], flesh=got["flesh"], hide=got["hide"], paint=paint, brass=brass,
                     iron=(metal + blade) * (1 - edge), trim=(metal + blade) * edge + got["trim"], steel=steel)
            w = {k: v * keep for k, v in w.items() if np.any(v)}
            if np.any(slit):
                w["slit"] = slit
            return w

        def paint(self, cv, atlas, pal):
            """EA's sheet painted from its own table: each material through its ramp (the table's
            ramps first, then the palette's) at the table's tones."""
            L = np.clip(cv.lum, 0, 1)
            w = self.own(cv, atlas, pal)
            out = np.zeros(L.shape + (3,), np.float32)
            for m, wm in w.items():
                g, k = atlas.tones[m]
                stops = atlas.ramps.get(m) or pal[RAMP_OF.get(m, m)]
                out += np.asarray(wm, np.float32)[..., None] * ramp(np.clip(L * g + k, 0, 1), stops)
            return out / np.maximum(sum(w.values()), 1e-4)[..., None]

        def apply(self, col, cv, pal):
            if hasattr(cv, "load") and self.sheet_atlas is not None:      # a building on its own sheet
                old = cv.memo(("mordor_sheet_paint", id(self), id(pal)), lambda: self.paint(cv, self.sheet_atlas, pal))
                o = (cv.tagi == 0).astype(np.float32)[..., None]
                return old * o + base.apply(self, col, cv, pal) * (1 - o)
            atlas = getattr(cv, "atlas", None)
            if not hasattr(cv, "load") and getattr(atlas, "own_sheet", False):   # a flat sheet with a table
                return self.paint(cv, atlas, pal)
            return base.apply(self, col, cv, pal)                          # MBFortress, flat or not: unchanged

    return dict(MordorSheetRecolour=MordorSheetRecolour)
