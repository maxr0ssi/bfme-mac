"""The Gondor farm (GondorFarm, ArnorFarm; model GBFarm_SKN, drawn by FarmInterface's Draw in
farminterface.ini): EA's farmhouse kept whole - the stone cottage with its porch, flower boxes,
windows and the thatched awning on the east - and dressed as a house of the Pelennor:

    quoins      long and short dressed corner stones up the cottage's four corners, and a
                battered plinth round its walls (not under the porch and flower beds)
    windows     a pediment on consoles over the west and east windows, a label moulding with
                drops over the south and north gable windows
    porch       before the west door: two columns, an architrave on side beams, a slated
                pediment with the White Tree on sable, raking cornices and a gilt knob
    kneelers    moulded blocks with weathered tops on the gable walls' corners, under the eaves
    roundel     the White Tree in a steel ring on the south gable over its window
    dovecote    a squat round dovecote by the field: a plinth, a stone drum, a landing ledge
                under a band of flight holes, a steel-banded cornice, a slate cone, a little
                open lantern, a gilt orb and a steel spike
    banner      one house-colour banner on the south gable (the RTS camera's side)

The crops (skinned, x -40.4..-2.6, |y| <= 29.6), the peasant and his hoe (x -27.2..-18.9) and
the field stay clear; nothing rises into EA's thatched roof (V2HIDE: its ridge runs north-south, its
eaves at z 19.72 at x 4.54 and 37.05 rise 1:1, so the west and east walls show to about 23; the
gables over the south and north walls start at 25.21, 1.7 out) or level 3's storey (V2, from
z 25.21 over the cottage's walls), and the
dovecote keeps inside level 2's yard wall (V1, its inner face at |y| 32.1).

EA's GBFARM (mesh = model coordinates): the cottage's walls are single planes, x 8.25 (west,
the door and porch at |y| < 4.2, flower beds at x 6.08..8.32, |y| 5.5..18.3) and 34.22 (east),
y +-18.68, from z 0.31 to 25.26; windows (N_WINDOW): west |y| 8.3..14.5 (z 7.0..15.9), south and
north x 18.15..25.0 (z 6.9..17.6, EA's frames to x 16.9..26.2), east y -11.43..-7.88 (z
12.7..16.1). The awning over the east side at y 0.7..17.9. Height limit +20 %: z 30.64."""
from sagekit.building import Building

from ..style import MenStyle
from ..prodkit import banner

X0, X1, YH = 8.25, 34.22, 18.68
QUOIN_TOP = 21.4                        # under the eaves (the roof is at z 22.35 over the quoins' fronts)
WEST_WINDOWS = (10.7, -12.08)           # y centres, half 2.4, head 15.9
EAST_WINDOW = (-9.66, 1.78, 16.06)      # y centre, half, head
DOVECOTE = (2.3, -25.6)                 # between the field (x < -2.6) and the cottage (x > 8.25), inside V1 (|y| < 30.8)
ROUNDEL = (21.4, 22.7, 2.05)            # x, z, radius on the south gable (over the window's frame, 19.5)
BANNER = (12.4, 22.5, 3.0, 10.8)        # x, z top, width, length (south gable)


