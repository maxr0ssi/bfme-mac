# Mallorn tree (`ElvenMallornTree`, `elvenmallorntree.ini`)

Model `EBMalTree`, redesigned mesh `EBMALTREE`: the trunk, roots and branches, 1,014 triangles.
It is painted from `EBMalTree.tga` (+ `_NRM`, DXT5 with EA's cut-out alpha, kept). Our texture is
`EBMalTreH.tga` (+ `_NRM`, `_D`, `_Snow`); new faces are mapped onto the faction atlas.
`Tier.STANDARD`.

- **Own copy:** the tree ships as `EBMalTree2` (`own_model`), because Arnor
  (`ArnorMallornTree`) and Amon Sul's map piece draw `EBMalTree` too.
- **Bone:** the body hangs on a bone turned 90 degrees, so the recipe works in model axes
  (`world_space`).

## The tree stays a tree

EA's leaves (`EBMALTREELEAVES`, gold cut-out cards) are untouched, and so are the talan (`V2A`),
the spiral stair of boards (`V2`), the lamp-bearing maiden on her pedestal (`V1`) and the torch
cards (`V1A`). The trunk and branches keep their shape. They are repainted by the style: the bark
comes out silver-grey, the Foliage layer keeps any green on the sheet green, and the cut-outs are
carried over.

## What changed (body, healthy)

- **Stair balustrade:** a silver balustrade follows EA's spiral stair up to the talan, measured
  from the stair's outer edge (`STAIR`: angle round (-7.5, -4.5), radius, board height). Turned
  balusters stand on the boards every ~1.5, under a rounded rail 2.55 over the boards.
- **Talan edge:** a narrow gold fascia and hanging leaf fringe follow the existing platform edge.
- **Newels:** a newel column with a crystal lantern stands either side of the stair's foot.
- **Lantern columns:** three slender lantern columns stand among the roots, 30 from the trunk, clear
  of the stair and the maiden.
- **Hanging lanterns:** three big crystal lanterns on gilt rods hang in the tree where EA's
  night-only lamps are (`N_WINDOW`), so there is something there by day and it carries the light
  at night.
- **Banners:** two leaf banners hang from the talan's rail on the camera's side, in the player's
  colour. `EBHCMalTree` is Arnor's too, so the house step ships an own copy, `EBHCMalTree2`, shown by
  the Elven mallorn only.

Earlier pass measurements (retained for history; current build evidence is in `work/logs/checks.log`):

Footprint and height unchanged (x -59.2..41.8, y -30.0..39.7, z 0.2..110.9). Triangles 1,014 ->
8,472 (the balusters are most of it). Texel density median 13.5 px/unit. `checks`: 105/105.

`facet_islands = True`: every original face of the trunk is its own UV island. Blender's unwrap of
the trunk's smooth shells folded onto itself (0.2 % overlap; the check wants none). This is a new
opt-in `Building` attribute (see the report's framework notes).

## Night

`night_lights`: every crystal is lit on the two facets the RTS camera sees, with no halo (a crystal
standing or hanging free has no wall to spill light on). That is the three hanging lanterns, the
two newels and the three lantern columns. EA's three canopy glow cards (`N_GLOW`, 24 x 24 additive
planes) stay round the three hanging lanterns as free-hanging glows (`Light.glow`).

## Status

The latest ivory, mithril and mallorn-gold pass is built and passes the offline checks;
review is still required before installation. Lifecycle fallbacks below remain intentional.

| Part | Healthy | Construction | Damaged | Really damaged | Rubble | Snow | LOD M/L |
|---|---|---|---|---|---|---|---|
| body (`EBMalTree2`) | built, checks pass, **awaiting review** | derived (`EBMalTree2_ASKN`) | derived (`EBMalTree2_D1`) | EA's (`EBMalTree_D2`: the lifecycle step refused `MALTREE_PIECE01`'s vertex layout) | built (`EBMalTree2_D3`) | `EBMalTreH_Snow` painted | old |
| banner (`EBHCMalTree2`, own copy) | 2 banners | | | | | | |

## Note for review

The renders alpha-test EA's leaf cards as the game does (sagekit/blender/render.py `cut_out`), so
the canopy in `renders/compare_*.png` is leaves, not black squares.
