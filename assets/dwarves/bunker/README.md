# Dwarven bunker (`DwarvenBunker`, `dwarfbunker.ini`)

Model `DBBunker`, redesigned mesh `DBBBUNKER`, own texture `DBBunkeH.tga` (+ `_NRM`, `_D1`, `_Snow`),
`Tier.STANDARD`. The far-off ground patch `DBBBUNKERG` (painted from `DBStoneA`, which is not
extracted) is left out of the bakes and renders (`bake_hidden`); it is untouched.

## What changed (body, healthy)

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

Nothing is placed at the (-X, +Y) corner, where the multiplayer banner (`DBHCBunker`) hangs.

Footprint unchanged (x -14.37..26.94, y -14.54..16.63), height 65.66 -> 76.26 (+16.1 %, limit
20 %), 659 -> 1,361 triangles. `checks`: 52/52.

## Status (`python3 -m sagekit inventory dwarves/bunker`)

| Part | Healthy | Construction | Damaged / really damaged | Rubble | Snow | LOD M/L |
|---|---|---|---|---|---|---|
| body (`DBBunker`) | built, reviewed in renders, not installed | `DBBunker_A` carries the new body | `DBBunker_D1` / `_D2` carry the new body (own `_D1` sheet) | old | own `_Snow` sheet | old |
| banner (`DBHCBunker`) | old | | | | | |

Known: the painter turns the brown shield panels (with their window slits) into flat dark brown
in this build, with or without the new geometry (seen on an empty design too) - a paint-stack
matter, not the recipe's.
