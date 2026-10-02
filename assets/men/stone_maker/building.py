"""The Gondor stoneworks (GondorStoneMaker, ArnorStoneMaker; model GBStoneMK_SKN): EA's quarry
tower kept whole - the battered base with its windows, the open crane stage between four
diagonal corner piers, the top storey with the timber crane turning on it, the treadwheel annex,
the stone pile and the guild flag - and dressed in the citadel's stone and steel:

    arches      a pointed archivolt of wedge stones and a raised keystone round each of the
                stage's four openings (EA's crane gear turns inside them untouched)
    cornice     a corbelled cornice under the top storey's rim with a sable band of gilt stars,
                kept under the crane's turning platform (z 75.8) and clear of the flag's bracket
    frieze      a sable band with gilt stars on the parapet course at the stage's foot
    windows     a pediment on consoles over each of the base's three windows
    plinth      a battered plinth round the base, battered buttresses with weathered tops either
                side of each window, sills on corbels
    fins        long-and-short quoins up the four corner fins' end faces and a moulded cap where
                they step in (z 57.6): the fins read as dressed pilasters
    band        a machicolation at the base's top (corbels, a sable slab with gilt stars)
    yard        a low wall with a moulded coping and pyramid-capped posts along the stone
                yard's east edge (outside the hooks' and the stones' reach)
    annex       square merlons along the treadwheel annex's east edge (the rope and the porter
                keep the rest)
    banner      one house-colour banner on the top storey's south face (the RTS camera's side)

Nothing new rises above the tower's rim: the crane turns a platform of radius about 17.5 round
its shaft at (28.3, -32.0) from z 75.8, its arm sweeps the north-west at 78.5 and above, and the
hooks, pulleys and rope hang over the stone pile (GBStoneMK_IDLA swept over all 310 frames).

EA's GBSTONEMK (mesh = model coordinates): the base's faces at y -47.4 (south), x 13.05 (west),
x 44.02 (east) to the setback (28..37) and the parapet course (37..40, faces y -43.6 / -19.65,
x 16.5 / 40.2, the stage's planes); the openings: south and north centred x 28.2, half 5.3,
springing 54.5, apex 57.9; east and west centred y -33.0, half 4.0, springing 54.0, apex 58.5;
the lintel 58..61; the top storey's faces y -42.9 / -20.5, x 17.6 / 39.2, to its rim at 75.66;
the flag's bracket on the east face at y -34.2..-31.6, z 65.8..72.4. Windows (panes 0.85 in,
frames 0.8 proud): south x 27.75 (half 3.0), west y -32.0 (2.7), east y -32.8 (2.85), sills 11.4,
heads 20.2. The annex x 13.8..43.05, y -19.9..-1.75, top 32."""
from sagekit.building import Building

from ..style import MenStyle
from ..prodkit import banner, pointed_voussoirs

CX, CY = 28.3, -31.7
STAGE = {"S": ((28.2, -43.6), (0, -1), 5.3, 54.5, 3.4), "N": ((28.2, -19.65), (0, 1), 5.3, 54.5, 3.4),
         "W": ((16.5, -33.0), (-1, 0), 4.0, 54.0, 4.5), "E": ((40.2, -33.0), (1, 0), 4.0, 54.0, 4.5)}
TOP = {"S": ((28.3, -42.9), (0, -1)), "N": ((28.3, -20.5), (0, 1)), "W": ((17.6, -31.7), (-1, 0)), "E": ((39.2, -31.7), (1, 0))}
TOP_HALF = 7.4                          # the top storey's faces between the corner piers
BASE = {"S": ((28.3, -47.4), (0, -1), 7.6), "W": ((13.05, -31.7), (-1, 0), 7.4), "E": ((44.02, -31.7), (1, 0), 7.4)}
WINDOWS = {"S": (27.75 - 28.3, 3.0), "W": (-(-32.0 + 31.7), 2.7), "E": (-32.8 + 31.7, 2.85)}
FINS = (28.45, -31.4, 20.5, 1.85, (38.4, 57.6))   # the corner fins' end faces: centre, radius along the diagonals, half, z
BAND = (24.2, 26.4, 28.2)               # the base's machicolation: corbel foot, slab foot, slab top
BUTTRESS = 6.3                          # buttresses either side of each base window (u)
YARD = (47.7, (-1.0, 44.0), 9.0)        # the yard wall's middle line x, its y run, post pitch
FLAG_U = -34.2 + 31.7, -31.6 + 31.7     # the flag bracket on the east face, in u (t = (0, 1))


