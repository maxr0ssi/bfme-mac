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

    IsengardSheetRecolour  the same for the buildings on sheets of their own (atlas.py SHEETS):
                      EA's faces read their own sheet's rects, new faces IBFortress's.

    IsengardOcclusion  sagekit's Occlusion, but EA's ground decals modelled facing down keep no
                      AO (it was baked from under the ground).
"""
import functools

# (gain, lift) from EA's luminance to the ramp's position: each material's range on IBFortress
# (p10..p90, measured 2026-09-28) lands on about 0.15..0.85 of its ramp; rock 1:1 (its ramp is
# built on EA's luminance: the own sheets' earth runs up to 0.7, which a gain would clip)
TONES = {"stone": (2.4, -0.25), "rock": (1.0, 0.0), "wood": (1.25, 0.14), "iron": (1.37, 0.095),
         "mark": (1.0, 0.0), "fire": (1.0, 0.0), "silver": (1.6, -0.35)}
SILVER = (0.40, 0.56)                       # EA's luminance over which a metal texel turns silver-white


@functools.lru_cache(maxsize=None)
def isengard_layers():
    import numpy as np

    from sagekit.paint.fields import hsv, ramp, smooth
    from sagekit.paint.layers import Layer, Occlusion, sheet_rgb

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

    def ground_decal(cv):
        """EA's faces lying flat on the ground (z = 0): ground decals such as the warg sentry's disc."""
        return (cv.tagi == 0) & (np.abs(cv.nrm[..., 2]) > 0.9) & (np.abs(cv.pos[..., 2]) < 0.3)

    class IsengardOcclusion(Occlusion):
        """Occlusion, except on EA's ground decals modelled facing down (the warg sentry's disc, the
        armory's floor): their AO was baked from below the ground, black, which darkened them to
        0.38 of their paint; the game draws them from above, open to the sky. Faces there whose AO
        is not black (undersides seen from below) keep it, and so does all but rock (the recolour's
        weights): built faces there, on the citadel and the walls, stay as they were."""

        def __init__(self, recolour):
            self.recolour = recolour

        def apply(self, col, cv, pal):
            f = (ground_decal(cv) & (cv.nrm[..., 2] < 0)) * (1 - smooth(cv.ao_s, 0.05, 0.2))
            f = f * self.recolour.weights(cv)["rock"]
            ao_s, ao_l = cv.ao_s + (1 - cv.ao_s) * f, cv.ao_l + (1 - cv.ao_l) * f
            ao = np.power(ao_s, 0.7) * (0.66 + 0.34 * ao_l)
            occ = np.array(pal["occl"], np.float32) * 0.6 + 0.4
            return col * (occ + (1 - occ) * ao[..., None]) * (0.88 + 0.12 * ao[..., None])

    return dict(IsengardRecolour=IsengardRecolour, IsengardOcclusion=IsengardOcclusion, ground_decal=ground_decal)


@functools.lru_cache(maxsize=None)
def isengard_sheet_layers():
    """IsengardSheetRecolour: IsengardRecolour for the buildings whose EA faces paint from a sheet of
    their own (assets/isengard/atlas.py SHEETS). On a building EA's faces (tag 0) take that sheet's
    material rects through their own UVs, new faces IBFortress's as before; on a flat sheet with a
    table (`own_sheet`) its rects. Rects in priority order (iron, mark, stone, rock, wood: the first
    one a texel falls in wins); fire by colour only outside every rect; the rest iron or silver.
    With no table it is IsengardRecolour, bit for bit (the citadel's paths never reach it)."""
    import numpy as np

    from sagekit.paint.fields import hsv, smooth
    from sagekit.paint.layers import sheet_rgb

    base = isengard_layers()["IsengardRecolour"]
    ORDER = ("iron", "mark", "stone", "rock", "wood")

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

    class IsengardSheetRecolour(base):
        def __init__(self, sheet_atlas=None, **kw):
            super().__init__(**kw)
            self.sheet_atlas = sheet_atlas

        def own(self, cv, atlas):
            """The weights of texels read on a sheet with a table."""
            H, S, V = hsv(sheet_rgb(cv))
            mats = atlas.materials
            left = np.ones(cv.lum.shape, np.float32)
            got = {}
            for k in ORDER:
                r = rects(cv, atlas, mats.get(k, ()))
                got[k] = r * left
                left = left * (1 - r)
            (h0, h1), (s0, s1), (v0, v1) = self.ember
            fire = ((H >= h0) & (H <= h1) | (H >= 345)).astype(np.float32) * smooth(S, s0, s1) * smooth(V, v0, v1) * left
            pale = got["mark"] * smooth(V, 0.45, 0.6) * (1 - smooth(S, 0.25, 0.4))
            metal = got["iron"] + left - fire
            bright = smooth(np.clip(cv.lum, 0, 1), *self.silver) if self.silver else 0.0
            return dict(stone=got["stone"] + got["mark"] - pale, rock=got["rock"], wood=got["wood"], mark=pale, fire=fire,
                        iron=metal * (1 - bright), silver=metal * bright)

        def weights(self, cv):
            if hasattr(cv, "load") and self.sheet_atlas is not None:      # a building on its own sheet
                def compute():
                    new = base.weights(self, cv)
                    old = self.own(cv, self.sheet_atlas)
                    # EA's ground decals (flat on z = 0: the warg sentry's disc) are earth: a mark
                    # rect there (its bones and their dark ground) paints as rock, not Orthanc stone
                    # and bone-white
                    g = isengard_layers()["ground_decal"](cv).astype(np.float32)
                    old["rock"] = old["rock"] + (old["stone"] + old["mark"]) * g
                    old["stone"], old["mark"] = old["stone"] * (1 - g), old["mark"] * (1 - g)
                    o = (cv.tagi == 0).astype(np.float32)
                    return {k: old[k] * o + new[k] * (1 - o) for k in new}
                return cv.memo(("isengard_sheet_weights", id(self)), compute)
            atlas = getattr(cv, "atlas", None)
            if not hasattr(cv, "load") and getattr(atlas, "own_sheet", False):   # a flat sheet with a table
                return self.own(cv, atlas)
            return base.weights(self, cv)                                   # IBFortress, flat or not: unchanged

        def apply(self, col, cv, pal):
            """A sheet's own tones (atlas.py SHEETS, a third item): on a building for EA's faces only,
            on a flat sheet for all of it."""
            atlas = self.sheet_atlas if hasattr(cv, "load") else getattr(cv, "atlas", None)
            tones = getattr(atlas, "tones", None)
            if not tones:
                return base.apply(self, col, cv, pal)
            plain = base.apply(self, col, cv, pal) if hasattr(cv, "load") else None
            keep, self.tones = self.tones, dict(self.tones, **tones)
            try:
                toned = base.apply(self, col, cv, pal)
            finally:
                self.tones = keep
            if plain is None:
                return toned
            o = (cv.tagi == 0).astype(np.float32)[..., None]
            return toned * o + plain * (1 - o)

    return dict(IsengardSheetRecolour=IsengardSheetRecolour)
