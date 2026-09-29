# Dwarven fortress wall hub (`DwarvenWallHubSmallExpansion`)

Model `DBGFWHub` (drawn by `dwarvenfortress.ini`: the bastion the fortress raises at a corner when
the wall-hub expansion is bought), mesh `DBWALLRMPRTN`, own texture `DBFortressL.tga` (from the
faction atlas `DBFortress1.tga`). `Tier.STANDARD`.

EA's mesh is the wall hub's hexagon (`DBWallRmprtN`) plus a short wall run out of its west corner
into the fortress (x -45.03 .. the corner, faces at |y| 8.0, walk at 52.21) and a rock bank along
that run's foot (to x -56.52). The recipe subclasses [`wall_hub`](../wall_hub/README.md).

## What changed

- **Hexagon:** the wall hub's design whole (coping and chevron parapet, corner blocks, crown,
  banners); the two banners beside the west corner move 2.5 along their faces, away from the run.
- **West run:** the wall segments' coping and chevron parapet on both faces (the coping's inner
  foot dropped to the run's lower walk), the slabs stopping at the hexagon's parapet; a banner
  (5 x 14) on each face over the rock bank.
- **Banners:** six; cloth in `DBHCGFWHub` (Draw tag `ModuleTag_Draw_HCGFWHub`).

## Status

Installed with the Dwarven pack. 178 -> 1,704 triangles, height 63.22 -> 75.40 (+19.3 %), 91/91
checks. Damaged derives the new body; construction, really damaged and rubble are rebuilt along
EA's pieces.
