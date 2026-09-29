# Dwarven archery range (`DwarvenArcheryRange`)

Model `DBArchRnge_SKN` (skinned, skeleton `DBArchRnge_SKL`), mesh `ARCHERYRANGE` (hall, tower base,
gallery, tower posts), own texture `dbarchrngH.tga` (from `dbarchrnge.tga`). `Tier.STANDARD`.
The upgrades are chained on this model: [`archery_tower`](../archery_tower/README.md) (`V2`),
[`archery_walls`](../archery_walls/README.md) (`V1A`), [`archery_obelisks`](../archery_obelisks/README.md) (`V1`).

## What changed

- **Roof**: EA's shingles inside a stepped stone roof: gold rune eave course, five tiers, a hexagon
  ridge with four gilded chevrons.
- **South gable**: crow-stepped, with a battered corner turret at each foot.
- **Hall walls**: battered plinth with a bronze course, pilasters between the windows, a hexagon cornice.
- **East gatehouse**: EA's rune portal flanked by two battered pylons under a stepped crown; the
  door opening stays clear.
- **Tower crown**: a battered ring with a rune belt over EA's hexagon cornice; stepped gables east,
  north and south. Each timber post rises out of a stone bastion.
- **Gallery**: chevron parapets with gilded tips, a rune fascia, a corbel table.
- **Banners**: five (two on the tower's east face, one on the south wall, two poles flanking the
  gatehouse); cloth in `DBHCArchRnge`.

## Kept clear

- The archer's line of fire over the south gallery edge (z 34, west of x -15.5); nothing new on the deck.
- Both ladders: `ARCHERYRANGE`'s (tower west face, y 31-40) and `V2`'s (y 40.6-49.7).
- `V2`'s storey starts at z 80, above the crown's finials (z 71.8).

## Status

Installed with the Dwarven pack. 861 -> 3,961 triangles, height 77.35 -> 77.35 (+0 %), 265/265
checks, 13 night lights. Damaged derives the new body; construction, really damaged and rubble are
rebuilt along EA's pieces. `archery_obelisks`, the chain's last link, ships the model.

## Known limits

- `add_solids` fans every polygon from its first point, so a non-convex face comes out wrong; this
  recipe caps no non-convex profile.
