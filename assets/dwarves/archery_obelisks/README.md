# dwarves/archery_obelisks

The archery range's level-2 obelisks (mesh `V1` of `DBArchRnge_SKN`), chained on
`dwarves/archery_walls` (`base`): each obelisk becomes a stele - battered plinth with a bronze
course, a stone sleeve over EA's shaft with a gold rune belt and a bronze band, and the fortress's
stepped corner pyramid with a gilded point.

EA's south faces lie on the model's footprint edge (y -54.14), so the recipe sets
`footprint_margin = 1.5` (the game's collision comes from the INI's geometry, not the mesh).
Build after `archery_range`, `archery_tower` and `archery_walls`.

As the chain's last link it ships the model and the damaged `DBArchRnge_D1` for the whole chain:
each link splices its mesh into its base's derived D1 (range, storey, walls, steles, each on its
own `_D` sheet). Rebuild the chain in order after changing any link.
