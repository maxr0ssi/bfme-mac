# Elven mallorn tree (`ElvenMallornTree`)

Model `EBMalTree`, mesh `EBMALTREE` (trunk, roots, branches), own texture `EBMalTreH.tga` (from
`EBMalTree.tga`, cut-out alpha kept). `Tier.STANDARD`. Ships as `EBMalTree2`: Arnor and Amon Sul's
map piece draw `EBMalTree`. Tilted bone, so model axes (`world_space`). EA's leaf cards, talan,
spiral stair, lamp-bearing maiden and torch cards are kept; the bark is repainted silver-grey.

## What changed

- **Stair balustrade**: turned silver balusters every ~1.5 up EA's stair, a rail 2.55 over the boards.
- **Talan edge**: a narrow gold fascia and a hanging leaf fringe.
- **Lanterns**: a crystal-lantern newel either side of the stair's foot, three lantern columns among
  the roots (clear of the stair and the maiden), three big crystal lanterns on gilt rods where EA's
  night-only lamps hang.
- **Night**: 19 lights on the crystals' camera-side facets; EA's three canopy glow cards stay.
- **Banners**: two, from the talan's rail; cloth in `EBHCMalTree2`, an own copy of Arnor's `EBHCMalTree`.

## Status

Installed with the Elven pack. 1,014 -> 11,128 triangles, height and footprint unchanged, 105/105
checks. Construction and damaged derive the new body; rubble is rebuilt along EA's pieces. Really
damaged stays EA's: `MALTREE_PIECE01`'s vertex layout differs from the template's.

## Known limits

- Renders invisible in game (own-copy bug, being fixed).
