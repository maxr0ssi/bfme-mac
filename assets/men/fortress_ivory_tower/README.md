# Men fortress Ivory Tower (`MenFortressCitadel`, UPGRADE_IVORY_TOWER)

Staged for review, not installed. Renders: `build/assets/men/fortress_ivory_tower/renders/`; on the
citadel with every upgrade: `build/assets/men/_group_addons/compare_citadel_*.png`; group sheet
`build/assets/men/_group_addons.jpg`.

## What changed

EA's slender tower kept whole, crowned the way the citadel crowns its four towers
(`citadel_motifs.py`, this folder):

- a machicolated gallery round the upper shaft's top (corbels, black band of silver stars,
  parapet, square merlons), six corbelled bartizans with slate spirelets round the belfry
- pinnacles with steel orbs on the middle storey's six corner blocks; stone sills and voussoir
  hoods with keystones over its painted windows
- a black star band under a cornice round the base's top, pinnacles on the six corner buttresses
- steel ribs up the spire, the citadel's finial (steel mast, gilt orb, ringed spike) to z 196

## Fit and status

- `GBFITOWER` 402 -> 4,264 triangles (budget 6,000); height 166.3 -> 184.4 (+10.9 %, the citadel
  grew +10.6 %); footprint unchanged. No banner (see below).
- Checks 81/81 **only with two framework fixes applied outside sagekit** (not in the pipeline yet):
  the tower has no hierarchy, so `checks.snapshot` fails on `arms[0]`, and its mesh has no
  container name, so `W3DFile.cache_entries` files it as `.GBFITOWER` against the game's
  `GBFITOWER` and the cache step stops. Built with the second fixed in a wrapper; see the group report.
- Lifecycle: construction, D2 and D3 rebuilt along EA's pieces; D2's stump keeps a bartizan
  fragment on its broken top (a human look wanted).

## Decisions

- No house-colour banner: an add-on's cloth goes to `GBHCFortress2`, which the citadel draws in
  every state, so it would hang in the air before the upgrade is built.

## `citadel_motifs.py`

The citadel's motifs as functions for every add-on (polygon, cornice, corbel course, gallery,
star band paint, star frieze, White Tree panel, voussoirs with closed backs, finial, spire ribs,
gable coping, the seven stars in an arc). Copied from `fortress/crown.py` and `gate.py`; the
citadel's recipe is not imported.
