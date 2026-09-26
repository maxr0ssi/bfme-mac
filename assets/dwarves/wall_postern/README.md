# Dwarven postern gate (`DwarvenWallPosternGateSmall`)

Model `DBWallPGN`, redesigned mesh `OBJECT01` (the two porches), `Tier.STANDARD`, own textures
`DBFortressP.tga` / `DBFortressP_NRM.tga` (+ `_D`, `_snow`, `_U`). The object also draws the wall
segment's model `DBWallN` (`ModuleTag_DrawWall`), which `wall_segment` redesigns. Its house-colour
module keeps the default tag `ModuleTag_Draw_HCBanner`, and the wall's module uses
`ModuleTag_Draw_HCWallN`, so the two don't collide.

## What changed (body, healthy)

On each porch (both faces of the wall):

- **Door frame:** a stepped pointed frame round EA's shouldered doorway: two recessed rings with
  the triangle frieze and bronze reveals, then a frame slab. EA's triangle-frieze reveal is kept.
  The frame's point rises over the doorway's flat top, so a small tympanum shows there.
- **Crown:** a corbelled cornice with the hexagon frieze, then a stepped gable (bronze step,
  triangle-frieze tier, stone point, top z 48.3).
- **Corner blocks:** the front blocks carry stepped pyramids with gilded points.
- **Banner poles:** a pole stands on each low side block. Their cloth is in `DBHCWallPGN`.

## Where the wall meets it

The wall passes through x +-8.3 up to z 53 (coping 57, chevrons 63.6). The porches stand against
both its faces. Nothing new sits inside |x| < 8.3, and everything stays under the walkway (the
+20 % limit is z 48.96). Faces against the wall are closed: the wall is another model, and the
sky check cannot see it.

Footprint unchanged, height 40.8 -> 48.3 (+18.4 %), 156 -> 1,280 triangles. `checks`: 44/44.

## Status

| Part | Healthy | Construction (`_A`) | Damaged (`_D1`) | Really damaged / collapse (`_D2`, `_D3`) | Snow / stonework |
|---|---|---|---|---|---|
| body (`DBWallPGN`) | built, rendered, not installed | derived: our body | derived: our body, own `_D` sheet | old | own `_snow` / `_U` sheets |
| wall (`DBWallN`) | `wall_segment` | | | | |
