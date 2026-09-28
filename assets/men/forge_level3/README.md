# Men forge, level 3 (`V2` of `GBBlkSmith_SKN`)

The belfry EA shows from level 3, chained on the finished level 2 (`base = "men/forge_level2"`,
`assets/men/barracks/levels.py`). Rebuild after `men/forge_level2`. Own texture `GBVF2` (damaged
`GBVF2D`, snow `GBVF2_snow`).

## What changed

- **Storey**: a voussoir surround with keystone and a sill on corbels round each of the four
  windows, outside EA's frames; nothing stands in a window (the arrows ARROW_01..04 leave
  through them at z 65.3). A steel band round the base.
- **Crown**: square merlons along the eave, a pinnacle on each chamfer; the dome's steel eave band
  and ribs, a steel mast, gilt orb and spike (EA's spike cleared).
- No cloth, no night lights (a level mesh). EA's slate stays slate (`VET_TILES`).
  `footprint_margin` 1.1: the surrounds' sills stand out of V2's faces, which are its box's edges.

## Status

- `V2` 376 -> 2,136 triangles; height +11.1 %; 143/143 checks. Awaiting review.
- Lifecycle: construction, really damaged and rubble carry our V2; damaged derived.
