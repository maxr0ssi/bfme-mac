# Men trebuchet tower b (`MenTrebuchetExpansion`, variation two)

Variation one's drum (`men/trebuchet/drum.py`, shifted +0.25 in x) with the band and merlons all
round the drum and along the platform block, pinnacles over the prow, the drum's shoulders and the
block's end; the stair-house gets an archivolt with quoins, imposts and keystone crest round its
door, corner pinnacles and White Tree shields (`drum.stair_house`, shared with `arrow_tower_b`).

Decisions: the archivolt stays under the house's barrel line (the stones' backs are open).
GBFTRTOWB_D2 failed the open-backs check with the default pose (3.4 %); `lifecycle` builds it at
EA's rest pose with tolerance 3 (0.94 %). No banners. Shipped models: GBFTRTOWB and its _A, _D2,
_D3 only.

## Status

- [x] healthy body designed (draft for Max's review; nothing installed)
- [x] lifecycle: construction, really damaged and rubble rebuilt along EA's pieces (`work/lifecycle.json`)
- [x] checks pass, renders reviewed (`build/assets/men/trebuchet_b/renders/compare_*.png`)

206 -> 3766 triangles; height 74.65 -> 76.98 (+3.1 %); checks pass; banners 0.
