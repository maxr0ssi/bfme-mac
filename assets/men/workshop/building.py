"""The Gondor siege workshop (GondorWorkshop, ArnorWorkshop; model GBWorkshop): EA's gatehouse kept
whole - two square towers with their grilled windows, the corbelled upper storeys and their
arcaded friezes, the moulded arch and the crenellated bridge between them - and dressed as the
citadel's works:

    crowns      a crenellated parapet round each tower top, a pinnacle with a steel orb on
                every corner and a steel mast with a gilt orb in the middle (at level 2 EA's
                slate caps (V1) rise inside the parapets and the mast becomes their finial; at
                level 3 the domed storeys (V2) close over all of it)
    corbels     paired corbels under the upper storeys' overhang at every corner (the window
                pediments and the yard recesses take the middles), a battered plinth
    windows     a little pediment on consoles over each front and outer grilled window
    gate        a voussoir archivolt with a raised keystone round EA's arch on both faces
    crests      over the bridge's middle merlons, front and yard: an entablature with a sable
                frieze and gilt stars, a pediment with the White Tree, a winged-helm crest and
                pinnacles
    banners     two house-colour banners, on the yard faces of the upper storeys (the RTS
                camera's side)

EA's GBWORKSHOP1 (mesh coordinates; the model is the mesh moved by (11.62, -0.16)): the towers'
lower shafts x -49.65..-32.35, |y - 0.155| 17.1..34.37, to the ledge (31.0..33.35); the upper
storeys x -51.02..-30.72 (flaring to -51.73..-30.28 by z 42), out to |y - 0.155| 35.75..36.3,
cornice 45.6..48.3 (to x -52.34..-29.41, |y - 0.155| <= 36.95), a top slab to 51.32 whose top is
x -51.9..-30.05, |y - 0.155| 16.39..36.48. The windows (frames 0.5 proud) at z 9.94..25.73 on the
front (x -49.65, y centre +-26.6, half 4.55) and on the outer faces (x -45.52..-36.35); a tall
recess on the yard faces (|y - 0.155| 20..32, to z 31.5). The arch: |y| < 13.4 to z 22.5, crown
27.8, frame front x -48.93 (yard -32.62); the bridge's walk at 34.08 with merlons (5.4 x 1.9,
2.8 high) at x -48.28..-46.40 and -35.14..-33.25. Level 2's V1 wraps the yard (z <= 21.76, also
in front of the towers), its caps stand on the tower tops (x -51.2..-30.8, |y| 16.7..36.7,
z 51.09..58.70) and blocks on the towers' outer faces (z 16.5..30.9); level 3's V2 storeys
enclose the tower tops (x -54.64..-27.50, |y - 0.155| 12.8..40.2, from z 48.26).
Height limit +20 %: z 61.95 (the mast's spike)."""
from sagekit.building import Building

from ..style import MenStyle
from ..prodkit import banner

YC = 0.155                              # the mirror plane
LOWER = (-49.65, -32.35, 17.1, 34.37)   # lower shafts: x front, x yard, |y| inner, |y| outer
UPPER = (-51.02, -30.72, 35.75)         # upper storeys (at their foot)
TOP = (-51.9, -30.05, 16.39, 36.48, 51.32)      # the top slab's top: x0, x1, |y| in, |y| out, z
WINDOW = (26.6, 4.55, 9.94, 25.73)      # front windows: |y| centre, half, sill, head
ARCH = (13.4, 5.3, 22.5)                # EA's opening (half, rise, spring)
X_FRONT, X_YARD = -48.93, -32.62        # the arch frame's faces
WALK = 34.08
CREST_Y = 7.0                           # the crests enclose the middle merlons (|y| <= 6.53)
BANNER = (45.1, 5.2, 12.2)              # z top (under the cornice), width, length
MAST = 58.7                             # the mast's orb (level 2's cap apex is at 58.70)


def towers():
    return (1, -1)


