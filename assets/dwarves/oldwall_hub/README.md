# Dwarven castle-wall hub (`DwarvenCastleWallHub`)

Model `DBWallRmprt`, mesh `GBWALLRAMPART`, own texture `DBWalR.tga` (no normal map), painted from
the faction atlas `DBFortress1.tga`. `Tier.STANDARD`. EA's sheet `DBWall.tga` is a placeholder; no
face samples it (see [oldwall_segment](../oldwall_segment/README.md)).

## What changed

EA's stand-in is a regular twelve-sided drum about (-2.01, 0): circumradius 51.17 to z 30.83,
then an upper drum overhanging to 59.09 up to a flat platform at 53.52. Its faces are removed
and the hub rebuilt with the new wall hub's vocabulary at this size:

- **Drum:** battered plinth, 36 three-step corbels carrying the overhang (a machicolation ring),
  upper drum, a rune band with Erebor-blue enamel, the walls' bronze drip band and coping (top 57).
- **Parapet:** the fortress's `chevron_parapet` on all twelve sides (56.6 .. 63.6, the walls'),
  slab fronts flush with the coping face.
- **Corners:** a stepped block with a gilded point (to 69.4) on every other vertex.
- **Crown:** a twelve-sided stepped crown in the middle of the platform (rune belt, bronze
  cornice, triangle frieze, two plain tiers, gilded point at 74.4).
- **Banners:** one (7 x 12.4) on each diagonal upper face under the rune band, and a banner pole
  on each diagonal of the platform; cloth in `DBHCWallRmprt` (Draw tag
  `ModuleTag_Draw_DBHCWallRmprt`).

## Status

Installed with the Dwarven pack. 82 -> 3,682 triangles, height 53.25 -> 74.13 (+39.2 %,
`max_z_growth = 0.40`), 32/32 checks. EA's drum is only as high as the walls' walkway; with the
default 20 % the crown would stop at 64.2, level with the walls' parapet. The object has no other
condition states and no `_A`/`_D*` models.
