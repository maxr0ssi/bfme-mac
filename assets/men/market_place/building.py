"""The Gondor market place (GondorMarketPlace, ArnorMarketPlace; model GBMarket_SKN): EA's market
kept whole - the stepped platform and its paving, the arcaded walls, the campanile with its open
belfry and bell, the stalls, crates and baskets, and the three cut-out awnings - and dressed in
the citadel's stone, steel and sable:

    campanile   crowned like the citadel's towers: a machicolated gallery at the shaft's top
                (corbels, a sable band of gilt stars, a parapet of square merlons) and four
                corbelled bartizans with slit windows and slate spirelets on its corners; steel
                ribs up the dome, a lantern cupola, a steel mast, a gilt orb and a spike; a
                pinnacle on each corner of the belfry's cornice; a sable band with gilt stars
                across each belfry face; White Tree roundels on the shaft's south and east faces
    arcade      a sable frieze of gilt stars under the south and east walls' coping; over each
                pier a moulded cap and a pinnacle; a raised keystone at every arch head and a
                White Tree roundel in the spandrel between the south arches
    west wall   over its great arch a pediment the wall's thickness deep: a sable tympanum with
                the White Tree, raking cornices, a pinnacle on the apex and keystones on both
                faces; pinnacles at the raised wall's ends (the torch keeps its place)
    banners     two house-colour banners on the arcade's end piers facing south and east (the
                RTS camera's sides)

The vendor, the townswoman, the chicken and the basket animate inside the arcade (x 8..32,
y -17..-2.5): nothing new stands there; the awnings (cut-outs, DXT5) and their posts, and the
torch's flame card (x -33..-27.5, y -24..-3.8, z 32.8..38.3) keep their places.

EA's MARKET_STRUCTUR (mesh = model coordinates): the campanile at (-18.24, 16.72), its shaft's
faces 8.69 out to z 33, battered in to 7.34 by 37, windows at 44.8..47, the belfry open from
49 to its lintel at 57.4..61.8 between corner columns (|u| > 4.24, to 63.5), the cornice at
63.5 (8.09), the square dome through (65.6, 6.57), (67.2, 5.85), (69.3, 4.13), (70.4, 2.6),
(71.2, 0.97) to 72.25. The south arcade wall y -35.16..-33.18, x -4.57..33.75, arches centred
x 5.68 and 22.68 (13.5 wide, crowns 29.57), coping to 32.2; the east wall x 31.3..33.28, y
-35.56..3.47, one wide arch between y -27 and -1; the west wall x -26.11..-23.5 raised to 41.51
between y -26.7 and -0.6. Height limit +20 %: z 86.8."""
from sagekit.building import Building

from ..style import MenStyle

TX, TY = -18.24, 16.72                       # the campanile's axis
SHAFT = 7.34                                 # its upper faces (z 37..44.8)
DOME = [(63.6, 8.0), (65.6, 6.57), (67.2, 5.85), (69.3, 4.13), (70.4, 2.6)]
LANTERN = (69.9, 2.3, 74.6)
FINIAL = (78.6, 85.0)
SOUTH, EAST = (-35.16, (-4.57, 33.75)), (33.28, (-35.56, 3.47))
PIERS_S, PIERS_E = (-2.82, 14.18, 31.6), (-31.3, 1.23)
TOP_WALL = 32.2
WEST = (-26.11, -23.5, (-26.3, -1.0), 41.51)
WEST_ARCH = (-13.67, 7.5, 35.65)             # its great arch: y centre, half, crown
GALLERY = (42.6, 46.0, 47.8)                 # corbel foot, slab foot, slab top (the shaft slopes in from 45.5)
ARCH_S = (5.68, 22.68)                       # the south arches' centres (crowns 29.57)
ARCH_E = (-14.0, 27.0)                       # the east arch: y centre, crown


