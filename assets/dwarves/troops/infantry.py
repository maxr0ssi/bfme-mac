"""Fitted Erebor troop metalwork; originals and animation attachment points stay intact.

The caller owns private texture aliases/material recolouring. No source atlas is resized.
Run ``python3 -m assets.dwarves.troops.infantry`` for the extracted-source geometry check.
"""
import json
import math
from collections import defaultdict
from pathlib import Path

from assets.dwarves.porter.unit import Mesh as PorterMesh
from sagekit.formats import w3dmesh as WM, w3dpose as P
from sagekit.formats.w3d import MESH, NORMALS, STAGE_TEXCOORDS, VERTICES, W3DFile, chunks
from sagekit.formats.w3dframes import mesh_bones

supported_modelnames = (
    'eudwarfgua_skn', 'duphalanx_skn', 'eudwarfaxe_skn', 'ruarcher_skn',
    'rudwrfhlbd_skn', 'rudwrfhmr_skn', 'duguaban_skn', 'duaxdban_skn',
    'duphaban_skn', 'ruyeobnr_skn', 'duphalanxa_skn', 'duphalanxb_skn',
)
# Existing metal pixels, normalized image coordinates (top-left origin). Added geometry
# samples these same sheets, so both original and Mithril texture replacements still work.
METAL = {'eudwarfgua': (.035, .554), 'eudwarfgua_banner': (.035, .554),
         'duphalanx_01': (.074, .700), 'eudwarfaxe': (.053, .455),
         'ruarcher': (.838, .409), 'rudwarf_b': (.899, .483),
         'duaxdban1': (.440, .087), 'ruyeobanner': (.440, .087)}
# Count/radius are deliberately small: this is raised forged edging, not new anatomy.
RECIPES = {
    'eudwarfgua_skn': {'SHIELD': (14, .075), 'SHOULDER': (8, .065),
                         'AXE': (8, .060), 'HAMMER1': (10, .060)},
    'duphalanx_skn': {'SHIELD': (12, .065), 'PIKE': (8, .050)},
    'eudwarfaxe_skn': {'SHIELD': (10, .065), 'AXE01': (8, .055)},
    'ruarcher_skn': {'HELMET': (8, .050), 'SHOULDER': (8, .060)},
    'rudwrfhlbd_skn': {'HELMET': (8, .055), 'SHIELD': (8, .055), 'MATTOCK': (10, .065)},
    'rudwrfhmr_skn': {'HELMET': (8, .055), 'SHIELD': (8, .055), 'HAMMER': (10, .065)},
    'duguaban_skn': {'OBJECT13': (8, .065), 'AXE01': (8, .055)},
    'duaxdban_skn': {'AXE01': (8, .055)},
    'duphaban_skn': {'CYLINDER01': (12, .065), 'AXE01': (8, .055)},
    'ruyeobnr_skn': {'HELMET': (8, .050), 'SHOULDER': (8, .060), 'SWORD': (6, .045)},
    'duphalanxa_skn': {'CYLINDER01': (12, .065), 'OBJECT01': (8, .050)},
    'duphalanxb_skn': {'CYLINDER01': (12, .065), 'OBJECT01': (8, .050)},
}
BODIES = {'eudwarfgua_skn': 'DWARF', 'duphalanx_skn': 'DWARF',
          'eudwarfaxe_skn': 'DWARF', 'ruarcher_skn': 'BODY',
          'rudwrfhlbd_skn': 'BODY', 'rudwrfhmr_skn': 'BODY',
          'duguaban_skn': 'OBJECT12', 'duaxdban_skn': 'DWARF',
          'duphaban_skn': 'OBJECT03', 'ruyeobnr_skn': 'BODY',
          'duphalanxa_skn': 'OBJECT03', 'duphalanxb_skn': 'OBJECT03'}


def unit(v):
    length = math.sqrt(sum(x*x for x in v))
    return tuple(x / length for x in v) if length > 1e-9 else (0., 0., 0.)


def normal(a, b, c):
    e, f = [b[k]-a[k] for k in range(3)], [c[k]-a[k] for k in range(3)]
    return unit((e[1]*f[2]-e[2]*f[1], e[2]*f[0]-e[0]*f[2], e[0]*f[1]-e[1]*f[0]))


