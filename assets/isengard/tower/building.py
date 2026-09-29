"""Isengard tower (IsengardTowerExpansion; model IBFITower): the citadel's tower expansion, a small
Orthanc - a square shaft tapering in bands to a flared crown of flanges and horns (z 130.5), its
faces set with pointed windows, knife fins round its foot, a wall stub toward the citadel (-X).
EA's body is Isengard already and stays whole; it gets fire, embers and the walls' profile:

- four braziers on iron brackets out of the shaft's corners under the crown (z 88), the crown
  lit from below: the building's real fire (four 'brazier' points);
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
0.067; each 3.3 wide. The stub is the walls' profile along x from -32.67 into the shaft at -9.4
(EA's fins at -32.67 and -21.15, pyramids at -30.7, -23.0, -15.2).
"""
from sagekit.building import Building

from ..style import IsengardStyle

C = (0.75, 0.0)
WINDOWS = [(58.9, 66.5, 68.8, (8.5, 8.35), 0.079), (82.6, 90.1, 91.8, (6.8, 6.65), 0.067)]
BRAZIER_Z, BRAZIER_AT, REACH = 87.0, 8.4, 3.8        # height, the corner's distance from the axis, bracket reach
BANNER = (78.0, 5.6, 17.0, 2.0, 7.6)                 # z_top, width, length, d out, the face's distance at z_top
STUB = dict(x0=-32.67, x1=-9.4, fins=(-27.0, -15.3), butt=-21.15, slit_u=(-29.8, -24.2, -18.0),
            pyramids=((-30.7, 57.5), (-23.0, 64.0), (-15.2, 57.5)), spikes_to=-12.0)


def _corners():
    """[(face point at BRAZIER_Z, outward direction)] on the shaft's four corners."""
    import math
    out = []
    for i in range(4):
        a = math.pi / 4 + math.pi / 2 * i
        d = (math.cos(a), math.sin(a))
        out.append(((C[0] + d[0] * BRAZIER_AT, C[1] + d[1] * BRAZIER_AT, BRAZIER_Z), d))
    return out


def _fire_points():
    """Where each bracket brazier's fire rises (shapes_walls.bracket_brazier: the basket's rim
    centre REACH out, 0.9 up, and 0.35 over it); host side, without mathutils."""
    return [(round(a[0] + d[0] * REACH, 1), round(a[1] + d[1] * REACH, 1), round(a[2] + 1.25, 1), "brazier")
            for a, d in _corners()]


class Tower(Building):
    style = IsengardStyle()
    source = "IBFITower"
    target = "IBFITOWER"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresQ.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCTower"
    fire_points = _fire_points()
    views = {
        "rts": ((-8.2, -0.0, 65.2), 314, 50, -38, 50),
        "close": ((-8.2, -0.0, 65.2), 186, 24, -30, 45),
        "top": ((0.8, 0.0, 88.0), 85, 25, -38, 45),
        "ingame": ((-8.2, -0.0, 65.2), 714, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V

        from ..shapes_walls import bracket_brazier, stub
        out = stub(kit, **STUB)
        for a, d in _corners():
            out += bracket_brazier(kit, a, d, REACH)
        out += self._windows(kit)
        z_top, w, length, dd, face = BANNER
        out += kit.banner(V((C[0] + face, C[1], 0)), V((0, 1, 0)), V((1, 0, 0)), 0.0, z_top, w, length, d=dd)
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
