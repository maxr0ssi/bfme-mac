"""Paint layers. A Style stacks them bottom to top; each takes the colour so far and returns the
new colour. Parameters are constructor arguments so a faction tunes a layer without subclassing.

    col = layer.apply(col, canvas, palette)          (h, w, 3) sRGB 0..1
    h   = layer.height(canvas, ds)                   optional: relief for the normal map (world
                                                     units, at normal-map size; ds() downsamples)
"""
import numpy as np

from .fields import hash01, hsv, ramp, seg_dist, smooth
from .imageio import to_srgb


class Layer:
    def apply(self, col, cv, pal):
        return col

    def height(self, cv, ds):
        return None


class Recolour(Layer):
    """The painted sheet recoloured per material through the palette's luminance ramps: every
    painted motif (reliefs, friezes, grilles) survives in the new colours."""
    MATERIALS = ("bronze", "gold", "wood", "ground", "glyph", "iron", "rock", "tiles")
    RAMP = {"glyph": "inlay"}

    def __init__(self, stone_pivot=0.45, stone_gain=1.12, stone_mid=0.47):
        self.pivot, self.gain, self.mid = stone_pivot, stone_gain, stone_mid

    def apply(self, col, cv, pal):
        L = np.clip(cv.lum, 0, 1)
        col = cv.w_stone[..., None] * ramp(np.clip((L - self.pivot) * self.gain + self.mid, 0, 1), pal["stone"])
        tot = cv.w_stone
        for m in self.MATERIALS:
            col += cv.masks[m][..., None] * ramp(L, pal[self.RAMP.get(m, m)])
        for m in self.MATERIALS:
            tot = tot + cv.masks[m]
        return col / np.maximum(tot, 1e-4)[..., None]


class TagRamp(Layer):
    """New faces of one atlas region painted with one ramp (e.g. trim faces become bronze bands)."""

    def __init__(self, tag, ramp_name, gain=1.05, lift=0.08):
        self.tag, self.ramp_name, self.gain, self.lift = tag, ramp_name, gain, lift

    def apply(self, col, cv, pal):
        f = cv.tag_is(self.tag).astype(np.float32)[..., None]
        L = np.clip(cv.lum, 0, 1)
        return col * (1 - f) + ramp(np.clip(L * self.gain + self.lift, 0, 1), pal[self.ramp_name]) * f


class MetalRims(Layer):
    """Burnished rims around every bronze plate. min_plate > 0 skips thin bronze (bars, rungs), which
    is all rim and would turn wholly gold."""

    def __init__(self, ramp_name="gold", lift=0.25, min_plate=0.0):
        self.ramp_name, self.lift, self.min_plate = ramp_name, lift, min_plate

    def apply(self, col, cv, pal):
        rim = smooth(cv.bronze, 0.4, 0.7) * (1 - smooth(cv.bronze_blur, 0.80, 0.95))
        if self.min_plate:
            rim = rim * smooth(cv.bronze_blur, self.min_plate, self.min_plate + 0.15)
        rim = rim[..., None]
        return col * (1 - rim) + ramp(np.clip(np.clip(cv.lum, 0, 1) + self.lift, 0, 1), pal[self.ramp_name]) * rim


class BuildingDecals(Layer):
    """Where the building's own decals (Building.decals()) go in the stack."""

    def __init__(self, building):
        self.decals = building.decals()

    def apply(self, col, cv, pal):
        for d in self.decals:
            col = d.apply(col, cv, pal)
        return col

    def height(self, cv, ds):
        hs = [h for h in (d.height(cv, ds) for d in self.decals) if h is not None]
        return sum(hs) if hs else None


class WoodGrain(Layer):
    def __init__(self, depth=0.30):
        self.depth = depth

    def apply(self, col, cv, pal):
        return col * (1 - cv.wood[..., None] * (self.depth * cv.grain[..., None]))


