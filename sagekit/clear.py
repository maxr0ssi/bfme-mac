"""EA's faces cleared from a target before a rebuilt design (`Building.clear`).

A rebuilt building keeps only EA's gameplay (footprint, bones, the pieces it keeps) and builds its
volumes again from the faction's kit: EA's faces there must go first, or they show through the new
solids. A recipe names them declaratively, in the target's coordinates (world ones for a
`world_space` recipe), and the geometry step clears them before design() (a recipe need not
reach into Blender for it, and the list says in one place what of EA's body is gone):

    clear = [Box((-45, -16, -1), (-0.45, 16.5, 80))]     faces whose centre lies in a box
    clear = [Piece((-27, 0.6, 70))]                      the connected piece of EA's mesh nearest a point
    clear = [Where(lambda c: c[0] < -0.45)]              a predicate on the face centre (x, y, z)
    clear = [ALL]                                        the whole mesh (a stand-in rebuilt entirely)

A plain callable counts as Where; several specs clear their union. Pure Python on the host (the
lists are small); sagekit/blender/clear.py applies them to a Blender mesh.
"""


class Where:
    """Faces whose centre (x, y, z) the predicate selects."""

    def __init__(self, fn):
        self.fn = fn

    def select(self, faces):
        return {f for f, c in enumerate(faces.centres) if self.fn(c)}


class Box(Where):
    """Faces whose centre lies in the axis-aligned box lo..hi."""

    def __init__(self, lo, hi):
        self.lo, self.hi = tuple(lo), tuple(hi)
        super().__init__(lambda c: all(a <= x <= b for a, x, b in zip(self.lo, c, self.hi)))


class Piece:
    """The connected piece(s) of EA's mesh (faces joined by vertices, welded by position: EA splits
    vertices at UV seams) holding the face nearest each point: a whole tower or hearth, without a
    box that must dodge its neighbours."""

    def __init__(self, *points):
        self.points = [tuple(p) for p in points]

    def select(self, faces):
        out = set()
        for p in self.points:
            near = min(range(len(faces.centres)), key=lambda f: sum((a - b) ** 2 for a, b in zip(faces.centres[f], p)))
            out |= faces.piece(near)
        return out


ALL = Where(lambda c: True)


class Faces:
    """A mesh's polygons (vertex index lists over `verts`): their centres and welded pieces."""

    def __init__(self, verts, polys):
        self.verts, self.polys = [tuple(v) for v in verts], [list(p) for p in polys]
        self.centres = [tuple(sum(self.verts[i][k] for i in p) / len(p) for k in range(3)) for p in self.polys]
        self._pieces = None

    def piece(self, f):
        if self._pieces is None:
            weld, parent = {}, {}
            key = [weld.setdefault(tuple(round(x, 3) for x in v), len(weld)) for v in self.verts]

            def find(x):
                while parent.setdefault(x, x) != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x
            for p in self.polys:
                for i in p[1:]:
                    parent[find(key[i])] = find(key[p[0]])
            self._pieces = [find(key[p[0]]) for p in self.polys]
        return {g for g, r in enumerate(self._pieces) if r == self._pieces[f]}


def select(specs, verts, polys):
    """{face index} the specs clear from a mesh (verts, polygons)."""
    faces, out = Faces(verts, polys), set()
    for s in specs or ():
        out |= (s if hasattr(s, "select") else Where(s)).select(faces)
    return out