class StoneMaker(Building):
    style = MenStyle()
    source = "GBStoneMK_SKN"
    target = "GBSTONEMK"
    sheet = "GBstoneMk1.tga"
    sheet_normal = None
    own_textures = {"GBstoneMk1.tga": "GBstoneMkH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    # EA's damaged, really damaged and rubble bodies are new meshes (GBSTONEMK_NEW and its pieces) painted
    # from GBstoneMk1D with a normal map; our sheet has none, and the tool cannot put a body without one
    # into EA's normal-mapped state meshes, so those states stay EA's
    _why = "EA's state bodies are normal-mapped new meshes; our sheet has no normal map"
    lifecycle = {"GBStoneMK_D1": {"skip": _why}, "GBStoneMK_D2": {"skip": _why}, "GBStoneMK_D3": {"skip": _why}}
    footprint_margin = 0.8              # the south buttresses' feet stand 0.72 past EA's fins (collision is the INI's)
    views = {
        "rts": ((17.6, -0.1, 38.7), 319, 50, -38, 50),
        "close": ((28.3, -32.0, 45.0), 170, 18, -45, 45),
        "stage": ((28.3, -32.0, 60.0), 90, 12, -60, 45),
        "ingame": ((17.6, -0.1, 38.7), 724, 53, -62, 50),
    }

    def decals(self):
        from ..prodkit import props_layer
        return [props_layer(sat=(0.18, 0.3), gate=(0.3, 0.55))]     # EA's planks and the guild flag keep their colours

    def design(self, kit):
        from .. import motifs as M
        out = []
        for key, (p, nrm, half, spring, rise) in STAGE.items():
            a, t, n = M.face(p, nrm)
            out += pointed_voussoirs(a, t, n, 0.0, half + 0.25, spring, rise + 0.2, 1.3, -0.4, 0.7, count=4)
            for e in (-1, 1):                           # colonnettes up the jambs
                u = e * (half + 0.85)
                out.append(M.slab(a, t, n, u - 0.5, u + 0.5, 40.2, spring, -0.3, 0.55, ("stoneB", "stoneB", None, "stoneB"), "stoneA"))
                out.append(M.slab(a, t, n, u - 0.7, u + 0.7, spring - 0.8, spring, -0.3, 0.8, front="course"))
            if key != "N":                              # the annex's ledge meets the north face there
                w = 9.0 if key == "S" else 8.0
                out += M.star_frieze(kit, a, t, n, -w, w, 37.3, h=2.3, d0=-0.3, d1=0.35, count=5)
        out += self._cornice(kit)
        out += self._base()
        out += self._band(kit)
        out += self._fins()
        out += self._yard(kit)
        out += self._annex(kit)
        a, t, n = M.face(*TOP["S"])
        out += banner(kit, a, t, n, 0.0, 70.0, 4.6, 9.0, d=0.8)
        return M.closed(out)                # the tower is hollow and open at its stage: no buried backs

    @staticmethod
    def _cornice(kit):
        """Corbels (70.5..73.6) and a sable band of gilt stars (73.6..75.2) under the top storey's
        rim, 1.3 out; on the east face the corbels skip the flag's bracket."""
        from .. import motifs as M
        out = []
        for key, (p, nrm) in TOP.items():
            a, t, n = M.face(p, nrm)
            h = TOP_HALF
            k = 5
            for i in range(k):
                u = -h + 0.8 + i * (2 * h - 1.6) / (k - 1)
                if key == "E" and FLAG_U[0] - 0.9 < u < FLAG_U[1] + 0.9:
                    continue
                out += kit.corbel(a, t, n, u, 70.5, w=0.5, z1=72.0, z2=73.6, d1=0.6, d2=1.2)
            out.append(M.slab(a, t, n, -h, h, 73.6, 75.2, -0.4, 1.3, ("stoneB", "stoneB", "top", "stoneB"), "enamel"))
            for i in range(4):
                out += kit.star(a, t, n, -h + (i + 0.5) * (2 * h) / 4, 74.4, 0.62, 1.2, 1.55)
        return out

    @staticmethod
    def _base():
        from .. import motifs as M
        out = []
        for key, (p, nrm, half) in BASE.items():
            a, t, n = M.face(p, nrm)
            u, wh = WINDOWS[key]
            out += M.window_pediment(a, t, n, u, wh + 1.1, 20.9, rise=2.1, d=1.0)
            out += M.plinth(a, t, n, -half, half, 1.4, h=2.2, out=0.85)
            s = wh + 0.9                        # a sill on two corbels
            out.append(M.slab(a, t, n, u - s, u + s, 10.7, 11.35, -0.3, 1.0, front="course"))
            for e in (-1, 1):
                out.append(M.slab(a, t, n, u + e * (wh - 0.3) - 0.4, u + e * (wh - 0.3) + 0.4, 9.4, 10.7, -0.3, 0.75,
                                  ("stoneB", "stoneB", None, "stoneB"), "stoneB"))
            for e in (-1, 1):                   # battered buttresses with a weathered top
                out += StoneMaker._buttress(a, t, n, e * BUTTRESS + (0.4 if key == "S" else 0.0))
        return out

    @staticmethod
    def _buttress(a, t, n, u, z0=1.4, z1=14.0, out=1.9, top=0.8):
        from sagekit.blender.geometry import prism_uz
        body = prism_uz(a, t, n, [(u - 0.85, z0), (u + 0.85, z0), (u + 0.85, z1), (u - 0.85, z1)], -0.3, out,
                        ["stoneB", "stoneB", "top", "stoneB"], "stoneB", None, bat=(out - top) / (z1 - z0))
        wedge = prism_uz(a, n, t, [(-0.3, z1), (top, z1), (-0.3, z1 + 1.5)], u - 0.95, u + 0.95,
                         [None, "top", "stoneB"], "stoneB", "stoneB")
        return [body, wedge]

    @staticmethod
    def _band(kit):
        """A machicolation at the base's top, under the setback: short corbels, a slab 1.5 out with
        a sable front and gilt stars, on the south, east and west faces."""
        from .. import motifs as M
        zc, zs, zw = BAND
        out = []
        for key, (p, nrm, half) in BASE.items():
            a, t, n = M.face(p, nrm)
            for u in (-6.6, -3.3, 0.0, 3.3, 6.6):
                out += kit.corbel(a, t, n, u, zc, w=0.45, z1=zc + 1.1, z2=zs, d1=0.75, d2=1.4)
            out.append(M.slab(a, t, n, -half - 0.2, half + 0.2, zs, zw, -0.4, 1.5, ("stoneB", "stoneB", "top", "stoneB"), "enamel"))
            for i in range(4):
                out += kit.star(a, t, n, -half + (i + 0.5) * (2 * half) / 4, (zs + zw) / 2, 0.68, 1.4, 1.75)
        return out

    @staticmethod
    def _fins():
        """Quoins up the four corner fins' end faces from the stage's foot, and a moulded cap
        where the fins step in (z 58): the fins read as dressed pilasters."""
        import math

        from .. import motifs as M
        cx, cy, r, h, (z0, z1) = FINS
        out = []
        for sx, sy in ((1, -1), (1, 1), (-1, 1), (-1, -1)):
            k = r / math.sqrt(2)
            a, t, n = M.face((cx + sx * k, cy + sy * k), (sx, sy))
            z, i = z0, 0
            while z + 1.9 <= z1 + 0.01:
                w = h + (0.55 if i % 2 == 0 else 0.1)
                out.append(M.slab(a, t, n, -w, w, z, z + 1.75, -0.3, 0.35, front="stoneB"))
                z, i = z + 1.9, i + 1
            out.append(M.slab(a, t, n, -h - 0.5, h + 0.5, z1, z1 + 0.6, -0.3, 0.8, front="course"))
            out.append(M.slab(a, t, n, -h - 0.7, h + 0.7, z1 + 0.6, z1 + 1.2, -0.3, 1.05, ("stoneB", "stoneB", "top", "stoneB"), "course"))
        return out

    @staticmethod
    def _yard(kit):
        """A low wall with a moulded coping along the stone yard's east edge (outside the hooks'
        and the stones' reach), a square post with a pyramid cap and a steel knob at each end
        and every `pitch`."""
        from .. import motifs as M
        x, (y0, y1), pitch = YARD
        out = []
        k = int(round((y1 - y0) / pitch))
        ys = [y0 + (y1 - y0) * i / k for i in range(k + 1)]
        for ya, yb in zip(ys, ys[1:]):
            out.append(M.box(x - 0.5, x + 0.5, ya, yb, 0.3, 3.2, "stoneA", cap1=("top", False)))
            out.append(M.box(x - 0.75, x + 0.75, ya, yb, 3.2, 3.75, "course", cap0=("stoneB", True), cap1=("top", True)))
        for y in ys:
            out += kit.pinnacle(x, y, 0.3, 4.4, half=0.95, spire=1.9)
        return out

    @staticmethod
    def _annex(kit):
        from .. import motifs as M
        a, t, n = M.face((43.05, -10.8), (1, 0))
        return M.parapet(kit, a, t, n, -8.6, 8.6, 32.0, -1.0, 0.0, h=0.9, merlon=2.2, w=2.0, gap=1.5, cap=0.45)

    def emphasis(self, c, n):
        return 1.3 if c.z > 36 else 1.0
