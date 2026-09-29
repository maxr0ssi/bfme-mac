"""The Goblins' paint layers (built on first use: sagekit.paint needs numpy, on Blender's Python;
this module must import anywhere).

    GoblinRecolour  EA's sheet split into six materials and each painted through its own ramp of the
                    palette, by EA's luminance (so every painted crack, scale and rivet survives):

        rock    dark, unsaturated texels and the cool blue-grey ones: the rock curtains, shadowed stone
        bone    pale, weakly saturated texels: tusks, spikes, skulls, the horn bands' highlights
        hide    everything else that is warm: the carved horn and hide plates, the dragon head
        stone   the block masonry (GoblinAtlas.materials "brick")
        wood    the riveted planks ("timber")
        iron    the beaten plates and bars ("iron")

    The rect materials are read in the sheet's own pixels on a flat sheet and through the baked
    atlas coordinates (auv) on a building, so a new face sampling the brick region is stone too.
    Rock takes precedence over brick (the dark joints and the curtains inside a block panel).
    New faces of the atlas's painted regions (iron, cloth) are left to the TagRamps.

    Gore            dried blood round a building's trophies (Building.decals: anchors from its
                    recipe) and thin drips down every crimson face under a ledge.
"""
import functools

# (gain, lift) from EA's luminance to the ramp's position, per material: each material's own
# luminance range on WBFortress (p10..p90) lands on its ramp's 0.15..0.85
TONES = {"rock": (2.2, 0.0), "bone": (1.15, -0.05), "hide": (1.7, -0.08), "stone": (1.6, -0.12),
         "wood": (1.8, -0.1), "iron": (1.7, -0.05)}


@functools.lru_cache(maxsize=None)
def goblin_layers():
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

    class GoblinRecolour(Layer):
        def __init__(self, tones=None, rock=((0.24, 0.40), (0.20, 0.34)), bone=((0.40, 0.56), (0.30, 0.46))):
            self.tones = dict(TONES, **(tones or {}))
            self.rock, self.bone = rock, bone

        def weights(self, cv):
            def compute():
                H, S, V = hsv(sheet_rgb(cv))
                mats = getattr(cv.atlas, "materials", {})
                timber, brick, iron = (rect_weight(cv, mats.get(k, ())) for k in ("timber", "brick", "iron"))
                (v0, v1), (s0, s1) = self.rock
                rock = (1 - smooth(V, v0, v1)) * (1 - smooth(S, s0, s1))
                cool = smooth(H, 150, 175) * (1 - smooth(H, 265, 290))       # the curtains' blue-grey
                rock = np.maximum(rock, cool * (1 - smooth(S, 0.30, 0.42)) * (1 - smooth(V, 0.50, 0.62)))
                (l0, l1), (b0, b1) = self.bone
                bone = smooth(V, l0, l1) * (1 - smooth(S, b0, b1))
                fixed = np.clip(timber + iron, 0, 1)
                rock = rock * (1 - fixed)
                stone = brick * (1 - fixed) * (1 - rock)
                rest = (1 - fixed) * (1 - rock) * (1 - stone)
                return dict(wood=timber * (1 - iron), iron=iron, rock=rock, stone=stone,
                            bone=rest * bone, hide=rest * (1 - bone))
            return cv.memo(("goblin_weights", id(self)), compute) if hasattr(cv, "memo") else compute()

        def apply(self, col, cv, pal):
            L = np.clip(cv.lum, 0, 1)
            w = self.weights(cv)
            out = np.zeros(L.shape + (3,), np.float32)
            for m, wm in w.items():
                g, k = self.tones[m]
                out += wm[..., None] * ramp(np.clip(L * g + k, 0, 1), pal[m])
            tot = sum(w.values())[..., None]
            out = out / np.maximum(tot, 1e-4)
            painted = getattr(cv, "painted", 0.0)
            if col is None or not np.any(painted):
                return out
            p = np.asarray(painted, np.float32)[..., None]
            return out * (1 - p) + col * p

    class Gore(Layer):
        """Dried blood, stylised for the RTS camera: a dark stain round each anchor (x, y, z,
        radius, run) - a skull on a spike, an impaled body, a pile - with drips running `run` down
        from it in uneven streaks; and thin drips down every crimson face under a ledge."""

        def __init__(self, anchors, spot=0.13, amount=0.9, ledge=0.55):
            self.anchors, self.spot, self.amount, self.ledge = list(anchors), spot, amount, ledge

        def mask(self, cv):
            def compute():
                pos = cv.pos
                streak = cv.streak_noise
                m = np.zeros(pos.shape[:2], np.float32)
                for x, y, z, r, run in self.anchors:
                    near = (np.abs(pos[..., 0] - x) < r * 1.5 + 1) & (np.abs(pos[..., 1] - y) < r * 1.5 + 1)
                    if not near.any():
                        continue
                    hz = np.hypot(pos[..., 0] - x, pos[..., 1] - y)
                    dz = pos[..., 2] - z
                    stain = (1 - smooth(np.hypot(hz, dz * 1.3), r * 0.45, r)) * (0.65 + 0.35 * cv.fine)
                    reach = run * (0.25 + 0.75 * smooth(streak, 0.35, 0.8))
                    drip = (1 - smooth(hz, r * 0.5, r * 1.05)) * smooth(streak, 0.45, 0.6) * (dz < 0.2) * \
                        (1 - smooth(-dz, reach * 0.6, reach + 0.01))
                    m = np.maximum(m, near * np.clip(np.maximum(stain, drip), 0, 1))
                return m
            return cv.memo(("goblin_gore", id(self)), compute)

        def apply(self, col, cv, pal):
            blood = ramp(np.full(col.shape[:2], self.spot, np.float32) * (0.8 + 0.4 * cv.fine), pal["hide"])
            m = self.mask(cv) * self.amount
            red = smooth(col[..., 0] - np.maximum(col[..., 1], col[..., 2]), 0.06, 0.18)
            runs = cv.ledge * smooth(cv.streak_noise, 0.58, 0.8) * red * self.ledge
            k = np.clip(np.maximum(m, runs), 0, 1)[..., None]
            return col * (1 - k) + blood * k

    return dict(GoblinRecolour=GoblinRecolour, Gore=Gore)


