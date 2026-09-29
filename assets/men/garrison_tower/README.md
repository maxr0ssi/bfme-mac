# Men garrison tower (`MenGarrisonTowerExpansion`, variation one)

Model `GBFDOTOWA`, mesh `GBFDOTOWA`, own texture `GBFortressN.tga` (from `GBFortress1.tga`).
EA's gate tower kept whole and crowned the citadel's way (`pad.py`, shared with
[`garrison_tower_b`](../garrison_tower_b/README.md); the tower top from `men/dome.py`).

## What changed

- **Gallery** round the shaft top on the three outward faces: corbels, a black band with silver
  stars, parapet and square merlons (no corbels in front of EA's crest).
- **Gate**: rusticated quoins, moulded imposts, an 11-stone archivolt with a raised keystone,
  portcullis teeth in the arch; pinnacles on the two diagonal buttresses; a moulded side plinth.
- **Belfry**: voussoir hoods and corbelled sills on the windows, slate-capped pinnacles on the
  chamfers; steel eave band and ribs on EA's dome, lantern cupola, gilt orb, steel spike.
- **Banners**: one, on the -Y face; cloth in `GBHCFDOTOWA`.

## Kept clear

- The -X side, on EA's footprint toward the citadel's pad: no gallery, no hoods; only the eave
  band and ribs pass it (`footprint_margin = 0.55`).

## Status

Installed with the Men pack. 430 -> 3,600 triangles, height 83.0 -> 98.5 (+18.7 %), 83/83 checks.
Construction, really damaged and rubble are rebuilt along EA's pieces.
