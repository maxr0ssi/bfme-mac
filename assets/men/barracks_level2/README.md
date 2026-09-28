# Men barracks, level 2 (`V1` of `GBBarracks_SKN`)

The yard wall EA shows from `Upgrade_GondorBarracksLevel2`, chained on the finished barracks
(`base = "men/barracks"`, `assets/men/barracks/levels.py`). Rebuild after `men/barracks`; rebuild
`men/barracks_level3` after this. Own texture `GBVB1` (damaged `GBVB1D`, snow `GBVB1_snow`).

## What changed

- **Gallery** on all four outer faces: corbels, a sable course of silver stars, square merlons
  with capstones.
- **Buttresses**: upright piers every 14 up the battered faces, capped under the corbels; White
  Tree roundels and steel-framed arrow slits in turn between them (south and east).
- **Gate towers**: the two rounded wall ends at the north-east entrance become square battered
  towers with a corbelled crown (sable band, merlons), corner pinnacles, a slate spire with a
  steel mast and gilt orb, a roundel and an arrow slit on each outward face.
- EA's flag pole on the keep's dome is cleared (the body's lantern and spike stand there).
- No cloth, no night lights (a level mesh). All pieces are closed solids (`motifs.closed`): V1
  is a one-sided shell.

## Status

- `V1` 216 -> 12,202 triangles; footprint V1's; 120/120 checks. Awaiting review.
- Lifecycle: construction, damaged and rubble carry our V1; really damaged (`GBBarracks_D2`) stays
  EA's for the level meshes (its V1 and the body's piece are painted from different sheets).
