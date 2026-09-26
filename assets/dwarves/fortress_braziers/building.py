"""The fortress's flame upgrade (FORTRESS_IMPROVEMENT_1, Draw ModuleTag_MunitionsDraw of
DwarvenFortressCitadel and DwarvenSummonedCitadelKeep): the two brazier columns either side of the
gate, rebuilt as gilded Dwarven braziers - an octagonal stepped pillar with a pilaster front and a
gold rune belt, a stepped capital, and on it an inverted stepped bowl: a rune band at its foot,
flaring bronze tiers and a gold rim with four stepped corner points round the fire bed (plain
bronze, not the gate crown's triangle frieze beside it, so the bowls read apart from the crown).

EA's brazier (mesh DBFFLAM, drawn at the fortress's origin) is a hexagonal column (vertex radius
2.44 at the ground, 3.26 at z 47.2) under a hexagonal cup (4.78 at z 55.7, inner rim 56.25, bottom
53.4); every new tier encloses it, so none of it shows. The fire cards (FLAMES, FIREGLOW) and
their bones are EA's and untouched: the fire bed stays at the cup's top (56.3).

The fortress (assets/dwarves/fortress) leaves the braziers a slot: the gate lintel and crown stop
at |y| 10.4, the pylons start at |y| 19.8, and each jamb carries a capping slab at z 44.2..45.0.
Everything here stays inside EA's bounding box (x 80.80..90.35, y -19.64..19.03). All
measurements in DBFFLAM mesh coordinates (= the fortress's), taken from the original model."""
from sagekit.building import Building

from ..style import DwarvenStyle

CX = 85.5738                                  # both columns' centre x
CYS = (14.8877, -15.5022)                     # +y and -y column centres (mirrored about the gate axis y -0.31)
RIM_X, RIM_Y = 4.778, 4.138                   # the bowl's rim: EA's cup's full extent (the bounding box)
SLAB_TOP = 45.0                               # the fortress's jamb capping slab


def hex_r(z):
    """Vertex radius of EA's hexagonal column at height z (2.44 at the ground, 3.26 at 47.2)."""
    return 2.44 + z * (3.26 - 2.44) / 47.2


