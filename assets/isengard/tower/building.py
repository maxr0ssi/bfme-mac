"""Isengard tower (IsengardTowerExpansion; model IBFITower): the citadel's tower expansion, a small
Orthanc - a square shaft tapering in bands to a flared crown of flanges and horns (z 130.5), its
faces set with pointed windows, knife fins round its foot, a wall stub toward the citadel (-X).
EA's body is Isengard already and stays whole; it takes the citadel's recipe:

- four lozenge blades on the shaft's diagonals from the plinth (z 0) to needles at z 121, their
  sharp edges out along EA's chamfered corners, clasping the shaft to z ~60 and standing free
  above it past the crown's flared corners; a deep fin a face, silver edges, ember slits, a collar;
  the White Hand in a pointed-arch slot on the field (+X) face of the two field blades;
- a beacon between EA's four inner horns: a faceted iron fire-pot on the crown's low pyramid, its
  fire and smoke the tower's chimney fire; four braziers on the crown's floor between the horns:
  the crown lit from within (fire_points: a 'chimney' and four 'brazier'). Pass 4 (2026-09-30):
  the needle stack out of the crown (to z 166) went; the beacon took its fire;
- EA's pointed windows glow: ember panels in the upper two window rows on every face (the +X
  face's middle one sits behind the banner);
- a heavy banner on the field face (+X) between the bands, the White Hand on it, the cloth in
  the player's colour;
- the wall stub takes the walls' profile (shapes_walls.stub): short knife fins, a buttress blade,
  ember slits, the silver lip and ridge, spikes, needles out of its three pyramids.

EA's facts (IBFITOWER mesh coordinates, identity bone; x -32.67..16.26, y +-15.57, z 0..130.48):
the shaft centred on (0.75, 0), faces square to the axes (7.2 out at z 85, 9.0 at 60), corners
chamfered (8.7 out at z 90); the crown flares from z 98 (9.4 at its corners) to 110 (12.8).
Windows (sill, shoulder, apex; the recess's distance from the axis at the sill; its lean in):
58.9, 66.5, 68.8, 8.5 (8.35 on the x faces), 0.079 per unit; 82.6, 90.1, 91.8, 6.8 (6.65),
0.067; each 3.3 wide. The crown's floor is at z 111.4..112.3 round a low pyramid (114.8) on
the axis; four inner horns rise from it about 6 out on the diagonals to z 130.5. The stub is the walls' profile along x from -32.67 into the shaft at -9.4
(EA's fins at -32.67 and -21.15, pyramids at -30.7, -23.0, -15.2).
"""
from sagekit.building import Building

from ..style import IsengardStyle

C = (0.75, 0.0)
WINDOWS = [(58.9, 66.5, 68.8, (8.5, 8.35), 0.079), (82.6, 90.1, 91.8, (6.8, 6.65), 0.067)]
BLADE = (5.2, 4.0, 0.0, 121.0, 1.06)                # half length (along the diagonal), half width, z0, z1, flare
BLADE_R = 13.6                                       # the four corner blades' centres from the axis, on the diagonals
HAND = (67.0, 3.0, 11.0, 0.025)                      # z0, width, height, the face's lean back per unit up
BEACON = (3.6, 3.4)                                  # the crown's fire-pot on the pyramid (z 114.8): radius, height
CROWN_BRAZIERS = [(C[0] + dx, C[1] + dy, 111.4) for dx, dy in ((6.4, 0), (-6.4, 0), (0, 6.4), (0, -6.4))]
BANNER = (78.0, 5.6, 17.0, 2.0, 7.6)                 # z_top, width, length, d out, the face's distance at z_top
STUB = dict(x0=-32.67, x1=-9.4, fins=(-27.0, -15.3), butt=-21.15, slit_u=(-29.8, -24.2, -18.0),
            pyramids=((-30.7, 57.5), (-23.0, 64.0), (-15.2, 57.5)), spikes_to=-13.0)


def _blades():
    """[(centre, axis degrees)] of the four corner blades."""
    import math
    out = []
    for deg in (45, 135, 225, 315):
        a = math.radians(deg)
        out.append(((round(C[0] + BLADE_R * math.cos(a), 3), round(C[1] + BLADE_R * math.sin(a), 3)), deg))
    return out


def _fire_points():
    """The crown's beacon (a chimney: fire and smoke out of the fire-pot) and the four crown
    braziers' embers (kit.brazier: h + 0.1 over the foot); host side, without mathutils."""
    return [(round(C[0], 1), round(C[1], 1), round(113.6 + BEACON[1] - 0.6, 1), "chimney")] + \
        [(round(x, 1), round(y, 1), round(z + 2.5, 1), "brazier") for x, y, z in CROWN_BRAZIERS]


