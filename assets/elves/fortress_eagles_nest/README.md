# Elven fortress eagle's nest (`ElvenCitadel`, `ModuleTag_EaglesNestDraw`)

Model `EBFENest`, mesh `EBFENEST1`, own texture `EBFortresJ.tga` (from `EBFortress.tga`).
`Tier.STANDARD`. The pillar in the [fortress](../fortress/README.md)'s courtyard that carries the
Great Eagle's perch. EA's pillar is kept whole; the work is on its head, over the mallorn canopy
(z 99) and the tree-houses (z 122.9). EA's eagle (`EBFE`) is not part of this recipe.

## What changed

- **Arch frames**: a silver frame with a slate reveal round each of EA's four head recesses.
- **Sill band and cornice**: silver, round the head's foot (z 102.1) and under the perch (z 122.3..124.25).
- **Crystal lanterns**: the citadel's ring lantern, smaller, on each cornice corner (to z 134.7).
- **Necking**: a silver astragal where the shaft flares into the head (z 94.8) and a ring of eight
  gilt leaves hanging from it.
- **Shaft foot**: a knotwork band between gilt beads (z 52.5..54.6), silver collars on the two steps.
- **The eagle**: `atlas.py` keeps EA's eagle (painted on `EBFortress.tga`) out of the sheet recolour.
- **Banners**: none; the citadel's `EBHCFortress` keeps its own four.

## Kept clear

- The eagle, from z 137.2, and the perch's roots and beams along the axes.

## Status

Installed with the Elven pack. 718 -> 3,984 triangles, height unchanged (141.0, EA's perch stays the
top), footprint unchanged, 86/86 checks. Construction, really damaged and rubble are rebuilt along
EA's pieces; damaged is a texture swap.
