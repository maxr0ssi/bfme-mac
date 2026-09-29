# Men stable, level 3 (`V2` of `GBStable_SKN`)

The belfry EA shows from level 3. Chained on `men/stable_level2`
([`levels.py`](../levels.py)); the chain's last link. Own texture `GBVS2` (damaged
`GBVS2D`, snow `GBVS2_snow`).

## What changed

- **Storey**: the two arched windows a face in voussoir surrounds with keystones and sills on
  corbels; a sable frieze of gilt stars under them.
- **Crown**: square merlons along the eave, a corbelled bartizan with a slate spirelet on each
  chamfer; the dome's steel eave band and ribs, a lantern, gilt orb and spike (EA's spike cleared).
- **Shaft**: long and short quoins up its corners. The body's machicolated terrace rings its foot.
- EA's slate stays slate (`VET_TILES`).

## Kept clear

- The windows: nothing stands in one (the level-3 arrows ARROW_01..08 leave through them at z 73.8).
- V2's flag poles and flags (V2FLAG) are untouched.
- `footprint_margin` 0.8: the west bartizans corbel out past V2's box.

## Status

Installed with the Men pack. `V2` 806 -> 6,050 triangles, height 55.0 -> 65.9 (+19.7 %, under the
20 % cap), 105/105 checks. Damaged and rubble carry our V2; really damaged (`GBStable_D2`) stays
EA's for the level meshes (its V2 and the body's piece are painted from different sheets, as the
barracks'); construction stays EA's.