class Ashlar(Layer):
    """Dressed-stone blocks in world space: courses on walls, slabs on floors. Block-to-block tone
    and tint, broad blotches, fine grain, darker mortar, lit block tops; mortar grooves in the
    normal map. `new_stone`: atlas regions whose new faces always count as plain stone."""

    def __init__(self, course=5.2, length=(8.0, 5.0), slab=(6.0, 9.0), new_stone=("stoneA", "stoneB", "top"),
                 tint_share=(0.33, 0.72), tint_amount=0.9, tone=0.20, blotch=0.18, fine=0.08, lit=0.10,
                 mortar_dark=0.48, mortar_tint=0.18, groove=0.22):
        self.course, self.length, self.slab, self.new_stone = course, length, slab, new_stone
        self.tint_share, self.tint_amount, self.tone, self.blotch_k, self.fine_k = tint_share, tint_amount, tone, blotch, fine
        self.lit_k, self.mortar_dark, self.mortar_tint, self.groove = lit, mortar_dark, mortar_tint, groove

    def blocks(self, cv):
        """(joint distance, rand1, rand2, height to the course top) per texel."""
        def compute():
            p, n = cv.flat(cv.pos), cv.flat(cv.nrm)
            vert = np.abs(n[:, 2]) < 0.7
            t = np.stack([-n[:, 1], n[:, 0], np.zeros(len(n), np.float32)], -1)
            t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-6)
            s = (p * t).sum(1)
            ang = np.round(np.degrees(np.arctan2(t[:, 1], t[:, 0])) / 15).astype(np.int64)
            H = self.course
            ci = np.floor(p[:, 2] / H)
            cf = p[:, 2] / H - ci
            L = self.length[0] + self.length[1] * hash01(ci, 11)
            o = hash01(ci, 12) * L
            bq = (s + o) / L
            bi = np.floor(bq)
            bf = bq - bi
            dv = np.minimum(np.minimum(cf, 1 - cf) * H, np.minimum(bf, 1 - bf) * L)
            top_v = (1 - cf) * H
            rv1, rv2 = hash01(ci, bi, ang, 1), hash01(ci, bi, ang, 2)
            Hh, Lh = self.slab
            ri = np.floor(p[:, 1] / Hh)
            rf = p[:, 1] / Hh - ri
            oh = hash01(ri, 21) * Lh
            hq = (p[:, 0] + oh) / Lh
            hi = np.floor(hq)
            hf = hq - hi
            dh = np.minimum(np.minimum(rf, 1 - rf) * Hh, np.minimum(hf, 1 - hf) * Lh)
            rh1, rh2 = hash01(ri, hi, np.round(p[:, 2]), 3), hash01(ri, hi, np.round(p[:, 2]), 4)
            d = np.where(vert, dv, dh)
            r1, r2 = np.where(vert, rv1, rh1), np.where(vert, rv2, rh2)
            top = np.where(vert, top_v, 99.0)
            return [x.reshape(cv.R, cv.R) for x in (d.astype(np.float32), r1, r2, top.astype(np.float32))]
        return cv.memo(("ashlar", id(self)), compute)

    def stone_mask(self, cv):
        def compute():
            m = cv.masks
            s = np.maximum(smooth(m["plain"], 0.15, 0.5), cv.tag_is(*self.new_stone).astype(np.float32))
            return s * (1 - np.clip(m["bronze"] + m["gold"] + m["wood"] + m["ground"] + m["glyph"] + m["iron"]
                                    + m["rock"] + m["tiles"], 0, 1)) * (1 - cv.painted)
        return cv.memo(("stone_mask", id(self)), compute)

    def mortar(self, cv):
        return cv.memo(("mortar", id(self)), lambda: (1 - smooth(self.blocks(cv)[0], 0.05, 0.15)) * self.stone_mask(cv))

    def apply(self, col, cv, pal):
        d, r1, r2, top = self.blocks(cv)
        smask, mortar = self.stone_mask(cv), self.mortar(cv)
        k = (cv.w_stone * (1 - cv.rock))[..., None]
        lo, hi = self.tint_share
        tint = np.where(r2[..., None] < lo, np.array(pal["stone_alt"], np.float32),
                        np.where(r2[..., None] > hi, np.array(pal["stone_alt2"], np.float32), 1.0))
        col = col * (1 + k * (tint - 1) * self.tint_amount)
        col = col * (1 + k * ((r1[..., None] - 0.5) * self.tone + (cv.blotch[..., None] - 0.5) * self.blotch_k
                              + (cv.fine[..., None] - 0.5) * self.fine_k))
        lit = smooth(-top, -0.55, -0.22) * (1 - mortar) * smask
        col = col * (1 + self.lit_k * lit[..., None])
        return col * (1 - self.mortar_dark * mortar[..., None]) + np.array(pal["occl"], np.float32) * self.mortar_tint * mortar[..., None]

    def height(self, cv, ds):
        d, sm = ds(self.blocks(cv)[0]), ds(self.stone_mask(cv))
        return -self.groove * (1 - smooth(d, 0.05, 0.42)) * sm


