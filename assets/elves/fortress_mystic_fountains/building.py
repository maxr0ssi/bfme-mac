"""The fortress's mystic fountains (Draw ModuleTag_DrawMysticFountains of ElvenCitadel): eight half-round
basins hung on the ring's faces, a swan in each pouring water. Each basin gets a gilt lip, a pair of
starlight crystal lanterns at its ends, and - over the six on the gable faces - a leaf banner in the
player's colour between the swan and the ring's frieze (the faces toward +-45 carry the fortress's
own ring banners, which end over their swans).

EA's model (EBFMFOUNT1, 1520 triangles, drawn at the fortress's origin; mesh coordinates): on each
face (toward +-45, +-67.5, +-112.5, +-157.5 degrees; outward n, along-face t) a basin centred at
radial 49.9 in the window recess (glass at radial 50.5; the ring's face at 52.5), radius 7.75 at its
widest (z 22.25), the lip curling in to 6.35 at its top (z 23.53), the half cone down to the wall at
z 13.57; the swan (radial 50.2..54.3) to z 31.5, its wings at |t| 7.8. The two basins toward +-45
hang 3.0 lower. EA's water (EBFMFOUNT2, EBFMFOUNT3) is untouched.

Height (measured from the model's foot, z 10.57): the banners' rods reach z 39.6 over EA's 31.5,
+38 % (max_z_growth 0.40, as the Dwarven old castle hub): under the 20 % default (35.7) there is no
room for cloth between the swans' heads and the top."""
import math

from sagekit.building import Building

from ..style import ElvenStyle



FACES = [(67.5, 0.0), (112.5, 0.0), (157.5, 0.0), (-67.5, 0.0), (-112.5, 0.0), (-157.5, 0.0), (45.0, -3.0), (-45.0, -3.0)]
CENTRE, LIP_Z = 49.9, 23.53           # the basins' centre (radial) and lip top
LIP_R = 6.4                           # the gilt lip's radius: its bead reaches 6.9, inside the rim (x 42.2 at +-45)
RING = 52.5
BANNER = (38.6, 5.8, 6.4, 0.35)       # rod z (its leaf-bud ends 39.6), width, length (tip 32.2, over the swans' 31.5), d


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
    max_z_growth = 0.40
    tri_budget = 5000
    views = {
        "rts": ((-5.8, -0.0, 21.0), 320, 50, -38, 50),
        "close": ((19.1, -46.1, 28.0), 70, 18, -40, 45),
        "ingame": ((-5.8, -0.0, 21.0), 727, 53, -62, 50),
    }

    def design(self, kit):
        from sagekit.blender.geometry import sweep
        out = []
        for deg, dz in FACES:
            n, t = axes(deg)
            c = n * CENTRE
            z = LIP_Z + dz
            # the gilt lip: a bead sweeping round the basin's rim from wall to wall
            path = []
            for i in range(7):
                p = math.radians(-90 + 30 * i)
                q = c + (n * math.cos(p) + t * math.sin(p)) * LIP_R
                path.append((q.x, q.y))
            prof = [(-0.45, z - 0.25), (0.4, z - 0.25), (0.5, z + 0.2), (0.0, z + 0.5), (-0.5, z + 0.15)]
            out += sweep(path, prof, [None, "gilt", "gilt", "gilt", "gilt"], center=(c.x, c.y))[0]
            # starlight lanterns standing on the lip's ends, by the wall
            for s in (-1, 1):
                p = math.radians(78)
                q = c + (n * math.cos(p) + t * (s * math.sin(p))) * LIP_R
                out += kit.crystal_lantern(q.x, q.y, z + 0.3, h=3.4, r=0.6, k=6, finial=False)
            # a leaf banner over the swan on the gable faces
            if dz == 0.0:
                z_top, width, length, d = BANNER
                out += kit.leaf_banner(n * RING, t, n, 0.0, z_top, width, length, d=d, free=True)
        return out

    def emphasis(self, c, n):
        return 1.3 if c.z > 22 else 1.0
