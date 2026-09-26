# Dwarven castle-wall hub (`DwarvenCastleWallHub`)

Model `DBWallRmprt`, redesigned mesh `GBWALLRAMPART`, `Tier.STANDARD`, painted from the faction
atlas onto `DBWalR.tga` (EA's sheet `DBWall.tga` is a placeholder; no face samples it: see
[oldwall_segment](../oldwall_segment/README.md)).

## What changed (body, healthy)

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
  on each diagonal of the platform; the cloth goes to our house-colour model `DBHCWallRmprt`
  (Draw tag `ModuleTag_Draw_DBHCWallRmprt`).

Footprint EA's (x -61.10 .. 57.08, y +-59.09); 82 -> 3,682 triangles. `checks`: 29/29 pass.

**Height 53.26 -> 74.13 (+39 %, `max_z_growth = 0.40`).** EA's drum is only as high as the
walls' walkway; with the default 20 % the crown would stop at 64.2, level with the walls'
parapet. The new walls' hub rises 12 above its walls' walkway; this one 22.5 (it is 2.3x wider).

## Status

| Part | Healthy | Other states |
|---|---|---|
| body (`DBWallRmprt`) | done, rendered, not installed | none exist (no condition states, no `_A`/`_D*` models) |
