"""W3D skeletons, animations and poses (pure Python).

The lifecycle models (construction, really damaged, rubble) move their pieces on bones: rigid
meshes hang on the bone the HLOD names, skinned ones name a bone per vertex (VERTEX_INFLUENCES)
and store each vertex in that bone's rest space. A pose is WW3D's HTreeClass::Anim_Update:

    world[p] = world[parent] @ base[p] @ T(animated translation) @ R(animated rotation)

with pivot 0 the object's own transform (identity here). Plain animations (0x200: per-frame
channels, bit channels for visibility) and time-coded compressed ones (0x280, flavor 0) are read;
adaptive-delta ones (flavor 1) raise, so a caller never poses from a guess.

Matrices are 3x4 row-major lists [r00 r01 r02 tx r10 ... tz]; quaternions (x, y, z, w) as stored.

sagekit/formats/w3dframes.py is the rest-pose half: where each mesh of a model stands (its bone's
model-space frame as a (rotation, translation) pair) and moving a mesh chunk between frames, for
the steps that place a body without animating it (derive, same_body, own copies, night lights).
The two read the same pivots and HLOD; they stay two modules: that half's (R, T) frames are what
the host-side placement code composes, this one's 3x4 matrices what the animation channels feed,
and one module would mean rewriting the other steps' callers for nothing gained.
"""
import math
import struct

from .w3d import (ANIMATION, ANIMATION_HEADER, COMPRESSED_ANIMATION, COMPRESSED_ANIMATION_HEADER, HIERARCHY,
                  HIERARCHY_HEADER, HLOD, HLOD_HEADER, HLOD_SUB_OBJECT, PIVOTS, VERTEX_INFLUENCES, _cstr, chunks)

ANIMATION_CHANNEL, BIT_CHANNEL = 0x202, 0x203
COMPRESSED_CHANNEL, COMPRESSED_BIT_CHANNEL = 0x282, 0x283
BINARY_MOVEMENT = 0x80000000
IDENTITY = [1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0, 0]


# ------------------------------------------------------------------------------------ matrices
def compose(t, q):
    x, y, z, w = q
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    x, y, z, w = x / n, y / n, z / n, w / n
    return [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), t[0],
            2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), t[1],
            2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), t[2]]


def mul(a, b):
    out = []
    for r in range(3):
        for c in range(4):
            v = a[4 * r] * b[c] + a[4 * r + 1] * b[4 + c] + a[4 * r + 2] * b[8 + c]
            out.append(v + (a[4 * r + 3] if c == 3 else 0.0))
    return out


def invert(m):
    """Inverse of a rigid transform (rotation + translation)."""
    r = [m[0], m[4], m[8], m[1], m[5], m[9], m[2], m[6], m[10]]
    t = (m[3], m[7], m[11])
    return [r[0], r[1], r[2], -(r[0] * t[0] + r[1] * t[1] + r[2] * t[2]),
            r[3], r[4], r[5], -(r[3] * t[0] + r[4] * t[1] + r[5] * t[2]),
            r[6], r[7], r[8], -(r[6] * t[0] + r[7] * t[1] + r[8] * t[2])]


def point(m, p):
    return tuple(m[4 * r] * p[0] + m[4 * r + 1] * p[1] + m[4 * r + 2] * p[2] + m[4 * r + 3] for r in range(3))


def direction(m, v):
    return tuple(m[4 * r] * v[0] + m[4 * r + 1] * v[1] + m[4 * r + 2] * v[2] for r in range(3))


def slerp(a, b, t):
    d = sum(x * y for x, y in zip(a, b))
    if d < 0:
        b, d = [-x for x in b], -d
    if d > 0.9995:
        return [x + (y - x) * t for x, y in zip(a, b)]
    th = math.acos(min(d, 1.0))
    s0, s1 = math.sin((1 - t) * th) / math.sin(th), math.sin(t * th) / math.sin(th)
    return [s0 * x + s1 * y for x, y in zip(a, b)]


# ------------------------------------------------------------------------------------ reading
def _first(d, tag):
    return [(o, s) for t, o, s, _ in chunks(d, 0, len(d)) if t == tag]


