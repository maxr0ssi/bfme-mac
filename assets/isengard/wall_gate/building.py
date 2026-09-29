"""Isengard wall gate (IsengardCastleWallGate; model IBWallGateN_SKN): EA's two gate pylons kept
whole - wedge blocks across the wall with chamfered ends, each crowned by a thin fork plate whose
horns reach z 76.85 over both faces - and the two spiked door leaves between them untouched. Each
pylon becomes a trident:

- a blade tower out of the pylon's top between the fork's horns (shapes_spire: a lozenge along
  the pylon, flared foot, two set-back steps, three layered fins a face, silver edges front and
  back, ember slits, a collar) to a needle at z 90 (+17 %);
- silver along the horns' outer edges;
- on each field face (the pylon's x ends): a fire basket on an iron bracket beside the gateway
  (four braziers, the gate's real fire), pointed ember slits low on the face, iron spikes along
  the top edge;
- one heavy banner a face (the +y pylon's +x end, the -y pylon's -x end), the White Hand on it,
  the cloth in the player's colour: the wall run's banners hang here;
- the White Hand in a pointed-arch slot on each pylon end without a banner (z 22..42).

EA's facts (IBGATE mesh coordinates, identity bone; x +-25.09, y +-59.19, z 0..76.85; mirror
symmetric in x and y): the pylons span |y| 48.26..59.19, their cores |y| 50.48..57.03 with ends
at |x| 19.7 at the ground leaning to 15.1 at the flat top (z 55.6), chamfered to |x| 13.4 / 10.3
at their faces |y| 48.26 and 59.19; the fork plate |y| 52.92..54.49 from z 41.4 (outer edge
|x| 16.05 -> 16.99 at 51.65 -> 19.0 at 56.55 -> 22.87 at 59.7 -> the horn's point 25.09 at 76.85).
Kept clear: the door leaves (x -10.3..10.3, |y| < 48.23, to z 47.1) fall outward about their feet
to lie at |x| <= 45.1 when open (IBWallGateN_OPN, 101 frames): nothing new enters |y| < 48.3.
The wall segments meet the pylons' outer faces (|y| 59.19).
"""
from sagekit.building import Building

from ..style import IsengardStyle

PYLON_Y, CORE = 53.7, (50.48, 57.03)
END_X0, END_LEAN, TOP_Z = 19.7, 4.6 / 55.6, 55.6        # the pylon ends' face: x = END_X0 - END_LEAN * z
TOWER = (9.0, 3.0, 55.0, 90.0, 1.12)                    # half length (x), half width (y), z0, z1, flare
HORN = [(19.0, 56.55), (22.87, 59.7), (25.09, 76.85)]   # the fork plate's outer edge, up to the horn's point
BRAZIER = (50.5, 50.9, 3.4)                             # bracket height, |y|, reach
BANNER = (46.0, 4.0, 18.0, 2.6, 55.2)                   # z_top, width, length, d out, |y| centre
HAND = (22.0, 4.6, 20.0)                                # the Hand's arch slot on the other end: z0, width, height


def end_x(z):
    return END_X0 - END_LEAN * z


def _brackets():
    """[(face point, out)] for the four braziers: each pylon end, on the gateway's side."""
    z, y, _ = BRAZIER
    return [((sx * end_x(z), sy * y, z), (sx, 0.0)) for sy in (1, -1) for sx in (1, -1)]


def _fire_points():
    reach = BRAZIER[2]
    return [(round(a[0] + d[0] * reach, 1), round(a[1], 1), round(a[2] + 1.25, 1), "brazier") for a, d in _brackets()]


class WallGate(Building):
    style = IsengardStyle()
    source = "IBWallGateN_SKN"
    target = "IBGATE"
    sheet = "IBFortress.tga"
    sheet_normal = "IBFortress_NRM.tga"
    own_textures = {"IBFortress.tga": "IBFortresE.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    HOUSE_DRAW = "ModuleTag_Draw_HCWallGate"
    fire_points = _fire_points()
    views = {
        "rts": ((-0.0, -0.0, 38.4), 330, 50, -38, 50),
        "close": ((-0.0, -0.0, 38.4), 195, 24, -30, 45),
        "pylon": ((12.0, 53.7, 55.0), 95, 22, -50, 45),
        "ingame": ((-0.0, -0.0, 38.4), 749, 53, -62, 50),
    }

    def design(self, kit):
        out = []
        for sy in (1, -1):
            out += self._pylon(kit, sy)
        return out

    @staticmethod
    def _pylon(kit, sy):
        from mathutils import Vector as V

        from ..shapes_spire import BROAD
        from ..shapes_walls import bracket_brazier, slit
        L, W, z0, z1, flare = TOWER
        c = (0.0, sy * PYLON_Y)
        out = kit.blade_tower(c, 0.0, L, W, z0, z1, flare=flare, fins=3, spurs=False, slits=(0.36, 0.48), collar=0.62,
                              profile=BROAD, slit_w=0.9)
        for sx in (1, -1):
            pts = [V((sx * (x - 0.3), sy * PYLON_Y, z - 0.2)) for x, z in HORN]
            for p, q in zip(pts, pts[1:]):
                out.append(kit.beam(p, q, 0.26, "trim"))
            n, t = V((sx, 0, 0)), V((0, sx, 0))
            face = V((sx * END_X0, 0, 0))
            for y in (51.3, 55.9):                              # slits low on the end face
                out += slit(kit, face, t, n, sx * sy * y, 7.0, 1.3, 10.0, lean=END_LEAN)
            out += kit.spike_row(V((sx * (end_x(TOP_Z) - 0.4), 0, 0)), V((0, 1, 0)), n, sy * CORE[0] + 0.6 * sy,
                                 sy * 52.6, TOP_Z + 0.3, 3.2, 2, lean=0.5, r=0.4)
            out += kit.spike_row(V((sx * (end_x(TOP_Z) - 0.4), 0, 0)), V((0, 1, 0)), n, sy * 54.8,
                                 sy * (CORE[1] - 0.6), TOP_Z + 0.3, 3.2, 2, lean=0.5, r=0.4)
        for a, d in _brackets():
            if a[1] * sy > 0:
                out += bracket_brazier(kit, a, d, BRAZIER[2])
        from ..shapes_addons import hand_arch
        z0, w, h = HAND                                        # the White Hand on the end without a banner
        sx = -sy
        out += hand_arch(kit, V((sx * end_x(z0), 0, 0)), V((0, sx, 0)), V((sx, 0, 0)), sx * sy * PYLON_Y, z0, w, h,
                         d0=-2.4, d1=0.7, bat=END_LEAN)
        z_top, w, length, dd, yb = BANNER
        sx = sy                                                # +y pylon: +x end; -y pylon: -x end
        n = V((sx, 0, 0))
        out += kit.banner(V((sx * end_x(z_top), 0, 0)), V((0, sx, 0)), n, sy * sx * yb, z_top, w, length, d=dd)
        return out

    def emphasis(self, c, n):
        if c.z > 40:
            return 1.35                       # the tridents, fires and banners
        return 1.0
