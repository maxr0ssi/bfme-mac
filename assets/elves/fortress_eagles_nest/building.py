"""The fortress's eagle's nest (Draw ModuleTag_EaglesNestDraw of ElvenCitadel): the slender pillar in
the courtyard's middle that carries the Great Eagle's perch, crowned and hung with the player's
colours.

EA's pillar (EBFENEST1, 718 triangles, drawn at the fortress's origin; mesh coordinates): a square
flared foot (|x|, |y| 14.43 at z 0 to 10.53 at 13.67 and 8.84 at 24.0), a knotwork band to 41.28, an
octagonal shaft tapering from 7.97 (z 52.14) to 6.84 (z 96.91), a head block (|x|, |y| 8.69, z
102.26..123.5) with a pointed arch recess on each face (12 wide, z 103.2..121.7; the recessed face
at 8.0), and the perch (a knotted post and a beam cross to |x|, |y| 12.98, z 124.5..141.01). EA's
eagle (EBFE, its own Draw module, left as it is) sits on the perch: x -21.1..13.5, |y| 35.3, z
137.2..182.3, so nothing new comes above z 134.

The redesign: a leaf banner on each face of the shaft hung from under the head (7 x 30, house colour),
a silver-and-enamel pointed arch frame round each head recess, a moulded cornice under the perch
with a crystal lantern on each corner, a knotwork band round the shaft's foot and moulded collars at
the foot's steps."""
import math

from sagekit.building import Building

from ..style import ElvenStyle



HEAD = 8.69                   # the head block's faces
HEAD_Z = (102.26, 123.5)
RECESS = (6.0, 103.2, 112.0, 121.7)          # half width, foot, springing, tip of the recess arch
BANNER = (101.9, 7.0, 30.0, 7.9, 0.1)       # rod z, width, length, plane (in the head's plan), d
FOOT = [(13.67, 10.53), (24.02, 8.84)]       # (z, half width) of the foot's steps
SHAFT = (7.93, 3.66)                         # the shaft's octagon at z 52.5: axis faces, their half width


def faces():
    """(anchor at z 0 on the plane |p| = 1, t, n) for the four sides (t x n = -z)."""
    from mathutils import Vector as V
    out = []
    for k in range(4):
        a = math.radians(90 * k)
        n = V((math.cos(a), math.sin(a), 0))
        out.append((n, V((-n.y, n.x, 0)), n))
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
        "close": ((0.0, 0.0, 108.0), 105, 16, -30, 45),
        "ingame": ((-0.0, -0.0, 70.5), 734, 53, -62, 50),
    }

    def design(self, kit):
        from sagekit.blender.geometry import box_rings, loft
        out = []
        z_top, width, length, plane, d = BANNER
        half, z0, spring, apex = RECESS
        for n, t, _ in faces():
            out += kit.leaf_banner(n * plane, t, n, 0.0, z_top, width, length, d=d, free=True)
            out += kit.arch(n * HEAD, t, n, 0.0, half, z0, spring, apex, w=0.85, d0=0.0, d1=0.55, ogee=0.25, k=7,
                            finial=False)

        def B(h, z):
            return box_rings((-h, h), (-h, h), z, 0.0)
        out.append(loft([B(8.6, 122.3), B(9.25, 122.9), B(9.45, 123.4), B(9.45, 123.8), B(9.1, 124.25)],
                        ["trim", "coping", "trim", "trim"], cap0=("stoneB", False), cap1=("top", True)))
        for sx in (-1, 1):                       # crystal lanterns on the cornice's corners
            for sy in (-1, 1):
                out += kit.crystal_lantern(sx * 8.3, sy * 8.3, 124.2, h=7.6, r=1.15)
        # a knotwork band round the shaft's foot, where EA's pointed wedges meet (octagon: the faces
        # toward the axes |u| <= 3.67 at 7.97, the diagonals between)
        a, b = SHAFT
        octa = [(a, -b), (a, b), (b, a), (-b, a), (-a, b), (-a, -b), (-b, -a), (b, -a), (a, -b)]
        out += kit.filigree_band(octa, 52.5, 54.6, d=0.3, center=(0, 0))
        for z, h in FOOT:                        # silver collars on the foot's steps, an enamel fillet
            out.append(loft([B(h - 0.3, z - 0.55), B(h + 0.35, z - 0.2), B(h + 0.35, z + 0.25), B(h - 0.3, z + 0.6)],
                            ["trim", "enamel", "coping"], cap0=("stoneB", False), cap1=("top", False)))
        return out

    def emphasis(self, c, n):
        return 1.4 if c.z > 95 else 1.0
