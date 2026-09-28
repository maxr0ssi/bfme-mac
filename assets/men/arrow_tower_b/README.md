# Men arrow tower b (`MenArrowTowerExpansion`, variation two)

Ships as our own GBFARTOWB2. The tower crowned as variation one (`men/arrow_tower/spire.py`),
here with the gallery all round (the wall frees the -X side) and four bartizans; the one banner on
the shaft's -Y face. On the wall walk (`wall.py`): stepped buttresses, a black band with silver
stars and merlons on both parapets; on the stair-house: archivolt, quoins, imposts, corner
pinnacles and shields (`men/trebuchet/drum.stair_house`).

Blocked on the same framework bug as `arrow_tower`: the embedded animation keeps EA's name
(`A*GBFARTOWB.GBFARTOWB`), so the own-copy name check fails; every other check passes.

## Status

- [x] healthy body designed (draft for Max's review; nothing installed)
- [x] lifecycle: construction, really damaged and rubble rebuilt along EA's pieces (`work/lifecycle.json`)
- [ ] checks pass, renders reviewed (`build/assets/men/arrow_tower_b/renders/compare_*.png`)

368 -> 4574 triangles; height 122.93 -> 140.5 (+14.3 %); checks all but the own-copy name; banners 1.
