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
from sagekit.formats import w3d as _w3d

from ..style import DwarvenStyle


def _bare_mesh_entries(cache_entries):
    """Framework workaround (sagekit/formats/w3d.py W3DFile.cache_entries): a bare mesh file (no
    hierarchy, empty container name, like dbfstatus.w3d) is filed in asset.dat as 'DBFSTATUS',
    not '.DBFSTATUS'; with the dot, the cache step cannot match the record to patch it."""
    if getattr(cache_entries, "bare_mesh_fix", False):
        return cache_entries

    def fixed(self):
        return [(n[1:] if tag == b"HSEM" and n and n.startswith(".") else n, tag, o, s)
                for n, tag, o, s in cache_entries(self)]
    fixed.bare_mesh_fix = True
    return fixed


_w3d.W3DFile.cache_entries = _bare_mesh_entries(_w3d.W3DFile.cache_entries)


def _bare_mesh_snapshot():
    """Framework workaround (sagekit/blender/checks.py snapshot): it reads arms[0] and so crashes
    on a model without a hierarchy. Blender side only: while a snapshot imports a model that has
    no armature, an empty stand-in armature is added, so the original and ours both report one
    armature with no bones (the structure checks then compare like with like)."""
    try:
        import bpy
        from sagekit.blender import checks
    except ImportError:                          # host side: nothing to patch
        return
    if getattr(checks.snapshot, "bare_mesh_fix", False):
        return
    snapshot = checks.snapshot

    def fixed(path, skeletons=None):
        imp = checks.scene.import_w3d

        def import_w3d(p, skl=None):
            imp(p, skl)
            if not any(o.type == "ARMATURE" for o in bpy.data.objects):
                o = bpy.data.objects.new("NO_HIERARCHY", bpy.data.armatures.new("NO_HIERARCHY"))
                bpy.context.collection.objects.link(o)
        checks.scene.import_w3d = import_w3d
        try:
            return snapshot(path, skeletons)
        finally:
            checks.scene.import_w3d = imp
    fixed.bare_mesh_fix = True
    checks.snapshot = fixed


_bare_mesh_snapshot()


def _figure_seams():
    """Recipe-side layout tweak (sagekit/blender/layout.py _seams cuts EA's faces only at hard
    edges over 40 degrees): EA's dwarf figure is organic - arms, beard, axe haft - and its
    smooth loops, unwrapped uncut, fold over themselves in the new layout (0.2 % of texels
    painted twice, arms and axe). Here every edge between two of EA's faces is a seam too, so each
    of EA's triangles is its own island and none can overlap. Blender side only."""
    try:
        import bmesh
        from sagekit.blender import layout
    except ImportError:
        return
    if getattr(layout._seams, "figure_fix", False):
        return
    seams = layout._seams

    def fixed(me):
        seams(me)
        bm = bmesh.new()
        bm.from_mesh(me)
        tagl = bm.faces.layers.int[layout.TAG_ATTR]
        for e in bm.edges:
            if all(f[tagl] == 0 for f in e.link_faces):
                e.seam = True
        bm.to_mesh(me)
        bm.free()
    fixed.figure_fix = True
    layout._seams = fixed


_figure_seams()

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
