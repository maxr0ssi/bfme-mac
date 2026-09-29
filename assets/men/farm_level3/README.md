# Men farm, level 3 (`V2` of `GBFarm_SKN`)

Chained on `men/farm_level2` ([`levels.py`](../levels.py)); the chain's last link, so its
`gbfarm_skn.w3d` ships. Own texture `GBFarP` (damaged state `GPVetD`).

## What changed

EA's V2 raises the cottage by a storey with small windows under a steeper thatch and the chimney.
Added:

- a sable band with gilt stars round the storey at its floor line;
- quoins up the storey's four corners;
- pediments on consoles over its ten windows;
- the White Tree in a steel ring high on the south and north gables;
- kneelers on the gables' corners under the eaves;
- a coping and two chimney pots on EA's stack;
- EA's thatch keeps its straw colour (`prodkit.props_layer`).

EA's walls are single planes: every face kept (`prodkit.closed`).

## Status

Installed with the Men pack. `V2` 341 -> 6,449 triangles, footprint EA's, height 45.1 -> 48.2
(+6.9 %, the chimney pots), 104/104 checks. The world-builder model carries V1 and V2. Damaged,
really damaged and rubble stay EA's (no body pieces of ours).

## Known limits

- The construction model is not rebuilt by this link: it falls below the lifecycle checks'
  standard at frame 999.
