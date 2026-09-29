"""The boiling-oil works (UPGRADE_BOILING_OIL, Draw ModuleTag_OilDraw of MenFortressCitadel): the
eight outlets on the curtain walls become the citadel's own spout housings, and the hearth on the
back wall walk a stone-kerbed firebox. EA's plates, hearth, trestles and hopper are kept whole.

    outlets  per plate: a moulded sill on a two-step corbel (from the plate's foot), jambs with capitals, a lintel under a
             little gable with a steel boss, and a steel spout mouth at the steam bone, so EA's
             plate reads as the dark slot between the jambs
    hearth   a stone kerb round EA's firebox (a band of iron grating round its outside, steel
             corner bosses), steel straps up both legs of each wooden trestle, a steel bearing on
             each apex, stone feet; a stone rim with steel corner studs round the hopper's grate

EA's GBFBOIL (154 triangles, on its bone at the fortress's origin; mesh = fortress coordinates):
eight plates 0.81 thick (x 48.76..49.57 on the +x wall), 4.93 wide, z 25.96..38.86, centred at
along 21.98 (the gate's wall, |y|) or 23.98 (the others); the steam bones (EA's STEAM_BONE02..09
meshes, kept) at 49.21, z 31.8..33.8 on each plate's middle; the curtain walls' face at 49.01.
The gate's pilasters reach |y| 19.4 and widen to 20.3 above z 40.1: the housings stop at
along 2.45 from the plate's middle. The hearth: EA's firebox x -47.27..-35.21, y -9.2..8.24, top
48.64 (coals to 49.02); the trestles (x -46.31..-35.97, |y| 6.8..7.91, apex (-41.14, 58.93));
the hopper x -36.51..-24.04, |y| <= 6.24 at z 46.75 to its grate x -33.81..-26.73, |y| <= 3.54 at
49.79. The pot (fortress_oil_guy) swings on its axle at (-41.22, 0.4, 56.23): its body within
|y| 5.6, its levers at y 8.37..8.88 sweeping down to about z 49.6, so nothing new stands in
|y| 5.6..9.5 above z 49.2 but inside the trestles' own planes (|y| 6.65..8.05).
"""
from sagekit.building import Building

from ..style import MenStyle

FACE = 49.01
# (outward normal, along axis, plate centres along it)
WALLS = [((1, 0), (0, 1), (-21.975, 21.975)), ((-1, 0), (0, -1), (-23.975, 23.975)),
         ((0, 1), (-1, 0), (-23.975, 23.975)), ((0, -1), (1, 0), (-23.975, 23.975))]
HALF = 2.45                     # the housing's half-width (the gate's pilasters)
STEAM_Z = 32.8
TRESTLE = dict(x=(-46.31, -35.97), apex=(-41.14, 58.93), foot=48.23, y=(6.8, 7.91))
HOPPER = dict(x=(-33.81, -26.73), y=3.54, z=49.79)