@functools.lru_cache(maxsize=None)
def goblin_sheet_layers():
    """GoblinSheetRecolour: GoblinRecolour for the production group, whose EA faces paint from a
    sheet of their own (assets/goblins/atlas.py SHEETS): on a building EA's faces (tag 0) take that
    sheet's material rects and new faces WBFortress's; on a flat sheet the canvas's atlas is the
    sheet's own. Inside a "rock" rect the texel is rock whatever its colour. With no sheet table
    and no rock rects it is GoblinRecolour, bit for bit (the citadel's and throne's paths never
    reach it)."""
    import numpy as np

    base = goblin_layers()["GoblinRecolour"]

    class _On:
        """The canvas seen through another atlas (its own memo keys for the weights)."""

        def __init__(self, cv, atlas, tag):
            self._cv, self.atlas, self._tag = cv, atlas, tag

        def __getattr__(self, name):
            return getattr(self._cv, name)

        def memo(self, key, fn):
            return self._cv.memo((self._tag,) + tuple(key) if isinstance(key, tuple) else key, fn)

    def rects(cv, atlas, names):
        """1 inside the atlas's rects of those materials (sheet px, y down)."""
        size = float(atlas.size)
        if hasattr(cv, "load"):
            auv = np.mod(cv.load("auv"), 1.0)
            x, y = auv[..., 0] * size, (1 - auv[..., 1]) * size
        else:
            h, w = cv.lum.shape
            x = (np.arange(w, dtype=np.float32)[None, :] + 0.5) * size / w * np.ones((h, 1), np.float32)
            y = size - (np.arange(h, dtype=np.float32)[:, None] + 0.5) * size / h * np.ones((1, w), np.float32)
        m = np.zeros(x.shape, np.float32)
        for n in names:
            for x0, y0, x1, y1 in getattr(atlas, "materials", {}).get(n, ()):
                m = np.maximum(m, ((x >= x0) & (x < x1) & (y >= y0) & (y < y1)).astype(np.float32))
        return m

    def rock_wins(w, rk):
        out = {k: v * (1 - rk) for k, v in w.items()}
        out["rock"] = out["rock"] + rk
        return out

    class GoblinSheetRecolour(base):
        def __init__(self, sheet_atlas=None, **kw):
            super().__init__(**kw)
            self.sheet_atlas = sheet_atlas

        def weights(self, cv):
            if hasattr(cv, "load") and self.sheet_atlas is not None:      # a building on its own sheet
                def compute():
                    new = base.weights(self, _On(cv, cv.atlas, "new"))
                    old = base.weights(self, _On(cv, self.sheet_atlas, "old"))
                    old = rock_wins(old, rects(cv, self.sheet_atlas, ("rock",)))
                    o = (cv.tagi == 0).astype(np.float32)
                    return {k: old[k] * o + new[k] * (1 - o) for k in new}
                return cv.memo(("goblin_sheet_weights", id(self)), compute)
            w = base.weights(self, cv)
            if not getattr(cv, "atlas", None) or "rock" not in getattr(cv.atlas, "materials", {}):
                return w                                                  # WBFortress, flat or not: unchanged
            return rock_wins(w, rects(cv, cv.atlas, ("rock",)))

        def apply(self, col, cv, pal):
            """The sheet's own tones (atlas.py SHEETS): on a building for EA's faces only (new faces
            painted as a material are the TagRamps' anyway) unless the tones say "all", on a flat
            sheet for all of it."""
            atlas = self.sheet_atlas if hasattr(cv, "load") else getattr(cv, "atlas", None)
            tones = getattr(atlas, "tones", None)
            if not tones:
                return base.apply(self, col, cv, pal)
            everywhere = tones.get("all", False)
            plain = None if everywhere else base.apply(self, col, cv, pal)
            keep, self.tones = self.tones, dict(self.tones, **{k: v for k, v in tones.items() if k not in ("all", "ramps")})
            ramps = tones.get("ramps") or {}
            own = type(pal)(pal.name, dict(pal.ramps, **ramps), pal.accents, pal.tints) if ramps else pal
            try:
                toned = base.apply(self, col, cv, own)
            finally:
                self.tones = keep
            if everywhere or not hasattr(cv, "load"):
                return toned
            o = (cv.tagi == 0).astype(np.float32)[..., None]
            return toned * o + plain * (1 - o)

    return dict(GoblinSheetRecolour=GoblinSheetRecolour)