class Occlusion(Layer):
    """Baked ambient occlusion, tinted with the palette's occlusion colour."""

    def apply(self, col, cv, pal):
        ao = np.power(cv.ao_s, 0.7) * (0.66 + 0.34 * cv.ao_l)
        occ = np.array(pal["occl"], np.float32) * 0.6 + 0.4
        return col * (occ + (1 - occ) * ao[..., None]) * (0.88 + 0.12 * ao[..., None])


class EdgeWear(Layer):
    """Highlights on convex edges, stronger on metal (burnished)."""

    def __init__(self, base=0.26, metal=0.30):
        self.base, self.metal = base, metal

    def apply(self, col, cv, pal):
        ek = (self.base + self.metal * cv.metal) * cv.convex
        return col + (np.array(pal["edge"], np.float32) * np.maximum(col.max(-1, keepdims=True), 0.35) * 1.25 - col) * ek[..., None]


class Streaks(Layer):
    """Grime streaks running down from every ledge."""

    def apply(self, col, cv, pal):
        s = cv.streak_noise
        gr = cv.ledge * smooth(s, 0.42, 0.75) * 0.55 + cv.vertical * smooth(s, 0.62, 0.85) * 0.12
        gr = gr * (1 - cv.glyph) * (1 - 0.6 * cv.metal)
        return col * (1 - gr[..., None] * 0.42) + np.array(pal["grime"], np.float32) * gr[..., None] * 0.18


class GroundDirt(Layer):
    def apply(self, col, cv, pal):
        dirt = smooth(-cv.z, -7.0, -0.5) * (0.55 + 0.45 * cv.blotch) * 0.55 * (1 - cv.tiles * 0.5)
        return col + (np.array(pal["dirt"], np.float32) - col) * dirt[..., None] * 0.6


class Moss(Layer):
    def apply(self, col, cv, pal):
        up = np.clip(cv.nrm[..., 2], 0, 1)
        moss = smooth(cv.blotch, 0.58, 0.78) * smooth(-cv.z, -20, -2) * (0.4 + 0.6 * up) * (1 - cv.ao_s * 0.5) * cv.w_stone * 0.5
        moss += smooth(cv.blotch, 0.66, 0.85) * (1 - cv.ao_s) * up * 0.35 * cv.w_stone
        tint = np.array(pal["moss"], np.float32) * (0.7 + 0.5 * cv.fine[..., None])
        return col + (tint - col) * np.clip(moss, 0, 0.6)[..., None]


class Inlay(Layer):
    """Runes and carved glyphs as inlay (and a faint glow where the palette has one)."""

    def __init__(self, strength=0.85, gain=1.1, glow=0.35):
        self.strength, self.gain, self.glow = strength, gain, glow

    def apply(self, col, cv, pal):
        g = np.clip(cv.glyph, 0, 1)[..., None]
        inlay = ramp(np.clip(np.clip(cv.lum, 0, 1) * self.gain, 0, 1), pal["inlay"])
        col = col * (1 - g * self.strength) + inlay * g * self.strength
        glow = pal.accents.get("glow")
        if glow is not None:
            from .fields import box_blur
            halo = box_blur(box_blur(cv.glyph, 6), 6) * cv.covm
            band = np.clip(cv.ground + cv.glyph, 0, 1)
            col = col + np.array(glow, np.float32) * (self.glow * halo * band)[..., None]
        return col


