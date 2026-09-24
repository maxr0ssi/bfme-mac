"""Canvas: the baked G-buffers of one building plus every field derived from them, computed once
on first use and shared by all layers (cached properties)."""
import os
from functools import cached_property

import numpy as np

from . import imageio, masks
from .fields import box_blur, fbm, hash01, smooth

TAG_SCALE = 100.0


class Canvas:
    def __init__(self, bake_dir, atlas, target_obj=None):
        self.dir = bake_dir
        self.atlas = atlas
        self.target_obj = target_obj            # bpy object, for ray casts (ledges)
        self.tags = ["old"] + list(atlas.regions)

        self._memo = {}

    def load(self, name):
        return np.load(os.path.join(self.dir, name + ".npy"))

    def memo(self, key, fn):
        """A field computed once per canvas by whichever layer asks first (e.g. the ashlar joints
        the colour and the normal map both use)."""
        if key not in self._memo:
            self._memo[key] = fn()
        return self._memo[key]

    # ------------------------------------------------------------------ raw buffers
    @cached_property
    def cov(self):
        return self.load("cov")[..., 0]

    @property
    def R(self):
        return self.cov.shape[0]

    @cached_property
    def covm(self):
        return (self.cov > 0.5).astype(np.float32)

    @cached_property
    def pos(self):
        return self.load("pos")

    @cached_property
    def nrm(self):
        n = self.load("nrm")
        n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-6)
        return n

    @cached_property
    def tagi(self):
        return np.rint(self.load("tag")[..., 0] * TAG_SCALE).astype(np.int64)

    def tag_is(self, *names):
        return np.isin(self.tagi, [self.tags.index(n) for n in names])

    @cached_property
    def masks(self):
        m1, m2, m3 = self.load("mask1"), self.load("mask2"), self.load("mask3")
        ms = [m1[..., 0], m1[..., 1], m1[..., 2], m2[..., 0], m2[..., 1], m2[..., 2], m3[..., 0], m3[..., 1], m3[..., 2]]
        return dict(zip(masks.NAMES, [np.clip(m, 0, 1) for m in ms]))

    def __getattr__(self, name):                # canvas.bronze, canvas.gold, ... (the material masks)
        if name in masks.NAMES:
            return self.masks[name]
        raise AttributeError(name)

    @cached_property
    def lum(self):
        atl = imageio.to_srgb(self.load("atlas")).astype(np.float32)
        return atl @ np.array([0.3, 0.59, 0.11], np.float32)

    @cached_property
    def ao_s(self):
        return np.clip(self.load("ao_s")[..., 0], 0, 1)

    @cached_property
    def ao_l(self):
        return np.clip(self.load("ao_l")[..., 0], 0, 1)

    @cached_property
    def bevel(self):
        return np.clip(self.load("bevel")[..., 0], 0, 1)

    # ------------------------------------------------------------------ flat views
    def flat(self, a):
        return a.reshape(self.R * self.R, -1) if a.ndim == 3 else a.reshape(self.R * self.R)

    @cached_property
    def z(self):
        return self.pos[..., 2]

    @cached_property
    def vertical(self):
        return (np.abs(self.nrm[..., 2]) < 0.6).astype(np.float32)

    # ------------------------------------------------------------------ material weights
    @cached_property
    def w_stone(self):
        """Weight of 'anything not otherwise a material' (the stone ramp)."""
        m = self.masks
        return np.clip(1 - (m["bronze"] + m["gold"] + m["wood"] + m["ground"] + m["glyph"] + m["iron"]
                            + m["rock"] + m["tiles"]), 0, 1)

    @cached_property
    def metal(self):
        return np.clip(self.bronze + self.gold, 0, 1)

    # ------------------------------------------------------------------ noise (world space)
    @cached_property
    def streak_noise(self):
        P = self.flat(self.pos)
        return fbm(np.stack([P[:, 0] * 0.9, P[:, 1] * 0.9, P[:, 2] * 0.035], -1), 4, 5).reshape(self.R, self.R)

    @cached_property
    def blotch(self):
        return fbm(self.flat(self.pos) * 0.09, 4, 9).reshape(self.R, self.R)

    @cached_property
    def fine(self):
        return fbm(self.flat(self.pos) * 0.6, 3, 17).reshape(self.R, self.R)

    @cached_property
    def grain(self):
        auv = self.load("auv")
        g = fbm(np.stack([auv[..., 0].ravel() * 900, auv[..., 1].ravel() * 60, np.zeros(self.R * self.R, np.float32)], -1),
                3, 31).reshape(self.R, self.R)
        return smooth(g, 0.35, 0.75)

    @cached_property
    def bronze_blur(self):
        return box_blur(box_blur(self.bronze, 5), 5)

    @cached_property
    def convex(self):
        return smooth(self.bevel, 0.02, 0.12) * smooth(self.ao_s, 0.72, 0.92)

    # ------------------------------------------------------------------ geometry-derived
    @cached_property
    def ledge_distance(self, step=4):
        """Per texel on vertical faces: distance straight up to the ledge above (ray cast)."""
        from mathutils import Vector
        from mathutils.bvhtree import BVHTree
        me = self.target_obj.data
        bvh = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
        h, w = self.covm.shape
        P = self.pos[::step, ::step].reshape(-1, 3)
        N = self.nrm[::step, ::step].reshape(-1, 3)
        C = self.covm[::step, ::step].reshape(-1)
        out = np.full(len(P), 1e3, np.float32)
        up = Vector((0, 0, 1))
        for i in np.nonzero((C > 0.5) & (np.abs(N[:, 2]) < 0.6))[0]:
            p, n = P[i], N[i]
            hit = bvh.ray_cast(Vector((p[0] + n[0] * 0.08, p[1] + n[1] * 0.08, p[2] + 0.02)), up, 60.0)
            if hit[0] is not None:
                out[i] = hit[3]
        out = out.reshape(h // step, w // step)
        return np.repeat(np.repeat(out, step, 0), step, 1)

    @cached_property
    def ledge(self):
        return np.exp(-np.minimum(self.ledge_distance, 1e3) / 7.0) * self.vertical

    def hash01(self, *ks):
        return hash01(*ks)