class MarketPlace(Building):
    style = MenStyle()
    source = "GBMarket_SKN"
    target = "MARKET_STRUCTUR"
    sheet = "GBMarketPlace.tga"
    sheet_normal = "GBMarketPlace_NRM.tga"
    own_textures = {"GBMarketPlace.tga": "GBMarketPlacH.tga"}      # free in EA's files and every recipe (sagekit/names.py)
    views = {
        "rts": ((0.3, -4.8, 35.8), 299, 50, -38, 50),
        "close": ((5.0, -10.0, 25.0), 150, 22, -40, 45),
        "tower": ((-18.2, 16.7, 60.0), 70, 18, -40, 45),
        "ingame": ((0.3, -4.8, 35.8), 680, 53, -62, 50),
    }

    def decals(self):
        from ..workshop.prodkit import props_layer
        return [props_layer(sat=(0.3, 0.45), gate=(0.35, 0.6))]          # EA's crates, stalls and awning stay wood and cloth

    def design(self, kit):
        out = []
        out += self._campanile(kit)
        out += self._arcade(kit)
        out += self._west(kit)
        return out

    @staticmethod
    def _campanile(kit):
        from ..barracks import motifs as M
        from ..shapes import rail
        out = []
        # ribs up the square dome: its four hips and the middle of each face
        for sx, sy, mid in [(1, 1, 0), (1, -1, 0), (-1, 1, 0), (-1, -1, 0), (1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1)]:
            pts = []
            for z, h in DOME:
                px, py = TX + sx * h, TY + sy * h
                ox, oy = (sx, sy)
                L = (ox * ox + oy * oy) ** 0.5
                pts.append((px + ox / L * 0.2, py + oy / L * 0.2, z + 0.1))
            out.append(rail(pts, 0.3, "trim", 0.16))
        z0, r, top = LANTERN
        out += kit.lantern(TX, TY, z0, r=r, top=top)
        orb, tip = FINIAL
        out += kit.finial(TX, TY, top - 0.1, orb, tip)
        for sx in (1, -1):                       # corner pinnacles on the cornice
            for sy in (1, -1):
                out += kit.pinnacle(TX + sx * 7.3, TY + sy * 7.3, 63.4, 65.2, half=0.8, spire=3.0)
        for nx, ny in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, t, n = M.face((TX + 5.88 * nx, TY + 5.88 * ny), (nx, ny))
            out += M.star_frieze(kit, a, t, n, -4.1, 4.1, 59.4, h=2.1, d0=-0.3, d1=0.3, count=3)
        for nx, ny in ((1, 0), (0, -1)):         # roundels facing the camera
            a, t, n = M.face((TX + SHAFT * nx, TY + SHAFT * ny), (nx, ny))
            out += M.roundel(kit, a, t, n, 0.0, 39.0, 2.0, d=0.2)
        out += MarketPlace._gallery(kit)
        return out

    @staticmethod
    def _gallery(kit):
        """The citadel's gallery round the shaft's top: two-step corbels between the corner fins,
        a slab 1.8 out with a sable front and gilt stars, a parapet with square merlons, and a
        corbelled bartizan on each corner."""
        import math

        from ..barracks import motifs as M
        zc, zs, zw = GALLERY
        sq = M.octagon(TX, TY, SHAFT, 0.0)
        out = M.band_path(sq, zs, zw, -1.6, 1.8, ["stoneB", "enamel", "top", None], center=(TX, TY))
        out += M.band_path(sq, zw, zw + 1.0, 1.05, 1.75, [None, "stoneA", "top", "stoneA"], center=(TX, TY))
        for nx, ny in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, t, n = M.face((TX + SHAFT * nx, TY + SHAFT * ny), (nx, ny))
            for u in (-4.6, -2.3, 0.0, 2.3, 4.6):
                out += kit.corbel(a, t, n, u, zc, w=0.45, z1=zc + 1.7, z2=zs, d1=0.8, d2=1.7)
            for u in (-3.45, 0.0, 3.45):
                out += kit.star(a, t, n, u, (zs + zw) / 2, 0.72, 1.7, 2.05)
            out += kit.merlons(a, t, n, -5.6, 5.6, zw + 1.0, 1.05, 1.75, w=1.7, gap=1.3, h=2.0, cap=0.4)
        r = 12.4 / math.sqrt(2)
        for dx in (1, -1):
            for dy in (1, -1):
                out += kit.bartizan(TX + dx * r, TY + dy * r, zc - 1.2, r=1.75, h=6.4, spire=5.6, facing=math.atan2(dy, dx))
        return out

    @staticmethod
    def _arcade(kit):
        from ..barracks import motifs as M
        out = []
        y, (x0, x1) = SOUTH
        a, t, n = M.face(((x0 + x1) / 2, y), (0, -1))
        u0, u1 = sorted(((x0 + 0.1 - a.x) * t.x, (x1 - 0.5 - a.x) * t.x))
        out += M.star_frieze(kit, a, t, n, u0, u1, 29.95, h=1.55, d0=-0.3, d1=0.45, pitch=3.2)
        for px in PIERS_S:
            out += MarketPlace._pier_top(kit, px, -34.17)
        for x in ARCH_S:
            out += MarketPlace._keystone(a, t, n, (x - a.x) * t.x, 29.57)
        out += M.roundel(kit, a, t, n, (14.18 - a.x) * t.x, 27.55, 1.85, d=0.2, studs=False)
        x, (y0, y1) = EAST
        a, t, n = M.face((x, (y0 + y1) / 2), (1, 0))
        u0, u1 = sorted(((y0 + 0.5 - a.y) * t.y, (y1 - 0.1 - a.y) * t.y))
        out += M.star_frieze(kit, a, t, n, u0, u1, 29.95, h=1.55, d0=-0.3, d1=0.45, pitch=3.2)
        for py in PIERS_E:
            out += MarketPlace._pier_top(kit, 32.29, py)
        y_arch, crown = ARCH_E
        out += MarketPlace._keystone(a, t, n, (y_arch - a.y) * t.y, crown)
        # the banners on the end piers (narrow piers: the rod alone, no consoles)
        a, t, n = M.face((-1.4, y), (0, -1))
        out += kit.banner(a, t, n, 0.0, 29.3, 2.4, 11.5, d=0.8)
        a, t, n = M.face((x, -0.2), (1, 0))
        out += kit.banner(a, t, n, 0.0, 29.3, 2.4, 11.5, d=0.8)
        return out

    @staticmethod
    def _pier_top(kit, x, y):
        """A moulded cap over an arcade pier (a plinth block and a cornice), a pinnacle on it."""
        from ..barracks import motifs as M
        out = [M.box(x - 1.25, x + 1.25, y - 1.25, y + 1.25, TOP_WALL - 0.05, TOP_WALL + 0.9, "stoneB", cap1=("top", True)),
               M.box(x - 1.5, x + 1.5, y - 1.5, y + 1.5, TOP_WALL + 0.9, TOP_WALL + 1.4, "course", cap0=("course", True), cap1=("top", True))]
        return out + kit.pinnacle(x, y, TOP_WALL + 1.4, TOP_WALL + 4.0, half=0.95, spire=3.6)

    @staticmethod
    def _keystone(a, t, n, u, crown):
        """A raised keystone over an arch head, from its crown (not below: the arch's void would show
        the stone's underside to the sky) up into the frieze."""
        from sagekit.blender.geometry import prism_uz
        return [prism_uz(a, t, n, [(u - 0.65, crown + 0.02), (u + 0.65, crown + 0.02), (u + 1.0, crown + 2.4), (u - 1.0, crown + 2.4)],
                         -0.3, 0.95, ["stoneB", "stoneB", "top", "stoneB"], "stoneA", None)]

    @staticmethod
    def _west(kit):
        from ..barracks import motifs as M
        x0, x1, (y0, y1), z = WEST
        a, t, n = M.face((x1, (y0 + y1) / 2), (1, 0))
        h = (y1 - y0) / 2 - 1.1
        out = []
        for y in (y0 + 0.9, y1 - 0.9):
            out += kit.pinnacle((x0 + x1) / 2, y, z, z + 2.2, half=1.0, spire=3.2)
        out += MarketPlace._pediment(kit)
        return out

    @staticmethod
    def _pediment(kit):
        """A pediment over the west wall's great arch, as deep as the wall, on its raised top."""
        from sagekit.blender.geometry import prism_uz
        from ..barracks import motifs as M
        x0, x1, _, z = WEST
        yc, half, crown = WEST_ARCH
        a, t, n = M.face((x1, yc), (1, 0))               # u along t = (0, 1)... in world y, d out of the court face
        d0, d1 = -(x1 - x0) - 0.35, 0.35
        w = half + 2.0
        out = [M.slab(a, t, n, -w - 0.3, w + 0.3, z - 0.1, z + 0.8, d0 - 0.2, d1 + 0.2, front="course", back="course")]
        zp, apex = z + 0.8, z + 0.8 + 5.2
        out.append(prism_uz(a, t, n, [(-w, zp), (w, zp), (0, apex)], d0, d1, [None, "stoneB", "stoneB"], "enamel", "enamel"))
        for e in (-1, 1):
            poly = [(0, apex), (e * w, zp), (e * (w + 1.0), zp), (0, apex + 1.1)]
            out.append(prism_uz(a, t, n, poly, d0 - 0.15, d1 + 0.15, ["stoneB", "stoneB", "top", None], "course", "course"))
            out += kit.pinnacle(x0 + (x1 - x0) / 2, yc + e * (w + 0.4), zp, zp + 1.2, half=0.75, spire=2.6)
        out += kit.white_tree(a, t, n, 0.0, zp + 0.5, 3.6, d1 - 0.05, r=0.13)
        b, tb, nb = M.face((x0, yc), (-1, 0))
        out += kit.white_tree(b, tb, nb, 0.0, zp + 0.5, 3.6, 0.3, r=0.13)
        c = (x0 + x1) / 2
        out += kit.pinnacle(c, yc, apex + 0.5, apex + 1.5, half=0.75, spire=2.8)
        out += MarketPlace._keystone(a, t, n, 0.0, crown)
        out += MarketPlace._keystone(b, tb, nb, 0.0, crown)
        return out

    def emphasis(self, c, n):
        return 1.3 if c.z > 28 else 1.0
