"""Fitted siege-machine joinery; original meshes, UVs, rigs and visibility stay intact.

Called by the troop review builder. Death pieces receive their own surface-fitted details,
never attachments borrowed from the living rig. This module cannot install or launch anything.
"""
import math

from assets.dwarves.porter.unit import Mesh
from sagekit.formats import w3dmesh as WM, w3dpose as P
from sagekit.formats.w3d import NORMALS, STAGE_TEXCOORDS, TRIANGLES, VERTICES, chunks

SUPPORTED_MODELS = frozenset(('dubtlwagon_skn', 'dubtlwagon_diea', 'eudwarfram_skn',
                              'eudwarfram_dtha', 'ducatapult_skn', 'ducatapult_diea', 'ducatapult_a'))
# Existing occupied material samples, normalized IMAGE coordinates (top-left origin).
# No atlas extension, source-island movement or additional texture is needed.
UV_PATCHES = {
    'dubtlwagon': {'bronze': (.40, .11, .93, .14), 'iron': (.12, .12, .19, .19),
                   'wood': (.39, .52, .64, .62), 'ground': (.45, .21, .78, .27)},
    'eudwarfram': {'bronze': (.08, .25, .41, .28), 'iron': (.62, .37, .70, .44),
                   'wood': (.07, .34, .43, .48), 'ground': (.11, .69, .41, .72)},
    'ducatapult': {'bronze': (.11, .405, .83, .48), 'iron': (.86, .30, .96, .37),
                   'wood': (.43, .51, .63, .59), 'ground': (.20, .23, .57, .30)},
}


def add(a, b, scale=1):
    return tuple(x + scale*y for x, y in zip(a, b))


