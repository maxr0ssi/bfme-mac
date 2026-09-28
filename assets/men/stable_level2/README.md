# Men stable, level 2 (`V1` of `GBStable_SKN`)

The paddock wall and gate arch EA shows from level 2, chained on the finished stable
(`base = "men/stable"`, `assets/men/barracks/levels.py`). Rebuild after `men/stable`; rebuild
`men/stable_level3` after this. Own texture `GBVS1` (damaged `GBVS1D`, snow `GBVS1_snow`).

## What changed

- **Gallery** along both curved walls' outer faces: two-step corbels, a sable band of silver
  stars, square merlons with capstones on the outer top edge.
- **Faces**: buttresses at the ends of each run, a White Tree roundel in the middle of each long run.
- **Gate arch**: a keystone on both faces of the crown, a winged helm crest on its top,
  pinnacles over the piers, moulded bands round both legs.
- EA's iron gate leaves and the yard (horse walker, the walking horse) are untouched: nothing
  reaches inside the walls. EA's slate stays slate (`VET_TILES`).
- No cloth, no night lights (a level mesh). All pieces closed (`motifs.closed`): V1 is a
  one-sided shell. `footprint_margin` 0.3: the merlons' capstones on the outer top edge pass V1's
  box (set by EA's flared foot) by up to 0.3.

## Status

- `V1` 354 -> 3,588 triangles; 120/120 checks. Awaiting review.
- Lifecycle: damaged, really damaged and rubble carry our V1; construction (`GBStable_A`) stays
  EA's (see the stable's README).
