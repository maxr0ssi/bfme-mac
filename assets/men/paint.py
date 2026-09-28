"""Gondor's own paint layers (built on first use: sagekit.paint needs numpy, on Blender's Python;
this module must import anywhere).

    Lawn        the courtyard's grass and the sheet's ivy stay green: green texels of EA's sheet
                painted with the leaf ramp by their luminance, over the stone recolour
    StarBand    silver seven-pointed stars painted in a row along black enamel bands
    SteelJoint  a dark joint on the white stone beside new steel and gold, so bright metal on
                bright limestone reads as metal set in stone, not as more stone

keep_layers(): what the stone recolour must not turn to white stone, shared by the sheet
recolour (MenStyle.sheet_layers) and the recipes' decals. The Recolour reads every unsaturated or
brownish texel as stone, so EA's wood, thatch, hay, dirt, fruit, crates, coals and red cloth came
out white and its blue-grey slate pale.

    Materials   EA's own colour back on coherent coloured (chroma) texels of the warm and red hues (wood,
                thatch, hay, dirt, fruit, flowers, crates, coals, red cloth and flags), except
                where the Recolour already paints the style's gold. Colour only: flat sheets too
    SheetSlate  EA's blue-grey slate painted with the charcoal slate ramp ("tiles") by colour
                alone (coherent, a little saturated, blue): flat sheets, whose stone is greyer
    Props       (prodkit.props_layer) EA's saturated props keep their colours, tuned per sheet
    Slate       (barracks.paintkit) slate by colour above a height and inside a box
    Keep        (barracks.paintkit) EA's colour on its saturated texels of a hue
    KeepFire    (stable.pieces) EA's colour on warm bright texels inside a box (coals, hay)
"""
import functools


@functools.lru_cache(maxsize=None)
def men_layers():
    import numpy as np

    from sagekit.paint.fields import hsv, ramp, smooth
    from sagekit.paint.imageio import to_srgb
    from sagekit.paint.layers import Layer

    def source(cv):
        rgb = getattr(cv, "rgb", None)
        if rgb is not None:
            return rgb
        return cv.memo("men_rgb", lambda: to_srgb(cv.load("atlas")).astype(np.float32))

    class Lawn(Layer):
        def __init__(self, strength=0.9, hue=(62.0, 150.0), sat=(0.16, 0.30)):
            self.strength, self.hue, self.sat = strength, hue, sat

        def apply(self, col, cv, pal):
            H, S, V = hsv(source(cv))
            (h0, h1), (s0, s1) = self.hue, self.sat
            m = smooth(H, h0, h0 + 12) * (1 - smooth(H, h1 - 12, h1)) * smooth(S, s0, s1) * smooth(V, 0.06, 0.16)
            m = (m * self.strength * (1 - getattr(cv, "painted", 0.0)))[..., None]
            return col * (1 - m) + ramp(np.clip(cv.lum * 1.1, 0, 1), pal["leaf"]) * m

    class SteelJoint(Layer):
        """Stone texels within `width` of a new metal face (world space, binned in cells) darken
        toward the joint and sink a little in the normal map."""

        def __init__(self, tags=("trim", "gilt", "iron"), width=0.55, strength=0.7, depth=0.08):
            self.tags, self.width, self.strength, self.depth = tags, width, strength, depth

        def mask(self, cv):
            def compute():
                out = np.zeros(cv.covm.shape, np.float32)
                src = cv.tag_is(*self.tags) & (cv.covm > 0.5)
                cand = (cv.covm > 0.5) & ~src & (cv.w_stone > 0.05)
                if not src.any() or not cand.any():
                    return out
                q = np.floor(cv.pos / (self.width / 2)).astype(np.int64)
                B = 1 << 20

                def key(c):
                    return ((c[..., 0] + B) << 42) | ((c[..., 1] + B) << 21) | (c[..., 2] + B)
                cells, inv = np.unique(key(q[src]), return_inverse=True)
                ps = cv.pos[src]
                cnt = np.bincount(inv, minlength=len(cells)).astype(np.float32)
                mean = np.stack([np.bincount(inv, ps[:, i], len(cells)) for i in range(3)], -1) / cnt[:, None]
                qc, pc = q[cand], cv.pos[cand]
                d = np.full(len(pc), 9.0, np.float32)
                for off in np.stack(np.meshgrid(*[(-1, 0, 1)] * 3, indexing="ij"), -1).reshape(-1, 3):
                    k = key(qc + off)
                    i = np.clip(np.searchsorted(cells, k), 0, len(cells) - 1)
                    d = np.where(cells[i] == k, np.minimum(d, np.linalg.norm(pc - mean[i], axis=1)), d)
                out[cand] = 1 - smooth(d, 0.3 * self.width, self.width)
                return out * cv.w_stone
            return cv.memo(("steeljoint", id(self)), compute)

        def apply(self, col, cv, pal):
            g = (self.strength * self.mask(cv))[..., None]
            return col * (1 - g) + np.array(pal["groove"], np.float32) * g

        def height(self, cv, ds):
            return ds(-self.depth * self.mask(cv))

    class StarBand(Layer):
        """Silver seven-pointed stars in a row along black enamel bands (the towers' gallery fronts):
        world space, one every `pitch` along each vertical face, centred in `zrange`."""

        def __init__(self, tag="enamel", zrange=(77.2, 80.1), pitch=3.2, r=0.95, ramp_name="trim", depth=0.06):
            self.tag, self.zrange, self.pitch, self.r, self.ramp_name, self.depth = tag, zrange, pitch, r, ramp_name, depth

        def mask(self, cv):
            def compute():
                pos, nrm = cv.pos, cv.nrm
                z0, z1 = self.zrange
                on = cv.tag_is(self.tag) & (np.abs(nrm[..., 2]) < 0.3) & (pos[..., 2] > z0) & (pos[..., 2] < z1)
                s = pos[..., 0] * -nrm[..., 1] + pos[..., 1] * nrm[..., 0]
                u = (s / self.pitch - np.floor(s / self.pitch) - 0.5) * self.pitch
                v = pos[..., 2] - (z0 + z1) / 2
                rr = np.hypot(u, v)
                sector = 2 * np.pi / 7
                phi = np.mod(np.arctan2(v, u) - np.pi / 2 + sector / 2, sector) - sector / 2
                R = self.r * (1 - 0.58 * np.abs(phi) / (sector / 2))
                return (on * (1 - smooth(rr - R, -0.06, 0.06))).astype(np.float32)
            return cv.memo(("starband", id(self)), compute)

        def apply(self, col, cv, pal):
            m = self.mask(cv)[..., None]
            L = np.clip(cv.lum * 0.4 + 0.62, 0, 1)
            return col * (1 - m) + ramp(L, pal[self.ramp_name]) * m

        def height(self, cv, ds):
            return ds(self.depth * self.mask(cv))

    return Lawn, SteelJoint, StarBand


