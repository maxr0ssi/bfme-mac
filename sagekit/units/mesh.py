"""New rigid pieces on an EA mesh, each bound to one of EA's bones, written by sagekit's mesh writer.

A Mesh starts empty (EA's mesh is replaced by the pieces) or, keep=True, with EA's vertices and
triangles exactly (positions, bones and skin weights, triangles; only the UVs move into the atlas'
left half). Pieces
are faces, bevelled boxes and tubes in the model's rest space; each vertex is stored in its bone's
rest space, so the piece follows that bone in every animation.

A rigid EA mesh (an HLOD sub-object on one bone, like the orc porter's CART and WHEEL_*) stays
rigid: every piece follows its bone. skin=True makes it a skin, so pieces may follow any bone; the
build hangs it on bone 0 like EA's skins (w3dpose.set_hlod_bones).

The atlas (paint.py): its left half is EA's character sheet tiled 4 x 4, its right half 16 swatch
tiles (tag 0..15, row-major). keep_uv and uv_for map into those halves.
"""
import math

from ..formats import w3dmesh as WM
from ..formats import w3dpose as P
from ..formats.w3d import NORMALS, STAGE_TEXCOORDS, VERTICES, rename_textures


def uv_for(tag, u, v):
    """(u, v) in swatch tile `tag` of the atlas' right half, inset by 5 %."""
    return (.5 + ((tag % 4) + .05 + .9 * u) / 8, 1 - ((tag // 4) + .95 - .9 * v) / 4)


def keep_uv(u, v):
    """EA's body UV (tiling in -2..2) in the atlas' left half, where EA's sheet repeats 4 x 4."""
    return ((u + 2) / 8, (v + 2) / 4)


class Mesh:
    """This recipe's polygons, bound to the existing rig and serialized by sagekit's mesh writer."""
    uv_for = staticmethod(uv_for)
    keep_uv = staticmethod(keep_uv)

    def __init__(self, original, skeleton, keep=False, names=None, bone="CART", rigid_bone=0, skin=None):
        self.original, self.skeleton = original, skeleton
        self.names, self.default_bone, self.rigid_bone = dict(names or {}), bone, rigid_bone
        self.skinned = original.skinned if skin is None else skin
        self.converted = self.skinned and not original.skinned
        self.kept = keep
        self.verts, self.tris = [], []
        if keep:
            bones = P.influences(original.bytes) if original.skinned else [rigid_bone] * len(original.verts)
            for i, b in enumerate(bones):
                self.verts.append((0, [(i, 1)], P.IDENTITY, b,
                                   {STAGE_TEXCOORDS: self.keep_uv(*original.uv[i])}))
            self.tris = list(zip(original.tris, original.surface))

    def _bone(self, bone):
        if self.skinned:
            return self.skeleton.index(bone or self.default_bone)
        if bone and self.skeleton.index(bone) != self.rigid_bone:
            raise ValueError("%s is rigid on bone %d: make it a skin (skin=True) to bind a piece to %s"
                             % (self.original.name, self.rigid_bone, bone))
        return self.rigid_bone

    def face(self, points, tag, bone=None, uvs=None):
        a, b, c = points[:3]
        e, f = [b[k] - a[k] for k in range(3)], [c[k] - a[k] for k in range(3)]
        n = (e[1] * f[2] - e[2] * f[1], e[2] * f[0] - e[0] * f[2], e[0] * f[1] - e[1] * f[0])
        if sum(x * x for x in n) < 1e-12:
            raise ValueError("degenerate design face")
        bone = self._bone(bone)
        transform = P.invert(self.skeleton.rest[bone])
        off = len(self.verts)
        uv = uvs or [(0, 0), (1, 0), (1, 1), (0, 1)][:len(points)]
        for p, (u, v) in zip(points, uv):
            self.verts.append((0, [(0, 1)], transform, bone,
                               {VERTICES: p, NORMALS: n, STAGE_TEXCOORDS: self.uv_for(tag, u, v)}))
        self.tris += [((off, off + i, off + i + 1), self.original.surface[0]) for i in range(1, len(points) - 1)]

    def box(self, lo, hi, tag, bone=None):
        """A box with bevelled edges (an octagon ring at each of four heights)."""
        x, y, z = lo
        X, Y, Z = hi
        bevel = min(.09, min(X - x, Y - y, Z - z) / 5)
        rings = []
        for inset, zz in [(bevel, z), (0, z + bevel), (0, Z - bevel), (bevel, Z)]:
            a, b, c, d = x + inset, X - inset, y + inset, Y - inset
            k = bevel * .4 if inset else bevel
            rings.append([(a + k, c, zz), (b - k, c, zz), (b, c + k, zz), (b, d - k, zz),
                          (b - k, d, zz), (a + k, d, zz), (a, d - k, zz), (a, c + k, zz)])
        for lower, upper in zip(rings, rings[1:]):
            for i in range(8):
                j = (i + 1) % 8
                self.face([lower[i], lower[j], upper[j], upper[i]], tag, bone)
        for pts, zz, rev in [(rings[0], z, True), (rings[-1], Z, False)]:
            for i in range(8):
                j = (i + 1) % 8
                face = [((x + X) / 2, (y + Y) / 2, zz), pts[j if rev else i], pts[i if rev else j]]
                self.face(face, tag, bone, [((p[0] - x) / (X - x), (p[1] - y) / (Y - y)) for p in face])

    def tube(self, a, b, r, tag, bone=None, sides=10, r1=None):
        """A capped tube from a to b, radius r (r1 at b)."""
        d = [b[i] - a[i] for i in range(3)]
        length = math.sqrt(sum(x * x for x in d))
        d = [x / length for x in d]
        up = (0, 0, 1) if abs(d[2]) < .9 else (0, 1, 0)
        u = (d[1] * up[2] - d[2] * up[1], d[2] * up[0] - d[0] * up[2], d[0] * up[1] - d[1] * up[0])
        q = math.sqrt(sum(x * x for x in u))
        u = [x / q for x in u]
        v = (d[1] * u[2] - d[2] * u[1], d[2] * u[0] - d[0] * u[2], d[0] * u[1] - d[1] * u[0])
        rings = [[tuple(c[j] + radius * (u[j] * math.cos(i * 2 * math.pi / sides) + v[j] * math.sin(i * 2 * math.pi / sides))
                        for j in range(3)) for i in range(sides)] for c, radius in [(a, r), (b, r if r1 is None else r1)]]
        for i in range(sides):
            k = (i + 1) % sides
            self.face([rings[0][i], rings[0][k], rings[1][k], rings[1][i]], tag, bone)
            self.face([a, rings[0][k], rings[0][i]], tag, bone)
            self.face([b, rings[1][i], rings[1][k]], tag, bone)

    def chunk(self):
        """The MESH chunk, its EA texture names swapped for the private ones (a shorter private
        name is padded with NULs: the writer keeps the texture chunks' sizes)."""
        m = self.original
        raw = WM.build_mesh(m.bytes, {0: WM.Source(m.bytes)}, m.name, m.container,
                            self.verts, self.tris, self.skinned, self.skeleton.rest)
        return rename_textures(raw, [(None, k, v.ljust(len(k), "\0")) for k, v in self.names.items()], m.name)
