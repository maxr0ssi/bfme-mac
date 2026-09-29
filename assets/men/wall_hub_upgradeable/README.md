# Men wall hub upgradeable (`MenWallHubSmallUpgradeable`, and Arnor's)

Model `GBWallUpgrdN`, mesh `OBJECT03`: the plot a wall upgrade replaces, whose tower is the same
mesh as `men/wall_hub`'s `GBWallRmprtN`. Own texture `GBFortressG.tga` (from `GBFortress1.tga`).
Chained on [`men/wall_hub`](../wall_hub/README.md): `WallHubUpgradeable` subclasses its `WallHub`;
rebuild after it.

## What changed

- The hub's redesign, whole: flush parapet with a band of silver stars and merlons, six corner
  bartizans, drum pilasters and window frames, steel ribs, lantern, orb and spike.
- **Banners**: none.

## Status

Installed with the Men pack. 94 -> 2,820 triangles, height 98.1 -> 110.2 (+12.4 %), footprint
unchanged, 50/50 checks. No lifecycle models of its own.

## Known limits

- `GBFORTRESS01`/`02`, the wall stubs either side, stay EA's; a chained recipe could carry the
  segments' crown through them.
