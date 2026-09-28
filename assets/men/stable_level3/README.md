# Men stable, level 3 (`V2` of `GBStable_SKN`)

The belfry EA shows from level 3, chained on the finished level 2 (`base = "men/stable_level2"`,
`assets/men/barracks/levels.py`). Rebuild after `men/stable_level2`. Own texture `GBVS2` (damaged
`GBVS2D`, snow `GBVS2_snow`).

## What changed

- **Storey**: the two arched windows a face in voussoir surrounds with keystones and sills on
  corbels; a sable frieze of gilt stars under them. Nothing stands in a window (the level-3
  arrows ARROW_01..08 leave through them at z 73.8).
- **Crown**: square merlons along the eave, a corbelled bartizan with a slate spirelet on each
  chamfer; the dome's steel eave band and ribs, a lantern, gilt orb and spike (EA's spike cleared).
- **Shaft**: long and short quoins up its corners. The body's machicolated terrace rings its foot.
- V2's flag poles and flags (V2FLAG) are untouched. EA's slate stays slate (`VET_TILES`).
- No cloth, no night lights (a level mesh). `footprint_margin` 0.8: the west bartizans corbel
  out past V2's box.

## Status

- `V2` 806 -> 6,050 triangles; height +19.7 % (under the 20 % cap); 105/105 checks. Awaiting review.
- Lifecycle: damaged and rubble carry our V2; really damaged (`GBStable_D2`) stays EA's for the
  level meshes (its V2 and the body's piece are painted from different sheets, as the barracks'),
  construction stays EA's.
