"""Angmar's paint layer (built on first use: sagekit.paint needs numpy, on Blender's Python; this
module must import anywhere).

    AngmarRecolour  EA's sheet split into materials by its table's rects (atlas.py materials for
                    KBFortress, atlas_sheets.py SHEETS for the other master sheets), each painted
                    through its own ramp of the palette at EA's luminance, so every block, frost
                    line and rivet survives:

        stone   blocks, rubble, slabs ("stone"): the palette's stone
        rock    ground ("rock")
        timber  the dark frost-grained wood ("timber"): its white frost lines reach the top of the
                ramp (rime)
        planks  warm boards and beams ("planks"): wood stays wood in every palette
        roof    the scale shingles ("roof")
        iron    plates and brackets ("iron"), and texels outside every rect
        trim    the brightest iron texels: lit metal edges
        rust    saturated orange texels on stone, rock and iron (EA's rust runs): by colour
        slit    only when the palette has a "slit" ramp: the dark insides of the slits ("slit"
                rects), lit through that ramp, darkest texel brightest (a glow, not paint)

    The palette's ramps keep EA's values: style.py builds every ramp from (position, luminance,
    hue) stops, so lights stay light and darks dark (Mordor's lesson). A palette may keep part of
    EA's own colour variation per material (Palette.chroma {material: amount}: EA's sheen on the
    shingles, the grain in the boards), added over the ramp's colour.

    A table of atlas_sheets.py (KBFortressB, KBFortressX, the production sheets, the bibs) may add:

        earth   ground, gravel, straw ("earth"): its own cold earth ramp (the table's ramps), EA's
                colour partly kept (the table's chroma), never rust
        glow    fire by colour in the "glow" rects (the forge's coals: warm, saturated, bright): the
                palette's "fire" ramp; the rest of those rects falls through to the next material
        ice     pale texels in the "ice" rects (the _ice sheets' crust) and, on a table with
                `frost`, pale unsaturated texels anywhere (the _snow and _ice sheets' snow and ice):
                the "ice" ramp (the tables' own pale blue-white), so they stay pale

    and its own ramps, tones and chroma over the palette's (the warm rust of every production sheet).
    KBFortress (the faction atlas) has none of these: the citadel's paint is unchanged, bit for bit.

    On a building, EA's faces (tag 0) read the building's own sheet's table when it has one
    (a wall on KBFortressB), new faces always KBFortress's (the faction atlas). Rects are read in
    the sheet's own pixels on a flat sheet and through the baked atlas coordinates (auv) on a
    building.
"""
import functools

# (gain, lift) from EA's luminance to each ramp's position (measured 2026-10-01 on KBFortress, p10..p90:
# stone 0.08..0.73, timber 0.06..0.54, planks 0.18..0.64, shingles 0.09..0.63): the stone, planks and
# roof keep EA's luminance as position; timber and iron spread so their brightest reach rime and edge
TONES = {"stone": (1.0, 0.0), "rock": (1.1, 0.0), "timber": (1.35, 0.0), "planks": (1.0, 0.0), "roof": (1.05, 0.0),
         "iron": (1.5, 0.0), "trim": (1.0, 0.0), "rust": (1.5, 0.0), "slit": (-2.4, 1.0),
         "earth": (1.0, 0.0), "ice": (1.0, 0.0), "glow": (1.2, 0.1)}
TRIM = (0.50, 0.66)                         # EA's luminance over which an iron texel is an edge (trim)
RUST = ((0.26, 0.42), (0.12, 0.24))         # saturation and value ramps of a rust texel (hue <= 40 or >= 345)
SLIT = (0.12, 0.26)                         # EA's luminance over which a texel in a slit rect is lit less
RUSTED = ("stone", "rock", "iron")          # the materials rust runs on
ORDER = ("stone", "rock", "timber", "planks", "roof", "iron", "trim", "rust", "slit")
OVERLAYS = ("slit", "ice", "glow")          # gated by value or colour over the rest, not in the rects' priority
RAMP_OF = {"glow": "fire"}                  # material -> palette ramp, where the names differ
ICE = (0.25, 0.45)                          # EA's luminance over which a texel in an "ice" rect is ice
FROST = ((0.50, 0.72), (0.10, 0.22))        # luminance and saturation ramps of a frost texel (`frost` tables)
GLOW = ((0.20, 0.40), (0.20, 0.45))         # saturation and value ramps of a glow texel (warm hue)