def normal(points):
    a, b = add(points[1], points[0], -1), add(points[2], points[0], -1)
    n = (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
    size = math.sqrt(sum(x*x for x in n))
    return tuple(x/size for x in n) if size else (0, 0, 0), size/2


class Fittings(Mesh):
    def __init__(self, original, skeleton, sheet):
        self.original, self.skeleton, self.sheet = original, skeleton, sheet
        self.bones = P.influences(original.bytes)
        self.verts = [(0, [(i, 1)], P.IDENTITY, b, {}) for i, b in enumerate(self.bones)]
        self.tris = list(zip(original.tris, original.surface))
        self.world = [P.point(skeleton.rest[b], v) for v, b in zip(original.verts, self.bones)]
        self.used = set()

    def face(self, points, tag, bone, uvs=None):
        n, area = normal(points)
        assert area > 1e-10, 'degenerate fitting'
        bone = self.skeleton.index(bone) if isinstance(bone, str) else bone
        transform = P.invert(self.skeleton.rest[bone])
        x, y, X, Y = UV_PATCHES[self.sheet][tag]
        off = len(self.verts)
        uvs = uvs or [(0, 0), (1, 0), (1, 1), (0, 1)][:len(points)]
        for p, (u, v) in zip(points, uvs):
            self.verts.append((0, [(0, 1)], transform, bone,
                               {VERTICES: p, NORMALS: n,
                                STAGE_TEXCOORDS: (x+(X-x)*u, 1-(y+(Y-y)*v))}))
        self.tris += [((off, off+i, off+i+1), self.original.surface[0])
                      for i in range(1, len(points)-1)]

    def chunk(self):
        m = self.original
        raw = bytearray(WM.build_mesh(m.bytes, {0: WM.Source(m.bytes)}, m.name, m.container,
                                      self.verts, self.tris, True, self.skeleton.rest))
        # The shared writer normalizes normals and regenerates face planes. Retain the exact
        # original prefixes, including tangent frames/colour channels, for the untouched art.
        def arrays(data, begin, end):
            for tag, offset, size, nested in chunks(data, begin, end):
                if tag in WM.PER_VERTEX or tag == TRIANGLES:
                    yield tag, offset+8, size
                elif nested:
                    yield from arrays(data, offset+8, offset+8+size)
        old = list(arrays(m.bytes, 8, len(m.bytes)))
        new = list(arrays(raw, 8, len(raw)))
        assert [a[0] for a in old] == [a[0] for a in new]
        for (_, a, size), (_, b, _) in zip(old, new):
            raw[b:b+size] = m.bytes[a:a+size]
        return bytes(raw)

    def gusset(self, target, outward, max_size=2.1):
        """A small bevelled plate lies entirely inside one existing rigid bone's triangle."""
        choices = []
        for i, tri in enumerate(self.original.tris):
            if i in self.used or len({self.bones[v] for v in tri}) != 1:
                continue
            pts = [self.world[v] for v in tri]
            n, area = normal(pts)
            if area < 2 or sum(a*b for a, b in zip(n, outward)) < .45:
                continue
            center = tuple(sum(p[k] for p in pts)/3 for k in range(3))
            choices.append((math.dist(target, center), i, pts, n, center))
        if not choices:
            return
        distance, index, pts, n, center = min(choices)
        if distance > 12:
            return
        self.used.add(index)
        bone = self.bones[self.original.tris[index][0]]
        radius = max(math.dist(p, center) for p in pts)
        shrink = min(.74, max_size/radius)
        # Triangular reinforcement is embedded at its foot, raised at the rim. Inset face
        # and little angular inlay stay on this bone even when the original face breaks away.
        foot = [add(center, add(p, center, -1), shrink) for p in pts]
        rim = [add(p, n, .16) for p in foot]
        inner = [add(add(center, add(p, center, -1), .72), n, .16) for p in foot]
        for i in range(3):
            j = (i+1) % 3
            self.face([foot[i], foot[j], rim[j], rim[i]], 'bronze', bone)
            self.face([rim[i], rim[j], inner[j], inner[i]], 'bronze', bone)
        self.face(inner, 'iron', bone)
        # Two narrow strokes echo the angular building inlays without stretching a rune sheet.
        a, b, c = inner
        tip = add(add(a, b), c)
        tip = tuple(x/3 for x in tip)
        for p in (a, b):
            end = add(tip, add(p, tip, -1), .53)
            start = add(tip, add(c, tip, -1), .32)
            edge = add(p, tip, -1)
            length = math.sqrt(sum(x*x for x in edge))
            side = (n[1]*edge[2]-n[2]*edge[1], n[2]*edge[0]-n[0]*edge[2],
                    n[0]*edge[1]-n[1]*edge[0])
            side = tuple(x*.045/length for x in side)
            self.face([add(add(start, side), n, .015), add(add(end, side), n, .015),
                       add(add(end, side, -1), n, .015), add(add(start, side, -1), n, .015)],
                      'bronze', bone)

    def hubs(self, names):
        for name in names:
            bone = self.skeleton.index(name)
            points = [p for p, b in zip(self.world, self.bones) if b == bone]
            if not points:
                continue
            pivot = P.point(self.skeleton.rest[bone], (0, 0, 0))
            side = 1 if pivot[1] > 0 else -1
            y = (max if side > 0 else min)(p[1] for p in points)
            a = (pivot[0], y-side*.12, pivot[2])
            b = add(a, (0, side*.48, 0))
            self.tube(a, b, 1.02, 'bronze', name, sides=8, r1=.8)
            self.tube(b, add(b, (0, side*.12, 0)), .49, 'iron', name, sides=8)


def design(w, sk, model_name):
    """Return changed mesh chunks only; the caller preserves all other W3D chunks."""
    model_name = model_name.lower().removesuffix('.w3d')
    if model_name not in SUPPORTED_MODELS:
        return {}
    if model_name.startswith('dubtlwagon'):
        mesh, sheet = ('DW_P19' if model_name.endswith('diea') else 'DUBTLWAGONM'), 'dubtlwagon'
        targets = [((x, s*10, z), (0, s, 0))
                   for x, z in [(-16, 11), (-17, 21), (-5, 19), (2, 22)] for s in (-1, 1)]
        wheels = ('WHEEL_R', 'WHEEL_L')
    elif model_name.startswith('eudwarfram'):
        mesh, sheet = ('RAM01' if model_name.endswith('dtha') else 'RAMSKINM'), 'eudwarfram'
        targets = [((x, s*y, z), (0, s, 0))
                   for x, y, z in [(0, 9, 23), (0, 10, 39), (13, 5, 16), (-12, 8, 8)]
                   for s in (-1, 1)]
        targets += [((19, 0, 17), (1, 0, 0))]
        wheels = ('WHEELR01', 'WHEELR02', 'WHEELL01', 'WHEELL02')
    else:
        mesh, sheet = ('CATAPULTM' if model_name.endswith('skn') else 'CATAPULT'), 'ducatapult'
        targets = [((x, s*y, z), (0, s, 0))
                   for x, y, z in [(-7, 8, 8), (14, 8, 10), (8, 20, 19), (0, 8, 23)]
                   for s in (-1, 1)]
        targets += [((24, s*6, 7), (1, 0, 0)) for s in (-1, 1)]
        wheels = ('B_CAT_WHEELFRTR', 'B_CAT_WHEELFRTL')
    original=w.meshes[mesh]
    # Preserve both skin channels on these source meshes; fittings use supported meshes only.
    if any(tag >= 0xC00 for tag, *_ in chunks(original.bytes,8,len(original.bytes))):
        return {}
    m = Fittings(original, sk, sheet)
    for point, outward in targets:
        m.gusset(point, outward)
    # Death wheels are fractured into other bones; each fragment already gets a fitted plate.
    if model_name.endswith(('skn', '_a')):
        m.hubs(wheels)
    return {mesh: m.chunk()}


def check(original, changed, skeleton):
    """Standalone check used by the troop builder, including the fitted death-fragment bones."""
    costs = {}
    for name, raw in changed.items():
        from sagekit.formats.w3d import Mesh as WMesh
        before, after = original.meshes[name], WMesh(raw, 0, len(raw)-8)
        count = len(before.verts)
        assert after.verts[:count] == before.verts, name
        assert after.uv[:count] == before.uv, name
        assert after.normals[:count] == before.normals, name
        assert after.tris[:len(before.tris)] == before.tris, name
        old_bones, new_bones = P.influences(before.bytes), P.influences(raw)
        assert new_bones[:count] == old_bones, name
        assert set(new_bones[count:]) <= set(old_bones), name
        assert all(0 <= b < len(skeleton.pivots) for b in new_bones), name
        assert all(math.isfinite(x) for v in after.verts for x in v), name
        costs[name] = {'added_vertices': len(after.verts)-count,
                       'added_triangles': len(after.tris)-len(before.tris),
                       'attachment_bones': sorted({skeleton.names[b] for b in new_bones[count:]})}
    return costs


if __name__ == '__main__':
    import json
    from pathlib import Path
    from sagekit import paths
    from sagekit.formats.w3d import W3DFile
    source = Path(paths.BUILD)/'dwarves/troops/src'
    results = {}
    for model in sorted(SUPPORTED_MODELS):
        path = source/(model+'.w3d')
        w = W3DFile(str(path))
        sk = P.Skeleton((source/w.skeleton()).read_bytes() if w.skeleton() else path.read_bytes())
        results[model] = check(w, design(w, sk, model), sk)
    print(json.dumps(results, indent=2))