class FortressOil(Building):
    style = MenStyle()
    source = "GBFBOil"
    target = "GBFBOIL"
    sheet = "GBFortress1.tga"
    sheet_normal = "GBFortress1_NRM.tga"
    own_textures = {"GBFortress1.tga": "GBFortressJ.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    parts = ("ModuleTag_OilDraw",)
    footprint_margin = 1.0          # the spout housings stand 1.5 out of the wall (0.94 past EA's plates),
                                    # inside the citadel's footprint (its towers reach 52.93)
    tri_budget = 5000
    views = {
        "rts": ((0.0, 0.0, 42.4), 317, 50, -38, 50),
        "close": ((49.0, 22.0, 33.0), 34, 12, -25, 45),
        "hearth": ((-38.0, 0.0, 51.0), 45, 45, 25, 45),
        "ingame": ((0.0, 0.0, 42.4), 720, 53, -62, 50),
    }

    def design(self, kit):
        from mathutils import Vector as V
        out = []
        for (nx, ny), (tx, ty), us in WALLS:
            n, t = V((nx, ny, 0)), V((tx, ty, 0))
            a = n * FACE
            for u in us:
                out += self._outlet(kit, a, t, n, u)
        out += self._hearth(kit)
        return out

    @staticmethod
    def _outlet(kit, a, t, n, u):
        """Every back is closed: the checks cast sky rays at this model alone, without the wall."""
        from sagekit.blender.geometry import prism_uz

        def P(u0, u1, z0, z1, d0, d1, tags, front):
            return prism_uz(a, t, n, [(u + u0, z0), (u + u1, z0), (u + u1, z1), (u + u0, z1)], d0, d1, tags, front, "stoneB")
        H = HALF
        S4 = ["stoneB", "stoneB", "top", "stoneB"]
        out = [P(-0.8, 0.8, 25.96, 26.9, -0.2, 0.75, S4, "stoneA"),                          # corbel, two steps
               P(-0.8, 0.8, 26.9, 27.8, -0.2, 1.3, ["stoneB", "stoneB", None, "stoneB"], "stoneA"),
               P(-H, H, 27.8, 28.9, -0.2, 1.45, S4, "course"),                              # sill
               P(-H + 0.15, H - 0.15, 28.9, 29.15, -0.2, 1.2, S4, "stoneB")]
        for e in (-1, 1):                                                                   # jambs and capitals
            j0, j1 = sorted((e * 1.85, e * H))
            out.append(P(j0, j1, 29.15, 37.6, -0.2, 1.0, [None, "stoneB", None, "stoneB"], "stoneA"))
            out.append(P(j0 - 0.08, j1 + 0.08, 37.6, 38.3, -0.2, 1.2, S4, "course"))
        out.append(P(-H, H, 38.3, 39.8, -0.2, 1.35, S4, "course"))                           # lintel
        out.append(prism_uz(a, t, n, [(u - H + 0.1, 39.8), (u + H - 0.1, 39.8), (u, 41.5)], -0.2, 1.0,
                            [None, "top", "top"], "stoneA", "stoneB"))                      # its gable
        out.append(P(-0.45, 0.45, 40.1, 40.9, 0.9, 1.25, ["trim"] * 4, "trim"))              # steel boss
        # the spout mouth round the steam bone: a steel plate and a short square mouth (dark iron
        # front); the steam rises from the bone at its lips
        out.append(P(-1.25, 1.25, STEAM_Z - 1.6, STEAM_Z + 1.6, 0.3, 0.72, ["trim"] * 4, "trim"))
        out.append(P(-0.65, 0.65, STEAM_Z - 0.75, STEAM_Z + 0.55, 0.6, 1.3, ["trim"] * 4, "iron"))
        return out

    def decals(self):
        """EA's glowing coals keep EA's own colours, the trestles their wood, the plates dark iron."""
        return [_embers_layer()]

    @staticmethod
    def _hearth(kit):
        from sagekit.blender.geometry import box

        from ..shapes import beam
        out = []
        # the kerb round the firebox: low on the levers' side (+y), an iron grating band outside
        for x0, x1, y0, y1, z1 in ((-48.0, -47.05, -9.6, 8.65, 49.4), (-35.45, -34.6, -9.6, 8.65, 49.4),
                                   (-47.2, -35.3, -9.6, -8.95, 49.4), (-47.2, -35.3, 8.0, 8.65, 49.15)):
            out.append(box(x0, x1, y0, y1, 46.7, z1, "course"))
            out.append(box(x0 - 0.06, x1 + 0.06, y0 - 0.06, y1 + 0.06, 47.35, 48.35, "iron", cap0=("iron", True),
                           cap1=("iron", True)))
        for x in (-47.5, -35.05):
            for y in (-9.25, 8.3):
                out.append(box(x - 0.45, x + 0.45, y - 0.45, y + 0.45, 49.0, 49.75 if y < 0 else 49.35, "trim",
                               cap1=("trim", True)))
        # the trestles: steel straps up both faces of both legs, a bearing on the apex, stone feet
        (xa, xb), (ax, az), fz = TRESTLE["x"], TRESTLE["apex"], TRESTLE["foot"]
        for s in (-1, 1):
            for y in (6.72, 7.99):
                for fx in (xa + 0.6, xb - 0.6):
                    out.append(beam((fx, s * y, fz + 1.8), (ax + (0.35 if fx > ax else -0.35), s * y, az - 1.2), 0.2, "trim"))
            y0, y1 = sorted((s * 6.65, s * 8.05))
            out.append(box(ax - 0.9, ax + 0.9, y0, y1, az - 1.3, az + 0.35, "trim", cap0=("trim", True), cap1=("trim", True)))
            for fx in (xa + 0.9, xb - 0.9):
                out.append(box(fx - 1.2, fx + 1.2, y0 + 0.05, y1 - 0.05, 48.6, 50.3, "stoneA", cap1=("top", True)))
                out.append(box(fx - 1.35, fx + 1.35, y0, y1, 50.3, 50.75, "course"))
        # the hopper's grate: a stone rim with steel studs on its corners
        (hx0, hx1), hy, hz = HOPPER["x"], HOPPER["y"], HOPPER["z"]
        for x0, x1, y0, y1 in ((hx0 - 0.5, hx1 + 0.5, -hy - 0.5, -hy + 0.1), (hx0 - 0.5, hx1 + 0.5, hy - 0.1, hy + 0.5),
                               (hx0 - 0.5, hx0 + 0.1, -hy, hy), (hx1 - 0.1, hx1 + 0.5, -hy, hy)):
            out.append(box(x0, x1, y0, y1, hz - 0.6, hz + 0.45, "course"))
        for x in (hx0 - 0.2, hx1 + 0.2):
            for y in (-hy - 0.2, hy + 0.2):
                out.append(box(x - 0.35, x + 0.35, y - 0.35, y + 0.35, hz + 0.45, hz + 0.95, "trim", cap1=("trim", True)))
        return out


def _embers_layer():
    """A paint layer (built on first use: sagekit.paint needs numpy) on EA's own faces: the firebox's
    top (x -47.27..-35.21, y -9.2..8.24, z 48.5..49.2, facing up) shows EA's texels unchanged (the
    glowing coals); the trestles stay wood and the outlet plates dark iron (the stone recolour
    would turn all three to white stone)."""
    import numpy as np

    from sagekit.paint.fields import ramp, smooth
    from sagekit.paint.imageio import to_srgb
    from sagekit.paint.layers import Layer

    class Embers(Layer):
        def apply(self, col, cv, pal):
            P, N = cv.pos, cv.nrm
            x, y, z = P[..., 0], P[..., 1], P[..., 2]
            old = cv.tag_is("old") & (cv.covm > 0.5)
            box = (x > -47.3) & (x < -35.2) & (y > -9.25) & (y < 8.3) & (z > 48.5) & (z < 49.2)
            coals = (box & old).astype(np.float32) * smooth(N[..., 2], 0.4, 0.7)
            wood = (old & (np.abs(y) > 6.7) & (np.abs(y) < 8.0) & (x > -46.4) & (x < -35.9) & (z > 48.3)).astype(np.float32)
            plate = (old & (np.maximum(np.abs(x), np.abs(y)) > 48.7) & (z < 39.0)).astype(np.float32)
            L = np.clip(cv.lum, 0, 1)
            src = to_srgb(cv.load("atlas")).astype(np.float32)
            out = col
            for m, c in ((coals, src), (wood, ramp(np.clip(L * 1.15, 0, 1), pal["wood"])),
                         (plate, ramp(np.clip(L * 1.3 + 0.05, 0, 1), pal["iron"]))):
                out = out * (1 - m[..., None]) + c * m[..., None]
            return out
    return Embers()