class Tower(Building):
    style = IsengardStyle()
    source = "IBFITower"
    target = "IBFITOWER"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresQ.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCTower"
    # The fire reduction (Max, 2026-10-05, docs/ART.md "Fire budget": a building whose fire is not its identity,
    # at most 6 live particles): the crown's fire-pot a brazier. 6.0 live (was 37.0).
    fire_points = [(0.8, 0.0, 116.4, 'brazier')]
    views = {
        "rts": ((-8.2, -0.0, 80.0), 350, 50, -38, 50),
        "close": ((-8.2, -0.0, 85.0), 250, 24, -30, 45),
        "top": ((0.8, 0.0, 128.0), 110, 25, -38, 45),
        "field": ((10.0, 0.0, 40.0), 150, 12, 0, 45),
        "ingame": ((-8.2, -0.0, 65.2), 714, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V

        from ..shapes_walls import stub
        out = stub(kit, **STUB)
        for c, deg in _blades():
            out += kit.blade_tower(c, deg, BLADE[0], BLADE[1], BLADE[2], BLADE[3], flare=BLADE[4], fins=1, spurs=False,
                                   slits=(0.36,), collar=0.66, slit_w=1.2)
        out += self._hands(kit)
        from ..shapes_addons import cauldron
        r, h = BEACON                                   # the crown's beacon on EA's low pyramid
        out += cauldron(kit, (C[0], C[1], 113.6), r, h, k=8, spikes=True, legs=False)
        for p in CROWN_BRAZIERS:
            out += kit.brazier(p, 1.1, 2.4)
        out += self._windows(kit)
        z_top, w, length, dd, face = BANNER
        out += kit.banner(V((C[0] + face, C[1], 0)), V((0, 1, 0)), V((1, 0, 0)), 0.0, z_top, w, length, d=dd)
        return out

    @staticmethod
    def _hands(kit):
        """The White Hand in a pointed-arch slot on the field face (+X) of each field blade, z 67..78,
        leaning back with the blade's taper."""
        import math

        from mathutils import Vector as V

        from ..shapes_addons import hand_arch
        from ..shapes_spire import PROFILE, scale
        L, W, z0, z1, flare = BLADE
        z = HAND[0] + HAND[2] / 2
        s = scale((z - z0) / (z1 - z0), PROFILE)
        out = []
        for c, deg in _blades():
            if deg not in (45, 315):
                continue
            a = math.radians(deg)
            d, p = V((math.cos(a), math.sin(a), 0)), V((-math.sin(a), math.cos(a), 0))
            side = -1 if deg == 45 else 1                  # the across vertex on the +X side
            outer, across = V((c[0], c[1], 0)) + d * L * s, V((c[0], c[1], 0)) + p * (side * W * s)
            m = (outer + across) / 2
            t = (across - outer).normalized()
            n = V((t.y, -t.x, 0))
            if n.dot(m - V((c[0], c[1], 0))) < 0:
                n = -n
            out += hand_arch(kit, m + V((0, 0, 0)), t, n, 0.0, HAND[0], HAND[1], HAND[2], d0=-0.5, d1=0.6, bat=HAND[3])
        return out

    @staticmethod
    def _windows(kit):
        """Ember panels in EA's pointed windows, leaning back with the recess."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import loft
        out = []
        m, hw = 0.35, 1.65
        for sill, shoulder, apex, (dy, dx), lean in WINDOWS:
            poly = [(-hw + m, sill + m), (hw - m, sill + m), (hw - m, shoulder), (0.0, apex - 0.5), (-hw + m, shoulder)]
            for n, dist in (((1, 0), dx), ((-1, 0), dx), ((0, 1), dy), ((0, -1), dy)):
                if n == (1, 0) and sill < 70:
                    continue                                  # behind the banner
                nv = V((n[0], n[1], 0))
                a = V((C[0], C[1], 0)) + nv * dist
                t = V((-nv.y, nv.x, 0))
                rings = [[a + t * u + nv * (d - lean * (z - sill)) + V((0, 0, z)) for u, z in poly] for d in (-0.4, 0.12)]
                out.append(loft(rings, ["ember"], cap0=("ember", True), cap1=("ember", True)))
        return out

    def emphasis(self, c, n):
        if c.z > 50:
            return 1.3                        # the shaft's upper half, the crown and the fires
        return 1.0
