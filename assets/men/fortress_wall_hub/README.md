# Men citadel wall hub (`MenWallHubSmallExpansion`)

Model `GBGFWHub`, mesh `OBJECT03`, own texture `GBFortressK.tga` (from `GBFortress1.tga`). EA paints
this mesh with `GBWall_NRM`, so the recipe's `sheet_atlas` is the faction atlas with that normal map,
and its own normal map is `GBWalK_NRM.tga` (the same name length: W3D patches names in place).
Chained on [`men/wall_hub`](../wall_hub/README.md): the recipe subclasses its `WallHub`; rebuild after it.

## What changed

- The free-standing hub's design, whole: parapet with silver stars and merlons, six bartizans,
  drum pilasters and window frames, ribbed dome, lantern, orb and spike.
- `BOX01`, the wall stub toward the citadel, stays EA's; the hub's -X bartizan rises from its top.
- **Banners**: none.

## Status

Installed with the Men pack. 94 -> 2,820 triangles, height 98.1 -> 110.2 (+12.4 %), 84/84 checks.
Construction and damaged are derived from the new body; really damaged and rubble are rebuilt.
