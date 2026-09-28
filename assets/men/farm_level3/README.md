# Men farm, level 3 (`V2` of `GBFarm_SKN`)

Draft for review, not installed. Chained on [`farm_level2`](../farm_level2/README.md); the
chain's last link, so its `gbfarm_skn.w3d` is the one that ships. Renders:
`build/assets/men/farm_level3/renders/`.

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

## Fit and status

- `V2` 341 -> 6,449 triangles; footprint EA's; height +6.9 % (the chimney pots); all checks pass. The construction
  model is not rebuilt by this link (below the lifecycle checks' standard at frame 999); the
  world-builder model carries V1 and V2.
- Own texture `GBFarP`; damaged state `GPVetD`. No cloth, no lights.
- EA's walls are single planes: every face kept (`prodkit.closed`).