class Mesh(PorterMesh):
    """Reuse the craftsman's primitives, preserving original UVs and rigid/skinned type."""
    def __init__(self, original, skeleton, rigid_bone):
        super().__init__(original, skeleton)
        self.bones = P.influences(original.bytes) or [rigid_bone]*len(original.verts)
        self.verts = [(0, [(i, 1)], P.IDENTITY, b, {}) for i, b in enumerate(self.bones)]
        self.tris = list(zip(original.tris, original.surface))
        self.world = [P.point(skeleton.rest[b], v) for b, v in zip(self.bones, original.verts)]
        texture = Path(original.textures[0]).stem.lower()
        self.patch = METAL[texture]

    def face(self, points, tag, bone, uvs=None):
        # Constant tiny metal crop avoids stretching skin/cloth across the fitted trim.
        start = len(self.verts)
        super().face(points, tag, bone, uvs)
        u, v = self.patch
        for i in range(start, len(self.verts)):
            self.verts[i][4][STAGE_TEXCOORDS] = (u + .002*(i % 2), 1-v + .002*((i//2) % 2))

    def chunk(self):
        return WM.build_mesh(self.original.bytes, {0: WM.Source(self.original.bytes)},
                             self.original.name, self.original.container, self.verts, self.tris,
                             self.original.skinned, self.skeleton.rest)

    def edging(self, count, radius):
        """Weld positions only for edge discovery; source vertex/UV seams are untouched."""
        edges = defaultdict(list)
        for tri in self.original.tris:
            if len({self.bones[i] for i in tri}) != 1:
                continue
            pts = [self.world[i] for i in tri]
            n = normal(*pts)
            if not any(n):
                continue
            for i, j in zip(tri, tri[1:]+tri[:1]):
                key = tuple(sorted((tuple(round(x, 4) for x in self.world[i]),
                                    tuple(round(x, 4) for x in self.world[j])))) + (self.bones[i],)
                edges[key].append((i, j, n))
        candidates = []
        for key, faces in edges.items():
            a, b, bone = key
            length = math.dist(a, b)
            if length < radius*8 or length > 8:
                continue
            # True borders and forged corners only; flat triangulation diagonals disappear.
            if len(faces) > 1 and all(sum(x*y for x,y in zip(faces[0][2], f[2])) > .82
                                      for f in faces[1:]):
                continue
            n = unit(tuple(sum(f[2][k] for f in faces) for k in range(3)))
            candidates.append((length, a, b, bone, n))
        for _, a, b, bone, n in sorted(candidates, reverse=True)[:count]:
            # A shallow rail straddles the existing corner and follows its exact bone.
            ends = [tuple(p[k]+n[k]*radius*.40 for k in range(3)) for p in (a,b)]
            self.tube(*ends, radius, 0, self.skeleton.names[bone], sides=4)

    def clasp(self):
        """One raised angular breast-clasp fitted inside an actual rigid torso triangle."""
        choices = []
        for tri in self.original.tris:
            if len({self.bones[i] for i in tri}) != 1:
                continue
            bone = self.bones[tri[0]]
            if not any(x in self.skeleton.names[bone] for x in ('SPINE2', 'RIBS', 'SPINE1')):
                continue
            pts = [self.world[i] for i in tri]
            n = normal(*pts)
            center = tuple(sum(p[k] for p in pts)/3 for k in range(3))
            if n[0] < .35 or center[2] < 10 or abs(center[1]) > 2.3:
                continue
            area = math.dist(pts[0],pts[1])*math.dist(pts[1],pts[2])
            choices.append((area, pts, n, bone, center))
        if not choices:
            return
        _, pts, n, bone, c = max(choices)
        # Inset triangle with faceted peak: no protruding block or body replacement.
        ring = [tuple(c[k]+(p[k]-c[k])*.34+n[k]*.035 for k in range(3)) for p in pts]
        peak = tuple(c[k]+n[k]*.15 for k in range(3))
        for a,b in zip(ring, ring[1:]+ring[:1]):
            self.face([a,b,peak], 0, self.skeleton.names[bone])


def design(w: W3DFile, sk: P.Skeleton, model_name: str) -> dict:
    name = Path(model_name).stem.lower()
    if name not in supported_modelnames:
        raise ValueError('Unsupported infantry model: '+name)
    rigid = mesh_bones(w.data)
    recipes = RECIPES[name]
    result = {}
    for mesh_name in list(recipes) + [BODIES[name]]:
        original = w.meshes[mesh_name]
        # The shared writer cannot retain secondary skin positions/normals.
        # Keep those detailed source meshes whole, including both influence weights.
        if any(tag >= 0xC00 for tag, *_ in chunks(original.bytes,8,len(original.bytes))):
            continue
        # The shared writer drops unused vertices; leave these source bodies byte-exact.
        if len({i for tri in original.tris for i in tri}) != len(original.verts):
            continue
        mesh = Mesh(original, sk, rigid.get(mesh_name, 0))
        if mesh_name in recipes:
            mesh.edging(*recipes[mesh_name])
        else:
            mesh.clasp()
        if len(mesh.verts) > len(original.verts):
            result[mesh_name] = mesh.chunk()
    return result


def check_sources(folder=Path('build/assets/dwarves/troops/src')):
    """A runnable check of every source body, bone, UV, topology and effect mesh."""
    costs = {}
    for name in supported_modelnames:
        w = W3DFile(str(folder/(name+'.w3d')))
        sk = P.Skeleton((folder/w.skeleton().lower()).read_bytes())
        replacements = design(w, sk, name)
        new = W3DFile(WM.replace_meshes(w.data, replacements))
        assert replacements, name
        assert new.skeleton() == w.skeleton()
        assert [b for t,b in w.top() if t != MESH] == [b for t,b in new.top() if t != MESH]
        assert new.meshes.keys() == w.meshes.keys()
        for key, old in w.meshes.items():
            m = new.meshes[key]
            n = len(old.verts)
            assert m.verts[:n] == old.verts, (name, key, 'positions')
            assert m.uv[:n] == old.uv, (name, key, 'UVs')
            assert m.tris[:len(old.tris)] == old.tris
            assert m.skinned == old.skinned
            if m.skinned:
                assert P.influences(m.bytes)[:n] == P.influences(old.bytes)
                bones = P.influences(m.bytes)
                assert all(0 <= b < len(sk.pivots) for b in bones)
                assert all(len({bones[i] for i in t}) == 1 for t in m.tris[len(old.tris):])
            assert all(math.isfinite(x) for rows in (m.verts,m.normals,m.uv) for row in rows for x in row)
            assert all(0 <= i < len(m.verts) for t in m.tris for i in t)
            if key not in replacements:
                assert m.bytes == old.bytes
        costs[name] = dict(source_triangles=sum(len(m.tris) for m in w.meshes.values()),
                           added_triangles=sum(len(new.meshes[k].tris)-len(m.tris) for k,m in w.meshes.items()),
                           changed_meshes=list(replacements))
    return costs


if __name__ == '__main__':
    print(json.dumps(check_sources(), indent=2))
