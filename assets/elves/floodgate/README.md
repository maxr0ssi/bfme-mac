# Elven floodgate (`ElvenFloodgateExpansion`)

Model `EBFFGate`, redesigned mesh `EBFFGATE1`, `Tier.STANDARD`, painted from the faction sheet
`EBFortress.tga` onto its own textures `EBFortresF.tga` / `EBFortresF_NRM.tga` (DXT5: EA's cut-out
alpha kept; + `_D`, `_snow`, `_U` variants). The flood doors are the Draw module
`ModuleTag_DrawDoors`, a model of their own: [`floodgate_doors`](../floodgate_doors/README.md).

The Bruinen's flood-tower on the fortress's pad: three rearing stone horses on a basin, pouring the
flood from their mouths, over a drum of pointed bays between buttress piers; the arm back to the
fortress is an aqueduct over the expansions' arch. The horses, the water (`EBFFGATE3/5/6`: the
streams, the basin, the splash; `GBWell_waterB`, `RBWell_waterB` are not ours to recolour), the
ground ring (`EBFFGATE4`) and the niches the doors close stay EA's. The streams fall within 17.6
of the drum's axis, inside the rim: nothing new is in their way.

## What changed (body, healthy)

- **Crown:** a moulded silver coping round the basin's rim (0.4 over it, its nose over EA's
  crown) carrying a ring of lancet merlons (1.8 wide, 4.0 high): the horses now rise from an Elven
  crown. It runs from the aqueduct's one wall round the front to the other.
- **Banners:** a leaf banner in the player's colour down each of the six buttress piers (2.6 x
  17.5, hung just under the crown, lying on the pier's front), so the drum carries the house's
  colours all round. The cloth goes to our house-colour model `EBHCFFGate` (Draw tag
  `ModuleTag_Draw_HCFloodgate`, from the style's `house_template`). The kit's leaf-bud rod ends
  are left off here: on the piers they would reach 1.3 past the footprint.
- **Aqueduct:** the same coping along both walls' tops, and the expansions' pointed silver frame
  round the arch on both faces (sea-green enamel reveals, a gilt leaf over the point;
  [`pad.py`](pad.py), shared with the watchtower and the vigilant ent).
- **Paint:** the faction style (moonstone, silver mouldings, gilt leaf, sea-green enamel).

`footprint_margin = 0.9`: the piers' fronts are EA's bounding box (y +-21.37, and x 21.55 at the
crown); the banners' gilt rods, 38.4-39 up, stand up to 0.85 past it. Nothing new passes it at
the ground. `facet_islands = True`: Blender's angle-based unwrap folded the horses' UVs onto themselves
(0.7 % overlap on EA's own faces, with or without EA's seams); every EA face is its own island.

Night lights: EA's model has no night meshes and the INI names none (`NightWindowName`); nothing
to light.

## Shared: `pad.py`

The expansions' connecting arm and its arch (EA drew the same arch into the floodgate, the
watchtower and the vigilant ent, shifted along x): `arch()` frames it, `coping()` runs the
moulding along an arm's top. `coping_profile()` is the kit's `coping_run` moulding without the
point in the middle of its bottom edge, which left a loose vertex in every capped run.

## Status (`python3 -m sagekit inventory elves/floodgate`)

| Part | Healthy | Damaged / snow / stonework | Construction (`_A`), really damaged (`_D2`), rubble (`_D3`) |
|---|---|---|---|
| body (`EBFFGate`) | done, rendered, not installed | our body on the variant sheets | `_D2`, `_D3` ours (lifecycle); `_A` left to EA by the lifecycle checks (18.5 % of our area shows its back at frame 350) |
| doors (`EBFFGate_DRCA`) | [`floodgate_doors`](../floodgate_doors/README.md) | | |
