# Men arrow tower (`MenArrowTowerExpansion`, variation one)

Ships as our own GBFARTOWA2 (Blue Mountains draws GBFARTOWA). EA's tower kept whole and crowned
from `spire.py` (shared with `arrow_tower_b`; gallery, plinth and banner from
`men/garrison_tower/pad.py`, eave band and ribs from `men/wall_hub/dome.py`): machicolated gallery
with silver stars on the three outward faces, corbelled bartizans with slate spirelets on the two
front corners (on the buttresses' heads), pilasters up the belfry's chamfers, pinnacles on the
dome's eave, steel ribs, lantern, gilt orb and spike; plinth; one banner on the -Y face.

Blocked on a framework bug (reported, not fixed here: the framework is frozen): the own-copy check
`every object name carries GBFARTOWA2` fails because `sagekit/formats/w3d.py rename_model` renames
the hierarchy, meshes and HLOD but not the embedded animation (`A*GBFARTOWA.GBFARTOWA` stays EA's
name, so its cache record would collide with EA's). Every other check passes; renders made with
`--from render`. `footprint_margin = 0.3` (the dome's eave lies on the footprint at -X).

## Status

- [x] healthy body designed (draft for Max's review; nothing installed)
- [x] lifecycle: construction, really damaged and rubble rebuilt along EA's pieces (`work/lifecycle.json`)
- [ ] checks pass, renders reviewed (`build/assets/men/arrow_tower/renders/compare_*.png`)

218 -> 2628 triangles; height 93.62 -> 109.0 (+16.4 %); checks 81/82 (the own-copy name); banners 1.
