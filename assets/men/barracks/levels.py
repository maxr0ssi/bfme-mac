"""The Men's level-up meshes as chained recipes (the Dwarven archery range's pattern:
assets/dwarves/archery_tower, archery_walls). Import-safe anywhere (no Blender).

EA shows two extra meshes on most production buildings, both painted from the shared GBVet sheet
(Men-only): V1 from level 2 (SubObjectsUpgrade ...Level2: ShowSubObjects V1) and V2 from level 3
(V1 and V2). Each is redesigned by a recipe of its own, chained on the finished model below it:

    men/<building>          the body (EA's model)                      ships nothing itself
    men/<building>_level2   base = "men/<building>",        target V1  ships nothing itself
    men/<building>_level3   base = "men/<building>_level2", target V2  ships the whole model

Build them in that order (each extracts its base's finished model); rebuilding a link means
rebuilding the links after it. A level-3 recipe sees V1 finished, so its design escalates from it.

What the chain implies (sagekit/building.py, Building.per_level):

- no cloth and no night lights on a level mesh: the house-colour model and the night meshes are
  shown at every level, so they would hang in the air before the upgrade. Heraldry on a level
  mesh is stone, steel, sable and gilt (motifs.roundel, shields), never `cloth`.
- each link paints its own copy of GBVet (same name length, 5 letters): GBV<letter><1|2>,
  1 for V1 (level 2), 2 for V2 (level 3). Letters taken: B barracks, A archer range, S stable,
  F forge, W workshop (reserved). A new building picks a free letter and adds it here.
- the snow state swaps GBVet for GBVet_snow in the INI: each link gets its own variant (GBVB1_snow)
  through Building.variants. EA's damaged models (_D1.._D3) are painted from GBVetD, which no INI
  state swaps to and no derived body carries, so the framework finds no variant of ours for it and
  the lifecycle step leaves those models to EA; LevelMesh adds it (GBVB1D, with_damaged below), and
  a body recipe whose damaged models use a sheet of their own does the same for it.

    class BarracksLevel2(LevelMesh):
        source, target, letter, level = "GBBarracks_SKN", "V1", "B", 2
        base = chain("barracks", 2)
        own_textures = level_textures("B", 2)
"""
from sagekit.building import Building

from ..style import MenStyle

SHEET = "GBVet.tga"
DAMAGED = "GBVetD.tga"                  # EA's damaged models' copy of the sheet
LETTERS = {"barracks": "B", "archer_range": "A", "stable": "S", "forge": "F", "workshop": "W"}


def level_textures(letter, level):
    """{GBVet.tga: our copy} for a building's level-`level` mesh (2: V1, 3: V2)."""
    return {SHEET: "GBV%s%d.tga" % (letter, level - 1)}


def chain(building, level):
    """The base recipe of a building's level-`level` mesh: the body for level 2, level 2's for 3."""
    return "men/%s" % building if level == 2 else "men/%s_level%d" % (building, level - 1)


def with_damaged(b, variants, *sheets):
    """`variants` (Building.variants) plus our own copy of each EA damaged sheet in `sheets` that
    only the lifecycle models draw (GBBarracks_NewD.tga -> gbbarracks_neHD.tga, GBVetD.tga ->
    GBVB1D.tga: same length, named like EA's); names already there are kept."""
    from sagekit.taxonomy import own_variant_name
    out = dict(variants)
    have = {k.lower() for k in out}
    for t in sheets:
        if t.lower() not in have:
            out[t] = own_variant_name(b.sheet_atlas.texture, b.own_diffuse, t)
    return out


class LevelMesh(Building):
    """A level-up mesh redesigned on its base's finished model (see the module docstring).
    Subclasses set source, target ("V1" / "V2"), base, own_textures, views and design()."""
    style = MenStyle()
    sheet = SHEET
    house_tags = ()                 # shown per level: no cloth leaves for the house-colour model
    level = 2

    def variants(self, install):
        return with_damaged(self, super().variants(install), DAMAGED)