class Workshop(Building):
    style = MenStyle()
    source = "GBWorkshop"
    target = "GBWORKSHOP1"
    sheet = "GBWorkshop3.tga"
    sheet_normal = "GBWorkshop3_NRM.tga"
    own_textures = {"GBWorkshop3.tga": "GBWorkshopH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    bake_hidden = ("V1", "V2", "N_WINDOW")    # level 1: the level-up meshes are their own recipes
    views = {
        "rts": ((3.3, -0.0, 24.8), 281, 50, -38, 50),
        "close": ((-41.0, 0.0, 30.0), 150, 22, -32, 45),
        "front": ((-41.0, 0.0, 30.0), 150, 16, 150, 45),
        "crown": ((-41.0, -26.0, 46.0), 70, 28, -40, 45),
        "ingame": ((3.3, -0.0, 24.8), 638, 53, -62, 50),
    }

    def variants(self, install):
        from ..prodkit import same_length_variants
        return same_length_variants(self, install, super().variants(install))

    def design(self, kit):
        out = []
        for s in towers():
            out += self._crown(kit, s)
            out += self._corbels(kit, s)
            out += self._windows(s)
            out += self._banner(kit, s)
        for x, sx in ((X_FRONT, -1), (X_YARD, 1)):
            out += self._archivolt(kit, x, sx)
            out += self._crest(kit, sx)
        return out

    # ------------------------------------------------------------------ tower tops
    @staticmethod
    def _crown(kit, s):
        from .. import motifs as M
        x0, x1, yi, yo, z = TOP
        ya, yb = sorted((YC + s * yi, YC + s * yo))
        out = []
        corners = [(x0, ya), (x1, ya), (x1, yb), (x0, yb)]
        # the four edges as faces looking out, each run between its corner pinnacles
        edges = [((x0, (ya + yb) / 2), (-1, 0), yb - ya), ((x1, (ya + yb) / 2), (1, 0), yb - ya),
                 (((x0 + x1) / 2, ya), (0, -1), x1 - x0), (((x0 + x1) / 2, yb), (0, 1), x1 - x0)]
        for p, nrm, L in edges:
            a, t, n = M.face(p, nrm)
            h = L / 2 - 1.3
            out += M.parapet(kit, a, t, n, -h, h, z, -1.0, 0.05, h=1.1, merlon=2.3, w=2.0, gap=1.5, cap=0.5)
        for cx, cy in corners:
            ix, iy = (1.25 if cx == x0 else -1.25), (1.25 if cy == ya else -1.25)
            out += kit.pinnacle(cx + ix, cy + iy, z, z + 3.6, half=1.1, spire=3.6)
        cx, cy = (x0 + x1) / 2, (ya + yb) / 2
        out += M.mast(kit, cx, cy, z, MAST - 0.1, base=1.4)
        return out

    # ------------------------------------------------------------------ corbels and plinth
    @staticmethod
    def _corbels(kit, s):
        """Pairs of corbels under the upper storey's overhang (its foot is 1.4 out of the lower
        shaft) at the corners of the front, outer and yard faces (the window pediments and the
        yard recess take the middles), and a battered plinth round the shaft's feet (not in the
        gate passage)."""
        from .. import motifs as M
        xf, xy, yi, yo = LOWER
        yc_t = YC + s * (yi + yo) / 2           # the tower's centre line
        out = []
        faces = [((xf, yc_t), (-1, 0)), ((xy, yc_t), (1, 0)), (((xf + xy) / 2, YC + s * yo), (0, s))]
        half = (yo - yi) / 2
        for p, nrm in faces:
            a, t, n = M.face(p, nrm)
            for u in (-half + 0.8, -half + 2.5, half - 2.5, half - 0.8):
                out += kit.corbel(a, t, n, u, 27.6, w=0.5, z1=29.25, z2=30.95, d1=0.7, d2=1.35)
            ext = 0.9 if nrm[1] else 0.0
            out += M.plinth(a, t, n, -half - ext, half + ext, 0.0, h=2.2, out=0.9)
        return out

    # ------------------------------------------------------------------ windows
    @staticmethod
    def _windows(s):
        """A pediment on consoles over the front and outer windows."""
        from .. import motifs as M
        yc, half, _, z1 = WINDOW
        xf, xy, _, yo = LOWER
        out = []
        for p, nrm in (((xf, YC + s * yc), (-1, 0)), (((xf + xy) / 2, YC + s * yo), (0, s))):
            a, t, n = M.face(p, nrm)
            out += M.window_pediment(a, t, n, 0.0, half + 0.5, z1 + 0.3, rise=1.9, d=0.95)
        return out

    # ------------------------------------------------------------------ the gate
    @staticmethod
    def _archivolt(kit, x, sx):
        from mathutils import Vector as V
        h, r, z = ARCH
        a, t, n = V((x, YC, 0)), V((0, sx, 0)), V((sx, 0, 0))
        inner, outer = (h + 1.2, r + 1.5, z), (h + 3.3, r + 3.6, z)
        return kit.voussoirs(a, t, n, inner, outer, -0.9, 0.95, count=9, key=(1.2, WALK - 0.2, 0.35))

    @staticmethod
    def _crest(kit, sx):
        """Over the bridge's two middle merlons, on its front (sx -1) or yard (sx 1) edge: an
        entablature enclosing them (a sable frieze with three gilt stars), a pediment with the
        White Tree on a sable tympanum, raking cornices, a winged-helm crest and end pinnacles."""
        from mathutils import Vector as V

        from sagekit.blender.geometry import prism_uz
        from .. import motifs as M
        xm = -47.34 if sx < 0 else -34.2          # the merlons' middle line
        a, t, n = V((xm, YC, 0)), V((0, sx, 0)), V((sx, 0, 0))
        # n points away from the bridge's axis: out of the front (sx -1) or the yard face (sx 1)
        d_front = 2.4
        out = [M.slab(a, t, n, -CREST_Y, CREST_Y, WALK - 0.2, WALK + 0.9, -1.4, d_front + 0.2, front="course", back="stoneB"),
               M.slab(a, t, n, -CREST_Y + 0.3, CREST_Y - 0.3, WALK + 0.9, WALK + 3.1, -1.3, d_front, front="enamel", back="stoneB")]
        for k in (-1, 0, 1):
            out += kit.star(a, t, n, k * 3.6, WALK + 2.0, 0.8, d_front - 0.1, d_front + 0.3)
        zc = WALK + 3.1
        out.append(M.slab(a, t, n, -CREST_Y - 0.2, CREST_Y + 0.2, zc, zc + 0.7, -1.4, d_front + 0.35, front="course", back="stoneB"))
        zp, apex = zc + 0.7, zc + 0.7 + 4.4
        ph = CREST_Y - 0.4
        out.append(prism_uz(a, t, n, [(-ph, zp), (ph, zp), (0, apex)], -1.1, d_front - 0.3, [None, "stoneB", "stoneB"], "enamel", "stoneB"))
        for e in (-1, 1):
            poly = [(0, apex), (e * ph, zp), (e * (ph + 1.0), zp), (0, apex + 1.1)]
            out.append(prism_uz(a, t, n, poly, -1.2, d_front + 0.25, ["stoneB", "stoneB", "slate", None], "course", "stoneB"))
        out += kit.white_tree(a, t, n, 0.0, zp + 0.35, 3.3, d_front - 0.25, r=0.13)
        out += kit.winged_crest(a, t, n, 0.0, apex + 0.9, -0.6, 0.9, s=0.7)
        for e in (-1, 1):
            c = a + t * (e * (CREST_Y - 0.4)) + n * 0.1
            out += kit.pinnacle(c.x, c.y, zp, zp + 1.6, half=0.8, spire=2.8)
        return out

    # ------------------------------------------------------------------ banners
    @staticmethod
    def _banner(kit, s):
        from .. import motifs as M
        z_top, w, L = BANNER
        a, t, n = M.face((UPPER[1], YC + s * 26.6), (1, 0))
        return banner(kit, a, t, n, 0.0, z_top, w, L, d=0.9)

    def emphasis(self, c, n):
        if c.z > 44:
            return 1.3                      # crowns, crests
        return 1.0
