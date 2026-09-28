# Men barracks, level 3 (`V2` of `GBBarracks_SKN`)

The belfry storey and the two turrets EA shows from `Upgrade_GondorBarracksLevel3`, chained on
level 2 (`base = "men/barracks_level2"`). The chain's last link: its `gbbarracks_skn.w3d` ships.
Own texture `GBVB2` (damaged `GBVB2D`, snow `GBVB2_snow`).

## What changed

- **Belfry storey**: its eight windows in voussoir surrounds with keystones and sills on
  corbels (the level-3 arrows' bones stay clear), a frieze of gilt stars under them, square
  merlons on the eave, a corbelled bartizan with slit windows and a slate spirelet on each
  chamfer; steel ribs, a lantern, gilt orb and spike (to z 123.5) on the dome (EA's spike goes).
- **Turrets**: window surrounds, merlons on the eave, a pinnacle on each chamfer, steel ribs and
  a gilt orb with a spike (EA's spikes go).
- `footprint_margin = 1.0`: the turrets' outer faces are V2's bounding box; their window
  surrounds stand 0.95 proud.

## Status

- `V2` 1,994 -> 13,160 triangles; height +4 %; 120/120 checks. Awaiting review.
- The domes' slate charcoal (`paintkit.Slate`). Really damaged (`GBBarracks_D2`) stays EA's.