@functools.lru_cache(maxsize=None)
def angmar_layers():
    import numpy as np

    from sagekit.paint.fields import hsv, ramp, smooth
    from sagekit.paint.layers import Layer, sheet_rgb

    def rects(cv, atlas, rs):
        """1 inside the rects (the atlas's sheet px, y down): by pixel on a flat sheet (rows
        bottom-up), through the baked atlas coordinates on a building."""
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

    class AngmarRecolour(Layer):
        def __init__(self, atlas=None, sheet_atlas=None):
            self.atlas, self.sheet_atlas = atlas, sheet_atlas      # the faction's, a building's own sheet's

        def weights(self, cv, atlas, lit):
            """{material: weight} of every texel read through `atlas`'s table (all stone without one)."""
            rgb = sheet_rgb(cv)
            H, S, V = hsv(rgb)
            lum = np.clip(cv.lum, 0, 1)
            mats = getattr(atlas, "materials", None) or {"stone": [(0, 0, atlas.size or 1024, atlas.size or 1024)]}
            left = np.ones(lum.shape, np.float32)
            got = {}
            for k, rs in mats.items():
                if k not in OVERLAYS:
                    r = rects(cv, atlas, rs) * left
                    got[k] = got.get(k, 0.0) + r
                    left = left - r
            got["iron"] = got.get("iron", 0.0) + left                   # outside every rect: metal
            (s0, s1), (v0, v1) = RUST
            orange = ((H <= 40) | (H >= 345)).astype(np.float32) * smooth(S, s0, s1) * smooth(V, v0, v1)
            rust = sum(got.get(k, 0.0) for k in RUSTED) * orange
            edge = smooth(lum, *TRIM)
            w = {k: got.get(k, 0.0) * (1 - orange) if k in RUSTED else got.get(k, 0.0) for k in ORDER[:6]}
            w.update(trim=w["iron"] * edge, rust=rust)
            w["iron"] = w["iron"] * (1 - edge)
            w.update({k: v for k, v in got.items() if k not in w})              # a table's own: earth
            dark = rects(cv, atlas, mats.get("slit", ())) * (1 - smooth(lum, *SLIT)) if lit else 0.0
            w = {k: v * (1 - dark) for k, v in w.items() if np.any(v)}
            if np.any(dark):
                w["slit"] = dark
            over = self.overlays(cv, atlas, mats, H, S, V, lum) if "ice" in mats or "glow" in mats or \
                getattr(atlas, "frost", False) else {}
            if over:                                                    # never on KBFortress (bit-identical)
                cover = sum(over.values())
                w = {k: v * (1 - cover) for k, v in w.items()}
                w.update(over)
            return w, rgb, lum

        def overlays(self, cv, atlas, mats, H, S, V, lum):
            """{ice, glow} over everything else: ice where pale in the ice rects and, on a `frost`
            table, wherever pale and unsaturated; glow where warm, saturated and bright in its rects."""
            ice = rects(cv, atlas, mats.get("ice", ())) * smooth(lum, *ICE)
            if getattr(atlas, "frost", False):
                (l0, l1), (s0, s1) = FROST
                ice = np.maximum(ice, smooth(lum, l0, l1) * (1 - smooth(S, s0, s1)))
            (s0, s1), (v0, v1) = GLOW
            warm = ((H <= 60) | (H >= 345)).astype(np.float32)
            glow = rects(cv, atlas, mats.get("glow", ())) * warm * smooth(S, s0, s1) * smooth(V, v0, v1) * (1 - ice)
            return {k: v for k, v in (("ice", ice), ("glow", glow)) if np.any(v)}

        def paint(self, cv, atlas, pal):
            w, rgb, L = self.weights(cv, atlas, "slit" in pal.ramps)
            chroma = dict(getattr(pal, "chroma", {}), **(getattr(atlas, "chroma", None) or {}))
            tones = dict(TONES, **(getattr(atlas, "tones", None) or {}))
            ramps = getattr(atlas, "ramps", None) or {}                 # a table's own over the palette's
            out = np.zeros(L.shape + (3,), np.float32)
            for m, wm in w.items():
                g, k = tones[m]
                c = ramp(np.clip(L * g + k, 0, 1), ramps.get(m) or pal[RAMP_OF.get(m, m)])
                if chroma.get(m):
                    c = c + chroma[m] * (rgb - L[..., None])            # EA's own colour variation
                out += np.asarray(wm, np.float32)[..., None] * c
            return np.clip(out / np.maximum(sum(w.values()), 1e-4)[..., None], 0, 1)

        def apply(self, col, cv, pal):
            atlas = self.atlas or cv.atlas
            if hasattr(cv, "load"):                                    # a building
                out = cv.memo(("angmar_paint", id(self), id(pal)), lambda: self.paint(cv, atlas, pal))
                if self.sheet_atlas is not None:                       # EA's faces on a sheet of their own
                    own = cv.memo(("angmar_own", id(self), id(pal)), lambda: self.paint(cv, self.sheet_atlas, pal))
                    o = (cv.tagi == 0).astype(np.float32)[..., None]
                    out = own * o + out * (1 - o)
                painted = getattr(cv, "painted", 0.0)
                if col is None or not np.any(painted):
                    return out
                p = np.asarray(painted, np.float32)[..., None]
                return out * (1 - p) + col * p
            return self.paint(cv, getattr(cv, "atlas", None) or atlas, pal)    # a flat sheet: its own table

    return dict(AngmarRecolour=AngmarRecolour)
