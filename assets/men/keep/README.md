# Men keep (`GondorKeep`, the battle tower)

Model `GBBtlTwrs`, redesigned mesh `OBJ0`, `Tier.STANDARD`, own sheet `GBBtlTwH.tga` (+ `_NRM`,
`_D`, `_snow`). Shares `tower.py` with the sentry tower.

## What changed

EA's tower stays whole (shaft, pilasters, lancet windows, painted statue niches, frieze, ribbed
dome, porch) and is crowned like the citadel's towers:

- **Crown** (`tower.py`): corbels under the frieze, a black band of silver stars on it, a parapet of
  square merlons, a small pinnacle over each fold, six corbelled bartizans with slate spirelets on
  the pilasters. The dome is **slate**, as on the citadel. EA's pale tiles would otherwise recolour
  to white stone, so the sheet's dome panel is hinted as tiles (`DOME_TILES`). The dome also gets
  six steel ribs, a lantern cupola, a gilt orb and a steel spike.
- **Shaft**: sills, colonnettes and pointed hoods with gilt knobs on the 12 lancets. String courses
  at 27.6, 59.8 and 80.9 collar the pilasters, and plinth blocks stand at the pilasters' feet.
- **Porch**: a voussoir archivolt, a black tympanum with the White Tree, raking cornices, a
  winged-helm crest, and buttress piers with pinnacles.
- **Heraldry**: 2 house-colour banners on the pilasters flanking the porch (cap 2). White Tree
  shields sit on the other four pilasters. Both stay clear of EA's statue niches, which are painted
  on every fold at z 30..46.6.

## Status

- [x] healthy body designed; checks 86/86 (footprint inside, height 115.7 -> 133.7, +15.5 %;
      1022 -> 8177 triangles)
- [x] night: EA's `N_WINDOW` panes (63.25..78.03) stay clear and lit (`renders/night/`); nothing
      stands in front of them
- [x] lifecycle: construction, really damaged and rubble are rebuilt; damaged is derived
- [ ] banners show only after `sagekit house men` (integration). Renders before that show the rod
      and tree without cloth.
- [ ] Max's review. Known: in the really-damaged `_D` variant, the dome panels' edges are lighter
      than in the healthy model (EA's damaged sheet carried over as a ratio).
