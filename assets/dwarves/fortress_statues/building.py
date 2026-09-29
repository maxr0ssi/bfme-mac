"""The fortress's statue upgrade (FORTRESS_IMPROVEMENT_3, Draw ModuleTag_StatueDraw of
DwarvenFortressCitadel): the axe-bearing dwarf over the gate, raised on a new stepped plinth -
a hexagon-chain step on the gate crown's platform, a bronze ledge, a rune die, a bronze cornice
and two statue steps with gold trim. EA's figure (and its painted stone) is kept as it is.

EA's statue (mesh DBFSTATUS, drawn at the fortress's origin; a bare mesh file, no hierarchy)
stands on a pale plinth: a pointed-back block x 72.2..89.42, |y| 9.49 (axis y -0.31), z
49.56..64.96, an arcaded cornice to 67.7 (x 71.93..89.8, y -9.73..9.10), a base to ~69.9 and a
hexagonal plaque on the gate front (x 89.34..90.66, z 42..63.45) sunk in the gate crown.

On the redesigned fortress (assets/dwarves/fortress) the gate crown's main block tops out at z 59.6
(x 83.3..90.9, |y| 10.4) and its stepped tiers rise inside the statue's footprint (hexagon tier
x 84.3..90.0, |y| 8.6 to 64.2, then to a point at 70.0): the new plinth encloses those tiers and
EA's plinth, cornice and base, so the statue stands on one clean stepped block. Everything stays
inside EA's bounding box (x 71.93..90.66, y -9.73..9.10). All measurements in DBFSTATUS mesh
coordinates (= the fortress's), taken from the original model."""
from sagekit.building import Building

from ..style import DwarvenStyle


X0, X1 = 71.93, 90.66                         # EA's statue box, back and front
Y0, Y1 = -9.73, 9.10


class FortressStatues(Building):
    style = DwarvenStyle()
    source = "DBFStatus"
    target = "DBFSTATUS"
    sheet = None                                                # the faction atlas DBFortress1
    own_textures = {"DBFortress1.tga": "DBFortressS.tga"}
    parts = ("ModuleTag_StatueDraw",)
    tri_budget = 1500
    facet_islands = True        # EA's figure (arms, beard, axe haft) folds over itself unwrapped uncut
    views = {
        "rts": ((81, -0.3, 70), 150, 50, -38, 50),
        "close": ((82, -0.3, 72), 95, 20, -30, 45),
        "ingame": ((81, -0.3, 60), 420, 53, -62, 50),
    }

    def design(self, kit):
        from sagekit.blender.geometry import box_rings, loft

        def B(x0, x1, y0, y1, z, ch=0.5):
            return box_rings((x0, x1), (y0, y1), z, ch)
        y0, y1 = Y0 + 0.03, Y1 - 0.03                 # just inside EA's cornice sides (they are the box's edge)
        rings = [
            B(72.1, 90.1, -9.60, 8.98, 49.5),                 # the block, down through the crown
            B(72.1, 90.1, -9.60, 8.98, 59.6),                 # hexagon-chain step above the crown's platform
            B(72.1, 90.1, -9.60, 8.98, 62.2),
            B(X0, X1, y0, y1, 62.2), B(X0, X1, y0, y1, 62.8),   # bronze ledge
            B(X0, X1, y0, y1, 67.7),                          # rune die round EA's plinth and cornice
            B(X0, X1, y0, y1, 68.3),                          # bronze cornice
            B(73.4, 89.9, -9.10, 8.50, 68.3), B(73.4, 89.9, -9.10, 8.50, 69.4),    # first statue step
            B(74.3, 89.4, -8.65, 8.03, 69.4, 0.4), B(74.3, 89.4, -8.65, 8.03, 70.5, 0.4),  # gold step
        ]
        # the die's sides: EA's arcaded cornice (64.96..67.7) stands 0.03 proud there and shows
        die = ["stoneB", "stoneB", "rune", "stoneB", "stoneB", "stoneB", "rune", "stoneB"]
        tags = ["stoneB", sides("hex", "stoneB"), "stoneB", "trim", die, "trim", "top", "stoneA", "top", "trim"]
        return [loft(rings, tags, cap0=("stoneB", False), cap1=("top", True))]

    def cache_ops(self, variants=None, derived=()):
        """Framework workaround (sagekit/building.py Building.cache_ops): the object record of a
        bare mesh file is 'DBFSTATUS', not 'DBFSTATUS.DBFSTATUS'; with the default name the
        dependency switch to our texture is silently skipped (route_cache_ops finds no object)."""
        obj = "%s.%s" % (self.source.upper(), self.target)
        return [op[:4] + (self.target,) if op[0] == "texture" and op[4] == obj else op
                for op in super().cache_ops(variants, derived)]

    def emphasis(self, c, n):
        return 1.3 if c.z > 59 else 1.0        # the plinth above the gate crown


def sides(tag, other):
    """Chamfered ring: the four faces (even sides) get `tag`, the chamfers `other`."""
    return [tag if k % 2 == 0 else other for k in range(8)]
