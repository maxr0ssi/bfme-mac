"""The fortress's mystic fountains (Draw ModuleTag_DrawMysticFountains of ElvenCitadel): eight half-round
basins hung in the ring's window recesses, a swan in each pouring water. Dressed as the citadel's
ring above them: a silver coping round each basin's lip, and on its ends, by the wall, a pair of the
citadel's starlight crystals in gilt cups with gilt leaf tips. No banners: the fortress's gate and
flèche carry its colours, and cloth over the swans hid them.

EA's model (EBFMFOUNT1, 1520 triangles, drawn at the fortress's origin; mesh coordinates): on each
face (toward +-45, +-67.5, +-112.5, +-157.5 degrees; outward n, along-face t) a basin centred at
radial 49.9 in the window recess (glass at radial 50.5; the ring's face at 52.5), radius 7.75 at its
widest (z 22.25), the lip curling in to 6.35 at its top (z 23.53), the half cone down to the wall at
z 13.57; the swan (radial 50.2..54.3) to z 31.5, its wings at |t| 7.8. Four basins sit 0.47 off
their face's middle (u below), the two toward +-45 hang 3.0 lower. EA's water (EBFMFOUNT2,
EBFMFOUNT3) is untouched. Nothing new rises over the swans (the crystals' gilt tips reach z 28.5)."""
import math

from sagekit.building import Building

from ..style import ElvenStyle

# (face, dz, u): the basin's face, its drop and its centre along the face (measured on EA's rims)
FACES = [(67.5, 0.0, -0.47), (112.5, 0.0, 0.47), (157.5, 0.0, 0.0), (-67.5, 0.0, 0.47), (-112.5, 0.0, -0.47),
         (-157.5, 0.0, 0.0), (45.0, -3.0, 0.0), (-45.0, -3.0, 0.0)]
CENTRE, LIP_Z = 49.9, 23.53           # the basins' centre (radial) and lip top
POOL_R, POOL_Z = 6.05, (-0.45, -0.16)  # the pool's sheet: radius, bottom and top (from the lip's top)
LIP_R = 6.4                           # the coping's radius: its nose reaches 6.9, inside the rim (x 42.2 at +-45)


def axes(deg):
    from mathutils import Vector as V
    a = math.radians(deg)
    n = V((math.cos(a), math.sin(a), 0))
    return n, V((-n.y, n.x, 0))


class FortressMysticFountains(Building):
    style = ElvenStyle()
    source = "EBFMFount"
    target = "EBFMFOUNT1"
    facet_islands = 20                  # EA's organic mallorn wood: seams at EA's islands and 20-degree turns
    sheet = "EBFortress.tga"
    sheet_normal = "EBFortress_NRM.tga"
    own_textures = {"EBFortress.tga": "EBFortresK.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_DrawMysticFountains",)
    tri_budget = 5000
    lifecycle = {"EBFMFount_D3": {"solid": 5.0}}  # split coping and pool slabs along EA's rubble pieces
    views = {
        "rts": ((-5.8, -0.0, 21.0), 320, 50, -38, 50),
        "close": ((19.1, -46.1, 24.0), 70, 18, -40, 45),
        "ingame": ((-5.8, -0.0, 21.0), 727, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V

        from sagekit.blender.geometry import loft, sweep
        out = []
        for deg, dz, u in FACES:
            n, t = axes(deg)
            c = n * CENTRE + t * u
            z = LIP_Z + dz
            # the silver coping: a rounded nose over the basin's lip, from wall to wall
            path = []
            for i in range(7):
                p = math.radians(-90 + 30 * i)
                q = c + (n * math.cos(p) + t * math.sin(p)) * LIP_R
                path.append((q.x, q.y))
            prof = [(-0.5, z - 0.3), (0.3, z - 0.3), (0.5, z + 0.05), (0.36, z + 0.42), (0.0, z + 0.55), (-0.5, z + 0.25)]
            out += sweep(path, prof, [None, "trim", "trim", "trim", "trim", "trim"], center=(c.x, c.y))[0]
            # the starlit pool: a sheet of crystal glass over EA's pool floor (whose teal tiles the
            # palette turns to ivory, which lost the water), under the coping's inner edge
            half = [c + (n * math.cos(math.radians(a)) + t * math.sin(math.radians(a))) * POOL_R for a in range(-90, 91, 30)]
            out.append(loft([[V((q.x, q.y, z + dzp)) for q in half] for dzp in POOL_Z],
                            [["crystal"] * 7], cap0=("crystal", True), cap1=("crystal", True)))
            # the citadel's starlight crystals on the coping's ends, by the wall
            for s in (-1, 1):
                p = math.radians(76)
                q = c + (n * math.cos(p) + t * (s * math.sin(p))) * LIP_R
                out += self._crystal(kit, q.x, q.y, z + 0.35)
        return out

    @staticmethod
    def _crystal(kit, cx, cy, z, h=3.6, r=0.62):
        """The citadel's starlight crystal in its gilt cup and cap, small, with a turned gilt tip for
        the leaf finial (whose blades would cost more than the rest of the basin's dress)."""
        from ..shapes import turned
        out = kit.crystal_lantern(cx, cy, z, h=h, r=r, k=6, finial=False)
        zt = z + 0.92 * h
        out.append(turned(cx, cy, [(0.2 * r, zt), (0.3 * r, zt + 0.12 * h), (0.05 * r, zt + 0.36 * h)], ["gilt", "gilt"], 6,
                          cap0=("gilt", False), cap1=("gilt", True)))
        return out

    def emphasis(self, c, n):
        return 1.3 if c.z > 20 else 1.0
