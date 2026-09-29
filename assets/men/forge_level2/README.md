# Men forge, level 2 (`V1` of `GBBlkSmith_SKN`)

The corner towers and yard walls EA shows from level 2. Chained on `men/forge`
([`levels.py`](../levels.py)). Own texture `GBVF1` (damaged `GBVF1D`, snow `GBVF1_snow`).

## What changed

- **Towers** (four, round EA's corner piers): a corbelled sable band of silver stars under each
  pyramid's eave, pinnacles on its four corners, a steel mast, gilt orb and spike on its apex;
  slit windows on the faces the camera sees and a White Tree roundel on the front towers' yard faces.
- **Yard walls**: along both outer faces two-step corbels, a slab with a sable band of silver
  stars, square merlons with capstones; buttresses below.

## Kept clear

- The smith, the forge bed, the weapon racks and EA's house banner: nothing reaches into the
  yard; the east gallery stops short of the banner's pole.
- `footprint_margin` 1.0: the towers stand on V1's bounding box, so their crowns and windows
  pass it (collision comes from the INI).

## Status

Installed with the Men pack. `V1` 298 -> 8,426 triangles, height 51.9 -> 61.4 (+18.3 %),
143/143 checks. Construction, really damaged and rubble carry our V1; damaged is derived.