@functools.lru_cache(maxsize=None)
def keep_layers():
    import numpy as np

    from sagekit.paint.fields import box_blur, hsv, ramp, smooth
    from sagekit.paint.imageio import to_srgb
    from sagekit.paint.layers import Layer

    def source(cv):
        rgb = getattr(cv, "rgb", None)
        if rgb is not None:
            return rgb
        return cv.memo("men_rgb", lambda: to_srgb(cv.load("atlas")).astype(np.float32))

    def new_faces(cv):
        return getattr(cv, "painted", 0.0)

    def memo(cv, key, fn):                              # a flat sheet's canvas keeps no memo
        return cv.memo(key, fn) if hasattr(cv, "memo") else fn()

    def coherent(m, radius):
        r = max(2, int(round(m.shape[1] / radius)))
        return box_blur(m.astype(np.float32), r)

    def in_hue(H, h0, h1, soft=6.0):
        if h0 > h1:                                     # a window across red (e.g. 330..70)
            return np.maximum(smooth(H, h0, h0 + soft), 1 - smooth(H, h1 - soft, h1))
        return smooth(H, h0, h0 + soft) * (1 - smooth(H, h1 - soft, h1))

    class Materials(Layer):
        def __init__(self, hue=(330.0, 72.0), chroma=(0.065, 0.1), radius=512, strength=1.0):
            self.hue, self.chroma, self.radius, self.strength = hue, chroma, radius, strength

        def mask(self, cv):
            def compute():
                H, S, V = hsv(source(cv))           # chroma (S x V), not saturation: EA's dark stone is
                m = coherent(S * V * in_hue(H, *self.hue), self.radius)     # warm-tinted but grey
                m = smooth(m, *self.chroma) * (1 - cv.gold)
                return (m * cv.covm * self.strength * (1 - new_faces(cv))).astype(np.float32)
            return memo(cv, ("men_materials", id(self)), compute)

        def apply(self, col, cv, pal):
            m = self.mask(cv)[..., None]
            return col * (1 - m) + source(cv) * m

    class SheetSlate(Layer):
        def __init__(self, hue=(195.0, 250.0), sat=(0.09, 0.15), val=(0.28, 0.38), radius=512, gain=1.05, lift=0.02):
            self.hue, self.sat, self.val, self.radius, self.gain, self.lift = hue, sat, val, radius, gain, lift

        def mask(self, cv):
            def compute():                          # dark stone reads blue and saturated: gate on value
                H, S, V = hsv(source(cv))
                m = smooth(coherent(S * in_hue(H, *self.hue), self.radius), *self.sat)
                m = m * smooth(coherent(V, self.radius), *self.val)
                return (m * cv.covm * (1 - new_faces(cv))).astype(np.float32)
            return memo(cv, ("men_sheetslate", id(self)), compute)

        def apply(self, col, cv, pal):
            m = self.mask(cv)[..., None]
            return col * (1 - m) + ramp(np.clip(cv.lum * self.gain + self.lift, 0, 1), pal["tiles"]) * m

    class Props(Layer):
        def __init__(self, sat=(0.3, 0.45), gate=(0.35, 0.6), hue=None, strength=0.95, rects=()):
            self.sat, self.gate, self.hue, self.strength, self.rects = sat, gate, hue, strength, rects

        def mask(self, cv):
            def compute():
                H, S, V = hsv(source(cv))
                m = smooth(S, *self.sat) * smooth(V, 0.04, 0.1)
                if self.hue:
                    h0, h1 = self.hue
                    m = m * smooth(H, h0, h0 + 6) * (1 - smooth(H, h1 - 6, h1))
                r = max(2, int(round(m.shape[1] / 256)))
                m = smooth(box_blur(m.astype(np.float32), r), *self.gate)
                if self.rects:
                    auv = np.mod(cv.load("auv"), 1.0)
                    old = cv.tag_is("old")
                    for u0, v0, u1, v1 in self.rects:
                        inside = (auv[..., 0] >= u0) & (auv[..., 0] <= u1) & (auv[..., 1] >= v0) & (auv[..., 1] <= v1)
                        m = np.maximum(m, (inside & old).astype(np.float32))
                return (m * self.strength * (1 - new_faces(cv))).astype(np.float32)
            return cv.memo(("props", id(self)), compute)

        def apply(self, col, cv, pal):
            m = self.mask(cv)[..., None]
            return col * (1 - m) + source(cv) * m

    class Slate(Layer):
        def __init__(self, z0, box=None, hue=(150.0, 245.0), sat=(0.04, 0.12), gain=1.05, lift=0.02):
            self.z0, self.box, self.hue, self.sat, self.gain, self.lift = z0, box, hue, sat, gain, lift

        def mask(self, cv):
            def compute():
                H, S, _ = hsv(source(cv))
                (h0, h1), (s0, s1) = self.hue, self.sat
                m = smooth(H, h0, h0 + 15) * (1 - smooth(H, h1 - 15, h1)) * smooth(S, s0, s1)
                p = cv.pos
                m = m * smooth(p[..., 2], self.z0 - 0.3, self.z0 + 0.3)
                if self.box:
                    x0, x1, y0, y1 = self.box
                    m = m * ((p[..., 0] > x0) & (p[..., 0] < x1) & (p[..., 1] > y0) & (p[..., 1] < y1))
                return (m * cv.covm * (1 - cv.painted)).astype(np.float32)
            return cv.memo(("slate", self.z0, self.box), compute)

        def apply(self, col, cv, pal):
            m = self.mask(cv)[..., None]
            return col * (1 - m) + ramp(np.clip(cv.lum * self.gain + self.lift, 0, 1), pal["tiles"]) * m

    class Keep(Layer):
        def __init__(self, hue=(335.0, 25.0), sat=(0.28, 0.42), strength=1.0):
            self.hue, self.sat, self.strength = hue, sat, strength

        def apply(self, col, cv, pal):
            rgb = source(cv)
            H, S, _ = hsv(rgb)
            h0, h1 = self.hue
            inside = (H >= h0) | (H <= h1) if h0 > h1 else (H >= h0) & (H <= h1)
            m = inside * smooth(S, *self.sat) * cv.covm * (1 - cv.painted) * self.strength
            m = m.astype(np.float32)[..., None]
            return col * (1 - m) + rgb * m

    class KeepFire(Layer):
        def __init__(self, box, hue=(0.0, 52.0), sat=(0.38, 0.55), val=(0.30, 0.45)):
            self.box, self.hue, self.sat, self.val = box, hue, sat, val

        def mask(self, cv):
            def compute():
                src = to_srgb(cv.load("atlas")).astype(np.float32)
                H, S, V = hsv(src)
                lo, hi = self.box
                p = cv.pos
                inside = np.all((p >= np.array(lo, np.float32)) & (p <= np.array(hi, np.float32)), axis=-1)
                (h0, h1), (s0, s1), (v0, v1) = self.hue, self.sat, self.val
                m = (H >= h0) * (1 - smooth(H, h1 - 6, h1)) * smooth(S, s0, s1) * smooth(V, v0, v1)
                return (m * inside * (1 - cv.painted)).astype(np.float32), src
            return cv.memo(("keepfire", id(self)), compute)

        def apply(self, col, cv, pal):
            m, src = self.mask(cv)
            m = m[..., None]
            return col * (1 - m) + src * m

    return dict(Materials=Materials, SheetSlate=SheetSlate, Props=Props, Slate=Slate, Keep=Keep, KeepFire=KeepFire)