class FortressBraziers(Building):
    style = DwarvenStyle()
    source = "DBFFlam"
    target = "DBFFLAM"
    sheet = None                                                # the faction atlas DBFortress1
    own_textures = {"DBFortress1.tga": "DBFortressF.tga"}
    parts = ("ModuleTag_MunitionsDraw",)
    tri_budget = 2000
    views = {
        "rts": ((86, -0.3, 34), 150, 50, -38, 50),
        "close": ((87, -0.3, 40), 95, 22, -30, 45),
        "ingame": ((86, -0.3, 30), 420, 53, -62, 50),
    }

    def design(self, kit):
        solids = []
        for cy in CYS:
            solids += self._pillar(cy)
            solids += self._bowl(cy)
        return solids

    @staticmethod
    def _pillar(cy):
        """An octagonal pillar round EA's hexagonal column (each ring a chamfered box whose chamfers
        run along the hexagon's slanted sides): stepped base, pilaster-fronted shaft, a gold rune
        belt between bronze rings, and a stepped capital up to the jamb's capping slab."""
        from sagekit.blender.geometry import box_rings, loft

        def O(r, z, k=1.06):                    # an octagon enclosing the hexagon of radius r
            r *= k
            return box_rings((CX - r, CX + r), (cy - 0.866 * r, cy + 0.866 * r), z, 0.5 * r)

        def B(hx, hy, z, ch=0.4):
            return box_rings((CX - hx, CX + hx), (cy - hy, cy + hy), z, ch)

        def front(tag, other="stoneB"):        # chamfered ring sides: 0 y0, 2 front (+X), 4 y1, 6 back
            return [tag if k == 2 else other for k in range(8)]
        shaft0, shaft1 = hex_r(2.6) + 0.1, hex_r(40.0) + 0.05
        s = lambda z: shaft0 + (shaft1 - shaft0) * (z - 2.6) / (40.0 - 2.6)   # noqa: E731
        rings = [O(3.2, 0.0), O(3.2, 1.3), O(2.85, 1.3), O(2.85, 2.6), O(s(2.6), 2.6),
                 O(s(28.4), 28.4), O(s(28.4) + 0.35, 28.4), O(s(28.4) + 0.35, 29.2),       # bronze ring
                 O(s(28.4) + 0.25, 29.2), O(s(28.4) + 0.25, 32.6),                          # rune belt
                 O(s(28.4) + 0.35, 32.6), O(s(28.4) + 0.35, 33.4), O(s(33.4), 33.4),       # bronze ring
                 O(s(40.0), 40.0),
                 B(3.55, 3.2, 40.0), B(3.55, 3.2, 41.6),                                       # capital
                 B(3.75, 3.45, 41.6), B(3.75, 3.45, 45.2)]
        tags = ["stoneB", "top", "stoneB", "top", front("pilaster", "stoneA"),
                "stoneB", "trim", "top", sides_("rune", "trim"), "stoneB", "trim", "top",
                front("pilaster", "stoneA"),
                "stoneB", "trim", "stoneB", "stoneB"]
        return [loft(rings, tags, cap0=("stoneB", False), cap1=("top", True))]

    @staticmethod
    def _bowl(cy):
        """The brazier on the capital: two plinth steps, then an inverted stepped bowl (rune band,
        gold band, two flaring bronze tiers, gold rim) round a fire bed, with a stepped
        gold point on each corner of the rim."""
        from mathutils import Vector as V
        from sagekit.blender.geometry import box_rings, loft

        def B(hx, hy, z, ch):
            return box_rings((CX - hx, CX + hx), (cy - hy, cy + hy), z, ch)
        rings = [B(3.6, 3.3, 45.2, 0.4), B(3.6, 3.3, 46.0, 0.4),          # plinth
                 B(3.35, 3.05, 46.0, 0.35), B(3.35, 3.05, 46.8, 0.35),     # bronze step
                 B(3.75, 3.3, 46.8, 0.4), B(3.75, 3.3, 48.6, 0.4),         # rune band
                 B(4.05, 3.6, 48.6, 0.45), B(4.05, 3.6, 49.1, 0.45),       # gold band
                 B(4.25, 3.78, 49.1, 0.5), B(4.4, 3.9, 52.0, 0.5),         # bronze tier
                 B(4.6, 4.02, 52.0, 0.5), B(4.7, 4.1, 55.0, 0.5),          # bronze tier
                 B(RIM_X, RIM_Y, 55.0, 0.5), B(RIM_X, RIM_Y, 56.8, 0.5),   # gold rim
                 B(3.5, 2.9, 56.8, 0.35), B(3.5, 2.9, 56.3, 0.35)]         # lip, fire bed
        tags = ["stoneB", "top", "trim", "stoneB", sides_("rune", "trim"), "stoneB", "trim", "stoneB",
                "trim", "stoneB", "trim", "stoneB", "trim", "trim", "stoneB"]
        out = [loft(rings, tags, cap0=("stoneB", False), cap1=("stoneB", True))]
        for sx in (-1, 1):                     # stepped gold points on the rim's corners
            for sy in (-1, 1):
                x, y = CX + sx * 3.9, cy + sy * 3.3
                r0 = box_rings((x - 0.45, x + 0.45), (y - 0.45, y + 0.45), 56.8, 0)
                r1 = box_rings((x - 0.45, x + 0.45), (y - 0.45, y + 0.45), 57.5, 0)
                r2 = box_rings((x - 0.3, x + 0.3), (y - 0.3, y + 0.3), 57.5, 0)
                out.append(loft([r0, r1, r2, [V((x, y, 58.8))] * 4], ["trim", "top", "trim"],
                                cap0=("trim", False), cap1=("trim", False)))
        return out

    def emphasis(self, c, n):
        return 1.3 if c.z > 44 else 1.0        # the bowls: what the RTS camera sees


def sides_(tag, other):
    """Chamfered ring: the four faces (even sides) get `tag`, the chamfers `other`."""
    return [tag if k % 2 == 0 else other for k in range(8)]