class Skeleton:
    """A HIERARCHY chunk: pivots [(name, parent, translation, rotation)] and their rest matrices.
    A bare mesh file (no hierarchy: DBFStatus) has its root alone, where every mesh then hangs."""

    def __init__(self, data):
        found = _first(data, HIERARCHY)
        self.name, self.pivots = None, [("ROOTTRANSFORM", -1, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0))]
        if found:
            self.pivots = []
        o, s = found[0] if found else (0, -8)
        for t, o2, s2, _ in chunks(data, o + 8, o + 8 + s):
            if t == HIERARCHY_HEADER:
                self.name = _cstr(data[o2 + 12:o2 + 28])
            elif t == PIVOTS:
                for i in range(s2 // 60):
                    p = o2 + 8 + 60 * i
                    name = _cstr(data[p:p + 16])
                    parent = struct.unpack_from("<i", data, p + 16)[0]
                    tr = struct.unpack_from("<3f", data, p + 20)
                    q = struct.unpack_from("<4f", data, p + 44)
                    self.pivots.append((name, parent, tr, q))
        self.names = [p[0].upper() for p in self.pivots]
        self.rest = self.pose(None, 0)[0]

    def index(self, name):
        return self.names.index(name.upper())

    def pose(self, anim, frame):
        """([world matrix per pivot], [visible per pivot]) at `frame` of `anim` (None: rest)."""
        world, vis = [], []
        for i, (_, parent, tr, q) in enumerate(self.pivots):
            if i == 0 or parent < 0:
                world.append(list(IDENTITY))
                vis.append(anim.visible(i, frame) if anim else True)
                continue
            m = mul(world[parent], compose(tr, q))
            if anim:
                m = mul(m, compose(anim.translation(i, frame), anim.rotation(i, frame)))
            world.append(m)
            vis.append(vis[parent] and (anim.visible(i, frame) if anim else True))
        return world, vis


class Animation:
    """One animation: per pivot, translation x/y/z and rotation as keys [(frame, value, step)]
    and visibility as keys [(frame, bool)]."""

    def __init__(self, data):
        self.keys, self.vis = {}, {}
        plain, comp = _first(data, ANIMATION), _first(data, COMPRESSED_ANIMATION)
        if not plain and not comp:
            raise ValueError("no animation in this file")
        o, s = (plain or comp)[0]
        for t, o2, s2, _ in chunks(data, o + 8, o + 8 + s):
            p = o2 + 8
            if t in (ANIMATION_HEADER, COMPRESSED_ANIMATION_HEADER):
                self.name, self.hierarchy = _cstr(data[p + 4:p + 20]), _cstr(data[p + 20:p + 36])
                self.frames = struct.unpack_from("<I", data, p + 36)[0]
                if t == COMPRESSED_ANIMATION_HEADER and struct.unpack_from("<H", data, p + 42)[0] != 0:
                    raise NotImplementedError("%s: adaptive-delta animation" % self.name)
            elif t == ANIMATION_CHANNEL:
                first, last, vlen, kind, pivot = struct.unpack_from("<5H", data, p)
                vals = [struct.unpack_from("<%df" % vlen, data, p + 12 + 4 * vlen * i) for i in range(last - first + 1)]
                self._add(pivot, kind, [(first + i, v, False) for i, v in enumerate(vals)])
            elif t == BIT_CHANNEL:
                first, last, kind, pivot = struct.unpack_from("<4H", data, p)
                default = data[p + 8] != 0
                bits = [(data[p + 9 + i // 8] >> (i % 8)) & 1 == 1 for i in range(last - first + 1)]
                if kind == 0:
                    self.vis[pivot] = (default, [(first + i, b) for i, b in enumerate(bits)])
            elif t == COMPRESSED_CHANNEL:
                n, pivot, vlen, kind = struct.unpack_from("<IHBB", data, p)
                keys, q = [], p + 8
                for _ in range(n):
                    code = struct.unpack_from("<I", data, q)[0]
                    keys.append((code & ~BINARY_MOVEMENT, struct.unpack_from("<%df" % vlen, data, q + 4),
                                 bool(code & BINARY_MOVEMENT)))
                    q += 4 + 4 * vlen
                self._add(pivot, kind, keys)
            elif t == COMPRESSED_BIT_CHANNEL:
                n, pivot, kind, default = struct.unpack_from("<IhBB", data, p)
                keys = []
                for i in range(n):
                    code = struct.unpack_from("<I", data, p + 8 + 4 * i)[0]
                    keys.append((code & ~BINARY_MOVEMENT, bool(code & BINARY_MOVEMENT)))
                if kind == 0:
                    self.vis[pivot] = (bool(default), keys, True)

    def _add(self, pivot, kind, keys):
        if kind in (0, 1, 2, 6):
            self.keys[(pivot, kind)] = keys

    def _value(self, pivot, kind, frame, default):
        keys = self.keys.get((pivot, kind))
        if not keys:
            return default
        if frame <= keys[0][0]:
            return list(keys[0][1])
        for (f0, v0, _), (f1, v1, step) in zip(keys, keys[1:]):
            if f0 <= frame <= f1:
                if step or f1 == f0:
                    return list(v1 if frame >= f1 else v0)
                t = (frame - f0) / (f1 - f0)
                return slerp(v0, v1, t) if kind == 6 else [a + (b - a) * t for a, b in zip(v0, v1)]
        return list(keys[-1][1])

    def translation(self, pivot, frame):
        return [self._value(pivot, k, frame, [0.0])[0] for k in (0, 1, 2)]

    def rotation(self, pivot, frame):
        return self._value(pivot, 6, frame, [0.0, 0.0, 0.0, 1.0])

    def visible(self, pivot, frame):
        v = self.vis.get(pivot)
        if v is None:
            return True
        if len(v) == 3:                                     # time-coded: the state holds from each key on
            state = v[0]
            for f, b in v[1]:
                if f <= frame:
                    state = b
            return state
        default, bits = v
        return next((b for f, b in bits if f == int(round(frame))), default)


def hlod(data):
    """(model, hierarchy, {MESH NAME: bone index}) from the first (most detailed) LOD array."""
    found = _first(data, HLOD)
    if not found:
        return None, None, {}
    o, s = found[0]
    model = hier = None
    bones = {}
    for t, o2, s2, has_sub in chunks(data, o + 8, o + 8 + s):
        if t == HLOD_HEADER:
            model, hier = _cstr(data[o2 + 16:o2 + 32]), _cstr(data[o2 + 32:o2 + 48])
        elif has_sub and not bones:
            for t3, o3, _, _ in chunks(data, o2 + 8, o2 + 8 + s2):
                if t3 == HLOD_SUB_OBJECT:
                    bone = struct.unpack_from("<I", data, o3 + 8)[0]
                    bones[_cstr(data[o3 + 12:o3 + 44]).split(".")[-1].upper()] = bone
    return model, hier, bones


def influences(mesh_bytes):
    """[primary bone per vertex] of a skinned mesh chunk, or None."""
    for t, o, s, _ in chunks(mesh_bytes, 8, len(mesh_bytes)):
        if t == VERTEX_INFLUENCES:
            return [struct.unpack_from("<H", mesh_bytes, o + 8 + 8 * i)[0] for i in range(s // 8)]
    return None


def mesh_frames(mesh, bones, skel, pose):
    """[(world matrix, visible)] per vertex of a Mesh (sagekit.formats.w3d) under a pose from
    skel.pose(): its HLOD bone for a rigid mesh, each vertex's bone for a skinned one."""
    world, vis = pose
    infl = influences(mesh.bytes) if mesh.skinned else None
    if infl is None:
        b = bones.get(mesh.name, 0)
        return [(world[b], vis[b])] * len(mesh.verts)
    own = vis[bones.get(mesh.name, 0)]
    return [(world[i], own) for i in infl]


def set_hlod_bones(data, bones):
    """Model bytes with the HLOD sub-objects of the meshes in `bones` ({MESH NAME: bone index}) on
    those bones (a mesh turned into a skin hangs on bone 0 like EA's); sizes unchanged."""
    d = bytearray(data)
    for t, o, s, _ in chunks(d, 0, len(d)):
        if t != HLOD:
            continue
        for t2, o2, s2, has_sub in chunks(d, o + 8, o + 8 + s):
            if not has_sub:
                continue
            for t3, o3, _, _ in chunks(d, o2 + 8, o2 + 8 + s2):
                name = _cstr(d[o3 + 12:o3 + 44]).split(".")[-1].upper()
                if t3 == HLOD_SUB_OBJECT and name in bones:
                    struct.pack_into("<I", d, o3 + 8, bones[name])
    return bytes(d)
