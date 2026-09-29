# Dwarven bunker (`DwarvenBunker`, `dwarfbunker.ini`)

Model `DBBunker`, mesh `DBBBUNKER`, own texture `DBBunkeH.tga` (from `DBBunker.tga`).
`Tier.STANDARD`. The far-off ground patch `DBBBUNKERG` (painted from `DBStoneA`, which is not
extracted) is left out of the bakes and renders (`bake_hidden`); it is untouched.

## What changed

The squat guard tower keeps its body, its shield-panel head, its corner fins, its stepped door
frame with the gabled canopy and its entrance steps. Added:

- **Crown:** a parapet slab on each head side (overhanging the shield panels by 0.95, carrying the
  hexagon frieze) with a stepped triangle gable in its middle; a stepped pyramid (the fortress's
  corner motif at 0.7 scale) on each corner fin.
- **Roof:** the low roof pyramid continues as a stepped crown: rune tier, bronze cornice,
  triangle-frieze tier, plain tier and a gilded point (the new highest point, z 76.3).
- **Door:** two pointed rings stepping forward around the original frame and canopy (triangle
  frieze on the inner ring, runes on the outer, bronze reveals). The door, frame and steps are not
  covered; the jambs stand beside the steps.
- **Shaft:** a rune belt around the octagonal shaft just under its flared corners.
- **Plinth:** a battered plinth with a bronze string course along the long -Y side (the RTS
  camera's side), flush with the door wall.
- **Banners:** two, down the +X and -Y shield panels; cloth in `DBHCBunker`.

## Kept clear

- The (-X, +Y) corner, where EA's house banner hangs.

## Status

Installed with the Dwarven pack. 659 -> 1,457 triangles, height 65.66 -> 76.26 (+16.1 %), 85/85
checks. Construction and damaged derive the new body; really damaged and rubble are rebuilt along
EA's pieces.

## Known limits

- The painter turns the brown shield panels (with their window slits) flat dark brown, with or
  without the new geometry: a paint-stack matter, not the recipe's.
