"""The fortress's eagle's nest (Draw ModuleTag_EaglesNestDraw of ElvenCitadel): the slender pillar in
the courtyard's middle that carries the Great Eagle's perch, dressed in the citadel's silver and
gold. Its head rises over the mallorn canopy (z 99) and the tree-houses (to z 122.9), so the work
is up there: silver frames round the head's arches, a silver sill band under them and a cornice
over them, the citadel's crystal lanterns on silver posts on the cornice's corners, and a silver
necking with a ring of gilt leaves where the shaft flowers into the head. No banners: the pillar
stands in the trees, where cloth would be lost, and the eagle is its emblem.

EA's pillar (EBFENEST1, 718 triangles, drawn at the fortress's origin; mesh coordinates): a square
flared foot (|x|, |y| 14.43 at z 0 to 10.53 at 13.67 and 8.84 at 24.0), a knotwork band to 41.28, an
octagonal shaft (axis faces at apothem 7.97 at z 52.14 tapering to 6.82 at 96.91, the diagonal
faces 0.25 further out) that flares to the head block (|x|, |y| 8.69, z 102.26..123.5) with a
pointed arch recess on each face (12 wide, z 103.2..121.7; the recessed face at 8.0), and the perch
(knotted roots on the axes at z 124.8..126.2, a beam cross along the axes to |x|, |y| 12.98 at z
138.4..141.01). EA's eagle (EBFE, its own Draw module, left as it is) sits on the perch from z 137.2,
so nothing new comes above z 135; the head's corners are free."""
import math

from sagekit.building import Building

from ..style import ElvenStyle

HEAD = 8.69                   # the head block's faces
RECESS = (6.0, 103.2, 112.0, 121.7)          # half width, foot, springing, tip of the recess arch
CORNICE_TOP = 124.25
LANTERNS = 8.25               # the corner lanterns' posts, on the cornice's corners (|x| = |y|)
FOOT = [(13.67, 10.53), (24.02, 8.84)]       # (z, half width) of the foot's steps
SHAFT = (7.93, 3.66)                         # the shaft's octagon at z 52.5: axis faces, their half width
NECK = 96.91                                 # the shaft's top, where it flares to the head
# the shaft's faces at z: axis faces 7.97 at 52.14 to 6.82 at 96.91, the diagonals 0.25 further out
AXIS_APO = (7.97, 52.14, 6.82, 96.91)


def axis_apo(z):
    a0, z0, a1, z1 = AXIS_APO
    return a0 + (a1 - a0) * (z - z0) / (z1 - z0)


def octagon(a, z):
    """The shaft's octagon ring at z grown by `a`: axis faces at axis_apo(z) + a, the diagonals 0.25
    further out (EA's vertices (6.82, 3.18) at the neck)."""
    from mathutils import Vector as V
    A = axis_apo(z) + a
    D = A + 0.25
    b = D * math.sqrt(2) - A
    pts = [(A, -b), (A, b), (b, A), (-b, A), (-A, b), (-A, -b), (-b, -A), (b, -A)]
    return [V((x, y, z)) for x, y in pts]


def faces():
    """(n, t) for the four sides (t x n = -z)."""
    from mathutils import Vector as V
    out = []
    for k in range(4):
        a = math.radians(90 * k)
        n = V((math.cos(a), math.sin(a), 0))
        out.append((n, V((-n.y, n.x, 0))))
    return out


