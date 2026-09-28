# Men garrison tower (`MenGarrisonTowerExpansion`, variation one)

EA's gate tower kept whole and crowned the citadel's way (`pad.py`, shared with
`garrison_tower_b`; the tower top from `men/wall_hub/dome.py`):

- machicolated gallery round the shaft top on the three outward faces: corbels, a black band
  with silver stars (StarBand), parapet and square merlons (no corbels in front of EA's crest)
- gate: rusticated quoins, moulded imposts, an 11-stone archivolt with a raised keystone,
  portcullis teeth in the arch; pinnacles on the two diagonal buttresses
- belfry: voussoir hoods and corbelled sills on the windows, slate-capped pinnacles on the
  chamfers; steel eave band and ribs on EA's dome, lantern cupola, gilt orb, steel spike
- moulded plinth on the side faces; one house-colour banner on the -Y face

Decisions: the -X side lies on EA's footprint (toward the citadel's pad), so the gallery wraps
three faces and the -X belfry face has no hoods; `footprint_margin = 0.55` lets the eave band and
ribs pass that edge. Shipped models: GBFDOTOWA and its _A, _D2, _D3 only (variation one).

## Status

- [x] healthy body designed (draft for Max's review; nothing installed)
- [x] lifecycle: construction, really damaged and rubble rebuilt along EA's pieces (`work/lifecycle.json`)
- [x] checks pass, renders reviewed (`build/assets/men/garrison_tower/renders/compare_*.png`)

430 -> 3788 triangles; height 83.0 -> 98.5 (+18.7 %); checks 83/83; banners 1.