class Farm(Building):
    style = MenStyle()
    source = "GBFarm_SKN"
    target = "GBFARM"
    sheet = "GBFarm.tga"
    sheet_normal = "GBFarm_NRM.tga"
    own_textures = {"GBFarm.tga": "GBFarH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    bake_hidden = ("V1", "V2", "N_WINDOW")          # level 1: the level-up meshes are their own recipes
    views = {
        "rts": ((-1.1, 0.1, 11.8), 262, 50, -38, 50),
        "close": ((20.0, -8.0, 12.0), 120, 24, -40, 45),
        "west": ((10.0, 0.0, 12.0), 90, 18, 180, 45),
        "ingame": ((-1.1, 0.1, 11.8), 595, 53, -62, 50),
    }

    def decals(self):
        from ..prodkit import props_layer
        return [props_layer(sat=(0.12, 0.22), gate=(0.4, 0.65), hue=(22.0, 50.0), rects=[(0.16, 0.22, 0.42, 0.46), (0.0, 0.455, 0.27, 0.5)])]          # EA's thatch (the awning, the shed) and timber stay straw and wood

    def design(self, kit):
        from .. import motifs as M
        out = []
        faces = {"W": M.face((X0, 0.0), (-1, 0)), "E": M.face((X1, 0.0), (1, 0)),
                 "S": M.face(((X0 + X1) / 2, -YH), (0, -1)), "N": M.face(((X0 + X1) / 2, YH), (0, 1))}
        for key, (a, t, n) in faces.items():
            half = YH if key in "WE" else (X1 - X0) / 2
            for side in (-1, 1):
                out += M.quoins(a, t, n, side * half, 0.9, QUOIN_TOP, side=side, long=2.2, short=1.3, h=1.55, d=0.35)
            if key != "W":
                out += M.plinth(a, t, n, -half, half, 0.3, h=2.0, out=0.8)
        a, t, n = faces["W"]
        for y in WEST_WINDOWS:
            out += M.window_pediment(a, t, n, y * t.y, 2.9, 16.35, rise=1.5, d=0.9)
        a, t, n = faces["E"]
        y, half, head = EAST_WINDOW
        out += M.window_pediment(a, t, n, y * t.y, half + 0.8, head + 0.4, rise=1.3, d=0.8)
        a, t, n = faces["S"]                       # the south gable, under the thatch's overhang
        rx, rz, rr = ROUNDEL
        out += M.roundel(kit, a, t, n, (rx - a.x) * t.x, rz, rr, d=0.25)
        bx, z_top, w, L = BANNER
        out += banner(kit, a, t, n, (bx - a.x) * t.x, z_top, w, L, d=0.7)
        for key in "SN":
            a, t, n = faces[key]
            out += self._hood(a, t, n)
            out += self._kneelers(a, t, n)
        out += self._porch(kit, *faces["W"])
        out = M.closed(out)                   # EA's walls are single planes: no buried backs
        out += self._dovecote(*DOVECOTE)
        return out

    @staticmethod
    def _hood(a, t, n):
        """A label moulding over the gable window (above EA's frame, which stands 1.04 proud to
        z 19.53), with short drops at its ends."""
        from .. import motifs as M
        u0, u1 = sorted(((16.35 - a.x) * t.x, (26.75 - a.x) * t.x))
        out = [M.slab(a, t, n, u0 - 0.3, u1 + 0.3, 19.65, 20.35, -0.3, 1.35, front="course")]
        for u in (u0, u1):
            out.append(M.slab(a, t, n, u - 0.35, u + 0.35, 18.2, 19.65, -0.3, 1.2, ("stoneB", "stoneB", None, "stoneB"), "course"))
        return out

    @staticmethod
    def _kneelers(a, t, n):
        """A kneeler on each corner of a gable wall over the quoins: a moulded block and a
        weathered top rising inward under the thatch's eaves."""
        from sagekit.blender.geometry import prism_uz
        from .. import motifs as M
        half = (X1 - X0) / 2
        out = []
        for e in (-1, 1):
            uc = e * half
            ui = uc - e * 2.5
            u0, u1 = sorted((uc, ui))
            out.append(M.slab(a, t, n, u0, u1, QUOIN_TOP, QUOIN_TOP + 1.0, -0.3, 0.95, front="course"))
            out.append(prism_uz(a, t, n, sorted([(uc, QUOIN_TOP + 1.0), (ui, QUOIN_TOP + 1.0), (ui, QUOIN_TOP + 1.85)]),
                                -0.3, 0.8, ["stoneB", "top", "stoneB"], "stoneB", None))
        return out

    @staticmethod
    def _porch(kit, a, t, n):
        """A porch before the west door (EA's hood over it, x 6.74..8.25, stays behind): two
        columns, an architrave on side beams back to the wall, a slated pediment with the White
        Tree on sable, raking cornices and a gilt knob."""
        from sagekit.blender.geometry import prism_uz
        from .. import motifs as M
        from ..shapes import turned
        out = []
        for e in (-1, 1):
            c = a + t * (e * 4.3) + n * 4.35
            out.append(turned(c.x, c.y, [(0.8, 0.3), (0.8, 1.2), (0.5, 1.5), (0.5, 13.4), (0.8, 13.8), (0.8, 14.3)],
                              ["stoneB", "course", "stoneA", "course", "course"], k=8, cap0=("stoneB", True), cap1=("top", True)))
            out.append(M.slab(a, t, n, e * 4.3 - 0.45, e * 4.3 + 0.45, 14.3, 15.4, -0.3, 3.3, front="course", back="stoneB"))
        out.append(M.slab(a, t, n, -5.0, 5.0, 14.3, 15.4, 3.3, 4.7, front="course", back="stoneB"))
        zp, apex, w = 15.4, 19.6, 5.2
        out.append(prism_uz(a, t, n, [(-w, zp), (w, zp), (0, apex)], 1.8, 4.5, ["stoneB", "slate", "slate"], "enamel", "stoneB"))
        for e in (-1, 1):
            poly = [(0, apex), (e * w, zp), (e * (w + 0.8), zp), (0, apex + 0.9)]
            if e < 0:
                poly.reverse()
            out.append(prism_uz(a, t, n, poly, 4.3, 4.95, ["stoneB", "stoneB", "top", "stoneB"], "course", "stoneB"))
        out += kit.white_tree(a, t, n, 0.0, zp + 0.4, 3.0, 4.55, r=0.1)
        c = a + n * 4.6
        out.append(turned(c.x, c.y, [(0.2, apex + 0.8), (0.5, apex + 1.2), (0.5, apex + 1.7), (0.15, apex + 2.1)], ["gilt"] * 3, k=6,
                          cap0=("gilt", True), cap1=("gilt", True)))
        return out

    @staticmethod
    def _dovecote(cx, cy):
        """A squat round dovecote: a plinth, a stone drum, a landing ledge under a band of flight
        holes, a steel-banded cornice, a slate cone, a little open lantern, a gilt orb and a
        steel spike."""
        from ..shapes import beam, turned
        k = 12
        holes = ["slit" if i % 2 == 0 else "stoneA" for i in range(k)]
        out = [turned(cx, cy, [(4.6, 0.0), (4.6, 1.2), (4.1, 1.5), (4.1, 9.6), (4.75, 9.9), (4.75, 10.3), (4.15, 10.4),
                               (4.15, 12.3), (4.6, 12.5), (4.6, 13.1)],
                      ["course", "stoneB", "stoneA", "course", "course", "stoneB", holes, "trim", "trim"], k=k,
                      cap0=("stoneB", False), cap1=("top", True)),
               turned(cx, cy, [(5.0, 13.05), (1.3, 18.5)], ["slate"], k=k, cap0=("slate", True), cap1=("top", True)),
               turned(cx, cy, [(1.1, 18.4), (1.1, 19.9)], ["arcade|a"], k=8, cap0=("stoneB", False), cap1=("top", False)),
               turned(cx, cy, [(1.55, 19.85), (0.0, 21.8)], ["slate"], k=8, cap0=("slate", True), cap1=("slate", False)),
               beam((cx, cy, 21.0), (cx, cy, 26.0), 0.16, "trim", 0.0),
               turned(cx, cy, [(0.18, 22.2), (0.5, 22.65), (0.5, 23.2), (0.16, 23.6)], ["gilt"] * 3, k=6,
                      cap0=("gilt", True), cap1=("gilt", True))]
        return out

    def emphasis(self, c, n):
        return 1.25 if c.z > 12 else 1.0
