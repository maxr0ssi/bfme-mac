# Dwarven archery range, level 2 obelisks (`V1` of `DBArchRnge_SKN`)

Model `DBArchRnge_SKN`, mesh `V1`, own texture `DBArchRngO.tga` (from `dbarchrnge.tga`).
`Tier.STANDARD`. Chained on `dwarves/archery_walls`; build after `archery_range`, `archery_tower`
and `archery_walls`.

## What changed

- **Steles**: each obelisk gets a battered plinth with a bronze course, a stone sleeve over EA's
  shaft with a gold rune belt and a bronze band, and the fortress's stepped corner pyramid with a
  gilded point.

## Kept clear

- EA's south faces lie on the footprint's edge (y -54.14), so the recipe sets
  `footprint_margin = 1.5` (the game's collision comes from the INI's geometry, not the mesh).

## Status

Installed with the Dwarven pack. 24 -> 532 triangles, height 65.19 -> 70.97 (+8.9 %), 266/266
checks. As the chain's last link it ships the model and the damaged `DBArchRnge_D1` for the whole
chain: each link splices its mesh into its base's derived D1. Rebuild the chain in order after
changing any link.
