# Dwarven archery range, level 2 yard walls (`V1A` of `DBArchRnge_SKN`)

Model `DBArchRnge_SKN`, mesh `V1A` (shown from `Upgrade_StructureLevel2`), own texture
`DBArchRngW.tga` (from `dbarchrnge.tga`). `Tier.STANDARD`. Chained on `dwarves/archery_tower`;
rebuild after it, and rebuild [`archery_obelisks`](../archery_obelisks/README.md) (`V1`) after this.

## What changed

EA's V1A is four plain battered walls, 16.9 high, round the shooting yard.

- **Coping**: over every ridge, a gold rune band on blue enamel between bronze edges.
- **Chevron crest**: the fortress's stepped chevrons with gilded tips, z 16.95 to 20.2.
- **Plinth**: battered, with a bronze string course, on the faces the footprint allows.
- **Niches**: EA's two plaques (west and south walls) set in stepped niches between pilasters.
- **Banners**: four, two on the south and two on the west outer face; the cloth stays in `V1A`
  in the palette's blue (`house_tags = ()`), since the house model is drawn at every level.

## Kept clear

- The crest stops short of the obelisks, the gallery post (y 27.6) and the hall's corner turret (y -25).
- The west wall's yard-face plinth stops at y 16, where the range's ground ladder stands.

## Status

Installed with the Dwarven pack. 139 -> 1,897 triangles, height 16.92 -> 20.22 (+19.5 %),
266/266 checks. Damaged carries our walls (`also_derived`); construction, really damaged and
rubble are rebuilt along EA's pieces.
