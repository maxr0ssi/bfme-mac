# Dwarven postern gate (`DwarvenWallPosternGateSmall`)

Model `DBWallPGN`, mesh `OBJECT01` (the two porches), own texture `DBFortressP.tga` (from the
faction atlas `DBFortress1.tga`). `Tier.STANDARD`. The object also draws the wall segment's model
`DBWallN` (`ModuleTag_DrawWall`), which [`wall_segment`](../wall_segment/README.md) redesigns. Its
house-colour module keeps the default tag `ModuleTag_Draw_HCBanner`, and the wall's module uses
`ModuleTag_Draw_HCWallN`, so the two don't collide.

## What changed

On each porch (both faces of the wall):

- **Door frame:** a stepped pointed frame round EA's shouldered doorway: two recessed rings with
  the triangle frieze and bronze reveals, then a frame slab. EA's triangle-frieze reveal is kept.
  The frame's point rises over the doorway's flat top, so a small tympanum shows there.
- **Crown:** a corbelled cornice with the hexagon frieze, then a stepped gable (bronze step,
  triangle-frieze tier, stone point, top z 48.3).
- **Corner blocks:** the front blocks carry stepped pyramids with gilded points.
- **Banners:** a pole on each low side block; cloth in `DBHCWallPGN`.

## Kept clear

- The wall passes through x +-8.3 up to z 53 (coping 57, chevrons 63.6). Nothing new sits inside
  |x| < 8.3, and everything stays under the walkway (the +20 % limit is z 48.96). Faces against the
  wall are closed: the wall is another model, and the sky check cannot see it.

## Status

Installed with the Dwarven pack. 156 -> 1,280 triangles, height 40.78 -> 48.30 (+18.4 %), 79/79
checks. Construction and damaged derive the new body; really damaged and collapse are rebuilt
along EA's pieces.
