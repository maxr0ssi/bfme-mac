# Men forge, level 3 (`V2` of `GBBlkSmith_SKN`)

The belfry EA shows from level 3. Chained on `men/forge_level2`
([`levels.py`](../levels.py)). Own texture `GBVF2` (damaged `GBVF2D`, snow `GBVF2_snow`).

## What changed

- **Storey**: a voussoir surround with keystone and a sill on corbels round each of the four
  windows, outside EA's frames. A steel band round the base.
- **Crown**: square merlons along the eave, a pinnacle on each chamfer; the dome's steel eave band
  and ribs, a steel mast, gilt orb and spike (EA's spike cleared).
- EA's slate stays slate (`VET_TILES`).

## Kept clear

- The windows: nothing stands in one (the arrows ARROW_01..04 leave through them at z 65.3).
- `footprint_margin` 1.1: the surrounds' sills stand out of V2's faces, which are its box's edges.

## Status

Installed with the Men pack. `V2` 376 -> 2,136 triangles, height 43.3 -> 48.2 (+11.1 %),
143/143 checks. Construction, really damaged and rubble carry our V2; damaged is derived.
