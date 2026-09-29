# Men citadel Ivory Tower (`MenFortressCitadel`, `UPGRADE_IVORY_TOWER`)

Model `GBFITower`, mesh `GBFITOWER`, own texture `GBFortressL.tga` (from `GBFortress1.tga`).
EA's slender tower kept whole, crowned the way the [citadel](../fortress/README.md) crowns its towers.

## What changed

- **Upper shaft**: a machicolated gallery round its top (corbels, black band of silver stars,
  parapet, square merlons); six corbelled bartizans with slate spirelets round the belfry.
- **Middle storey**: pinnacles with steel orbs on the six corner blocks; stone sills and voussoir
  hoods with keystones over the painted windows.
- **Base**: a black star band under a cornice round its top; pinnacles on the six corner buttresses.
- **Spire**: steel ribs, and the citadel's finial (steel mast, gilt orb, ringed spike) to z 196.
- **Banners**: none.

## `citadel_motifs.py`

The citadel's motifs as functions for every add-on (gallery, star band, voussoirs, finial, spire
ribs, gable coping, the seven stars), copied from `fortress/crown.py` and `gate.py`.

## Status

Installed with the Men pack. 402 -> 4,264 triangles (budget 6,000), height 166.3 -> 184.4
(+10.9 %), footprint unchanged, 81/81 checks. Construction, really damaged and rubble are rebuilt
along EA's pieces; the really damaged stump keeps a bartizan fragment on its broken top.
