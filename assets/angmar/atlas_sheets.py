"""Angmar's other sheets: where the materials are on each one.

KBFortress (atlas.py) paints the citadel; the other two master sheets paint the rest of the
fortress family, each with its own table here, in that sheet's own pixels (x right, y down; the
size is the healthy sheet's), read by eye on the flat sheets (2026-10-01):

    KBFortressB   the walls (hub, segment, gate, postern, tower, trebuchet, the cliff cap), the
                  wall-hub and battle-tower expansions, the catapult, the sanctum
    KBFortressX   the House of Lamentation, the fortress spikes, the kennel

Each table lists its materials in priority order: the first one whose rect a texel falls in wins;
slits lie over the rest (AngmarRecolour, paint.py). The materials are the citadel's (atlas.py):

    slit    the dark insides of arrow slits and barred windows: lit through the palette's "slit"
            ramp, darkest texel brightest; lighter texels (the frames) fall through
    iron    plates, panels, studded bands, brackets: rust on them found by colour
    planks  warm boards and beams: wood stays wood in every palette
    roof    the scale shingles
    timber  the dark frost-grained wood: its frost lines are the ramp's rime
    rock    the mossy ground patch
    stone   blocks, rubble, slabs and stairs: everything else

State sheets (_d1, _snow, and the Ice Walls upgrade's _ice, which EA swaps in by INI: KBFortress_Ice,
KBFortressB_Ice, KBFortressX_Ice) share their healthy sheet's layout (sheet_atlas). Their ice
crust lies over the stone at the walls' feet; on the _ice sheets it reads as pale stone through
the stone ramp until a table of its own maps it.

The production sheets (KBHall, KBDen, KBTemple, KBForge, KBMill, KBBtlTwr) get their tables
here when the production group starts: until then `sagekit sheets angmar` must not run (a sheet
without a table reads as stone, AngmarRecolour)."""
from sagekit.atlas import Atlas

_SLITS = [(48, 652, 88, 748), (176, 652, 212, 748), (302, 652, 338, 748),            # the small slits
          (388, 666, 437, 788), (468, 666, 514, 788), (543, 666, 592, 788), (623, 666, 670, 788),
          (703, 666, 752, 788), (806, 768, 832, 842),                                 # the tall ones
          (512, 490, 672, 582)]                                                       # the barred windows
_TIMBER = [(512, 0, 822, 135), (512, 345, 822, 450), (855, 570, 1024, 1024)]
_ROCK = [(512, 245, 612, 345)]
SHEETS = {
    "kbfortressb.tga": (1024, {
        "slit": _SLITS,
        "iron": [(0, 320, 385, 528),                    # the riveted plate panels
                 (345, 165, 512, 600),                  # the carved spire and its pieces
                 (822, 515, 1024, 570)],                # small bits and brackets
        "planks": [(345, 0, 410, 165), (822, 135, 1024, 515)],
        "roof": [(410, 0, 512, 135), (822, 0, 1024, 135)],
        "timber": _TIMBER,
        "rock": _ROCK,
        "stone": [(0, 0, 1024, 1024)],
    }),
    "kbfortressx.tga": (1024, {
        "slit": _SLITS,
        "iron": [(390, 566, 512, 597), (410, 626, 855, 658), (410, 770, 855, 800),   # the studded bands
                 (705, 452, 822, 532),                  # the stair's studded edges
                 (822, 515, 1024, 570)],
        "planks": [(60, 362, 512, 534),                 # the ochre beam
                   (822, 148, 1024, 515)],
        "roof": [(822, 0, 1024, 148)],
        "timber": _TIMBER,
        "rock": _ROCK,
        "stone": [(0, 0, 1024, 1024)],                  # blocks, the rune-diamond rubble, slabs
    }),
}
STATES = ("_d1", "_d", "_snow", "_ice")


def key(name):
    """The table a sheet reads: its own, or its healthy sheet's for a state sheet, or None."""
    k = name.lower().replace("\\", "/").split("/")[-1].replace(".dds", ".tga").replace(".png", ".tga")
    while k not in SHEETS:
        state = next((s for s in STATES if k.endswith(s + ".tga")), None)
        if state is None:
            return None
        k = k[:-len(state + ".tga")] + ".tga"
    return k


def sheet_atlas(name, ground_sat=(.6, .8)):
    """The Atlas of one of the tabled sheets (materials in its own pixels, `own_sheet` set), or None
    (KBFortress and its states: the faction atlas; the rest: no table yet)."""
    k = key(name)
    if k is None:
        return None
    size, materials = SHEETS[k]
    a = Atlas()
    a.texture, a.size, a.materials, a.own_sheet = name, size, materials, True
    a.ground_sat = ground_sat
    return a
