# Men barracks, level 3 (`V2` of `GBBarracks_SKN`)

The belfry storey and the two turrets EA shows from `Upgrade_GondorBarracksLevel3`. Chained on
`men/barracks_level2` ([`levels.py`](../levels.py)); the chain's last link, so its
`gbbarracks_skn.w3d` ships. Own texture `GBVB2` (damaged `GBVB2D`, snow `GBVB2_snow`).

## What changed

- **Belfry storey**: its eight windows in voussoir surrounds with keystones and sills on
  corbels (the level-3 arrows' bones stay clear), a frieze of gilt stars under them, square
  merlons on the eave, a corbelled bartizan with slit windows and a slate spirelet on each
  chamfer; steel ribs, a lantern, gilt orb and spike (to z 123.5) on the dome (EA's spike goes).
- **Turrets**: window surrounds, merlons on the eave, a pinnacle on each chamfer, steel ribs and
  a gilt orb with a spike (EA's spikes go).
- **Paint**: the domes' slate charcoal (`paint.Slate`).
- `footprint_margin = 1.0`: the turrets' outer faces are V2's bounding box; their window
  surrounds stand 0.95 proud.

## Status

Installed with the Men pack. `V2` 1,994 -> 13,160 triangles, height 96.5 -> 100.4 (+4.0 %),
120/120 checks. Construction, damaged and rubble carry our V2; really damaged (`GBBarracks_D2`)
stays EA's, as at level 2.
