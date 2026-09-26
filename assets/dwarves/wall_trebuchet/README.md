# Dwarven wall trebuchet bastion (`DwarvenWallCatapultSmall`)

Model `DBWallTrebN`, redesigned mesh `DBWALLTREBN`, `Tier.STANDARD`, own textures
`DBFortressJ.tga` / `DBFortressJ_NRM.tga` (+ `_D`, `_snow`, `_U`). `P1` (the flat platform card
under the floor) is untouched and left out of the bakes. The trebuchet itself is a separate
object that stands on the round platform.

## What changed (body, healthy)

- **Rim:** chevron merlons (stepped-triangle tops, bronze step) sit on the rim's outer 2.4. There
  are two on each angled face and one on each wall face, clear of the join. Each prow tip has a
  stepped pyramid with a gilded point. Nothing enters the platform (z 50.1): the trebuchet keeps
  its floor.
- **Wall joins:** the wall runs along Y and meets the wall faces (y +-22.5) at x +-8.3. Over each
  join there is a pier on the rim, within y 19.0..22.5 (the platform ends at 18.7). It has a
  hexagon-frieze block, a bronze cornice, a triangle-frieze tier and a stone point at z 63.4. It
  takes the wall segment's coping (to 57) and chevrons (to 63.6) instead of leaving them to end in
  the air over the rim (53.1).
- **Banners:** a pair of Erebor-blue banners on each angled face, either side of EA's relief
  panel, hung under the band. Their cloth is in `DBHCWallTrebN`.
- EA's carved panels, the triangle-frieze band and the prow emblems are kept.

Footprint unchanged, height 53.0 -> 63.4 (+19.5 %), 288 -> 1,324 triangles. `checks`: 51/51.

Not verified: the trebuchet's swing against the merlons. The merlons stand 6 above the rim and
the piers 10.3, both on the rim's outer edge. Worth a look in game.

## Status

| Part | Healthy | Construction (`_A`) | Damaged (`_D1`) | Really damaged / rubble (`_D2`, `_D3`) | Snow / stonework |
|---|---|---|---|---|---|
| body (`DBWallTrebN`) | built, rendered, not installed | derived: our body | derived: our body, own `_D` sheet | old | own `_snow` / `_U` sheets |