class FortressEaglesNest(Building):
    style = ElvenStyle()
    source = "EBFENest"
    target = "EBFENEST1"
    facet_islands = 20                  # EA's organic mallorn wood: seams at EA's islands and 20-degree turns
    sheet = "EBFortress.tga"
    sheet_normal = "EBFortress_NRM.tga"
    own_textures = {"EBFortress.tga": "EBFortresJ.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_EaglesNestDraw",)
    tri_budget = 5000
    views = {
        "rts": ((-0.0, -0.0, 70.5), 323, 50, -38, 50),
        "close": ((0.0, 0.0, 110.0), 105, 16, -30, 45),
        "ingame": ((-0.0, -0.0, 70.5), 734, 53, -62, 50),
    }

    def design(self, kit):
        from sagekit.blender.geometry import box_rings, loft

        def B(h, z):
            return box_rings((-h, h), (-h, h), z, 0.0)
        out = []
        half, z0, spring, apex = RECESS
        for n, t in faces():                     # 1. silver frames round EA's four arch recesses
            out += kit.arch(n * HEAD, t, n, 0.0, half, z0, spring, apex, w=0.85, d0=0.0, d1=0.55, ogee=0.25, k=7,
                            finial=False)
        # 2. the head's sill band under the arches (EA's chamfer 7.95 at 102.26 to 8.69 at 103.2)
        out.append(loft([B(7.9, 102.1), B(8.95, 102.5), B(9.0, 103.3), B(8.75, 103.65)], ["trim", "trim", "trim"],
                        cap0=("stoneB", True), cap1=("trim", True)))
        # 3. the cornice under the perch
        out.append(loft([B(8.6, 122.3), B(9.25, 122.9), B(9.45, 123.4), B(9.45, 123.8), B(9.1, CORNICE_TOP)],
                        ["trim", "trim", "trim", "trim"], cap0=("stoneB", True), cap1=("top", True)))
        for sx in (-1, 1):                       # 4. the citadel's crystal lanterns on the corners
            for sy in (-1, 1):
                out += self._lantern(kit, sx * LANTERNS, sy * LANTERNS)
        out += self._necking(kit)                # 5. the necking: a silver astragal, gilt leaves under it
        # 6. the shaft's foot, mostly behind the citadel's ring: a knotwork band where EA's pointed
        #    wedges meet and silver collars on the foot's steps
        a, b = SHAFT
        octa = [(a, -b), (a, b), (b, a), (-b, a), (-a, b), (-a, -b), (-b, -a), (b, -a), (a, -b)]
        out += kit.filigree_band(octa, 52.5, 54.6, d=0.3, center=(0, 0))
        for z, h in FOOT:
            out.append(loft([B(h - 0.3, z - 0.55), B(h + 0.35, z - 0.2), B(h + 0.35, z + 0.25), B(h - 0.3, z + 0.6)],
                            ["trim", "trim", "trim"], cap0=("stoneB", True), cap1=("top", True)))
        # The collapse turns these ornaments over: retain their normally buried backs and caps.
        for solid in out:
            for poly in solid.polys:
                poly[2] = True
        return out

    @staticmethod
    def _lantern(kit, cx, cy):
        """A starlight crystal in a gilt cup on a short silver post, a gilt leaf on its tip (the
        citadel's ring lanterns, smaller): the tip at z 134.7, under the eagle."""
        from ..shapes import turned
        z = CORNICE_TOP - 0.1
        out = [turned(cx, cy, [(0.95, z), (0.95, z + 0.4), (0.62, z + 0.7), (0.42, z + 1.2), (0.36, z + 2.3), (0.75, z + 2.7)],
                      ["trim"] * 5, 10, cap0=("trim", False), cap1=("trim", True))]
        return out + kit.crystal_lantern(cx, cy, z + 2.6, h=6.2, r=1.05)

    @staticmethod
    def _necking(kit):
        """A silver astragal round the shaft just under its flare (z 94.8..96.8) and a ring of gilt
        leaves hanging from it down the shaft's faces: long ones on the axis faces, short ones on
        the diagonals - the capital EA's plain shaft never had."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import loft
        out = [loft([octagon(0.0, 94.8), octagon(0.42, 95.1), octagon(0.42, 96.2), octagon(0.1, 96.8)],
                    ["trim", "trim", "trim"], cap0=("stoneB", True), cap1=("trim", True))]
        for k in range(8):
            ang = math.radians(45 * k)
            n = V((math.cos(ang), math.sin(ang), 0))
            t = V((-n.y, n.x, 0))
            diag = k % 2 == 1
            length, width = (4.2, 2.1) if diag else (6.6, 2.9)
            apo = axis_apo(95.0) + (0.25 if diag else 0.0)
            # the shaft widens downwards (0.026 a unit): d leaves the blade 0.05 proud at its tip
            d = 0.12 + 0.026 * length
            out.append(kit.leaf_blade(n * apo, t, n, 0.0, 95.0, length, width, lean=math.pi, thick=0.12, d=d))
        return out

    def emphasis(self, c, n):
        return 1.4 if c.z > 94 else 1.0