class StrokeSigil(Layer):
    """An emblem drawn as line strokes in world space on vertical faces near given anchors, gilded
    and carved: strokes [((s0, z0), (s1, z1))] with s along the face from the anchor axis.
    `on` limits it to a material (e.g. the bronze of a shield)."""

    def __init__(self, anchors, strokes, zrange, reach=17.0, width=(0.16, 0.30), on="bronze", on_range=(0.3, 0.6),
                 ramp_name="gold", depth=0.14):
        self.anchors, self.strokes, self.zrange, self.reach = anchors, strokes, zrange, reach
        self.width, self.on, self.on_range, self.ramp_name, self.depth = width, on, on_range, ramp_name, depth

    def mask(self, cv):
        def compute():
            pos, nrm = cv.pos, cv.nrm
            out = np.zeros(pos.shape[:2], np.float32)
            side = (np.abs(nrm[..., 2]) < 0.3) & (pos[..., 2] > self.zrange[0]) & (pos[..., 2] < self.zrange[1])
            for cx, cy in self.anchors:
                near = side & (np.abs(pos[..., 0] - cx) < self.reach) & (np.abs(pos[..., 1] - cy) < self.reach)
                if not near.any():
                    continue
                tx, ty = -nrm[..., 1], nrm[..., 0]
                s = (pos[..., 0] - cx) * tx + (pos[..., 1] - cy) * ty
                d = np.full(pos.shape[:2], 9.0, np.float32)
                for a, b in self.strokes:
                    d = np.minimum(d, seg_dist(s, pos[..., 2], a, b))
                out = np.maximum(out, near * (1 - smooth(d, *self.width)))
            return out * smooth(cv.masks[self.on], *self.on_range)
        return cv.memo(("sigil", id(self)), compute)

    def apply(self, col, cv, pal):
        sg = self.mask(cv)[..., None]
        L = np.clip(cv.lum, 0, 1)
        return col * (1 - sg) + ramp(np.clip(L * 0.6 + 0.45, 0, 1), pal[self.ramp_name]) * sg

    def height(self, cv, ds):
        return ds(-self.depth * self.mask(cv))


def sheet_rgb(cv):
    """EA's own colour under the canvas: a flat sheet's pixels (SheetCanvas.rgb), or on a building
    the original sheet as baked through the atlas mapping."""
    rgb = getattr(cv, "rgb", None)
    if rgb is not None:
        return rgb
    return cv.memo("sheet_rgb", lambda: to_srgb(cv.load("atlas")).astype(np.float32))


class Foliage(Layer):
    """Green texels of the original sheet (ivy, grass, moss) painted with the leaf ramp by their own
    luminance, over whatever the Recolour made of them; new faces keep their own paint. Works on
    building canvases and on flat sheets."""

    def __init__(self, strength=0.9, hue=(62.0, 150.0), sat=(0.16, 0.30)):
        self.strength, self.hue, self.sat = strength, hue, sat

    def apply(self, col, cv, pal):
        H, S, V = hsv(sheet_rgb(cv))
        (h0, h1), (s0, s1) = self.hue, self.sat
        m = smooth(H, h0, h0 + 12) * (1 - smooth(H, h1 - 12, h1)) * smooth(S, s0, s1) * smooth(V, 0.06, 0.16)
        m = (m * self.strength * (1 - getattr(cv, "painted", 0.0)))[..., None]
        return col * (1 - m) + ramp(np.clip(cv.lum * 1.1, 0, 1), pal["leaf"]) * m


class Groove(Layer):
    """A dark joint on the stone beside new metal (the `tags`' faces), so bright metal on pale stone
    reads as metal set in stone, not as more stone; it sinks a little in the normal map. World
    space, as the faces lie on the mesh (their UV islands are apart): the metal texels are binned
    in cells of half the width, and every stone texel takes its distance to the nearest cell's mean
    point among the 27 round its own; dark at the joint (the palette's "groove"), gone at `width`."""

    def __init__(self, tags=("trim", "gilt"), width=0.6, strength=0.75, depth=0.08):
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
            n = np.bincount(inv, minlength=len(cells)).astype(np.float32)
            mean = np.stack([np.bincount(inv, ps[:, i], len(cells)) for i in range(3)], -1) / n[:, None]
            qc, pc = q[cand], cv.pos[cand]
            d = np.full(len(pc), 9.0, np.float32)
            for off in np.stack(np.meshgrid(*[(-1, 0, 1)] * 3, indexing="ij"), -1).reshape(-1, 3):
                k = key(qc + off)
                i = np.clip(np.searchsorted(cells, k), 0, len(cells) - 1)
                d = np.where(cells[i] == k, np.minimum(d, np.linalg.norm(pc - mean[i], axis=1)), d)
            out[cand] = 1 - smooth(d, 0.3 * self.width, self.width)
            return out * cv.w_stone
        return cv.memo(("groove", id(self)), compute)

    def apply(self, col, cv, pal):
        g = (self.strength * self.mask(cv))[..., None]
        return col * (1 - g) + np.array(pal["groove"], np.float32) * g

    def height(self, cv, ds):
        return ds(-self.depth * self.mask(cv))
