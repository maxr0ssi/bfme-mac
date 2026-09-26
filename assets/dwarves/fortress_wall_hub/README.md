# Dwarven fortress wall hub (`DwarvenWallHubSmallExpansion`)

Model `DBGFWHub` (drawn by `dwarvenfortress.ini`: the bastion the fortress raises at a corner when
the wall-hub expansion is bought), redesigned mesh `DBWALLRMPRTN`, `Tier.STANDARD`, painted from
the faction atlas onto `DBFortressL.tga` / `_NRM` (+ `_D`, `_Snow`, `_U` variants).

EA's mesh (178 triangles) is the wall hub's hexagon (`DBWallRmprtN`, 138) plus a short wall run out
of its west corner into the fortress (x -45.03 .. the corner, faces at |y| 8.0, walk at 52.21) and
a rock bank along that run's foot (to x -56.52). The recipe subclasses `dwarves/wall_hub`:

- **Hexagon:** the wall hub's design whole (coping and chevron parapet, corner blocks, crown,
  banners); the two banners beside the west corner move 2.5 along their faces, away from the run.
- **West run:** the wall segments' coping and chevron parapet on both faces (the coping's inner
  foot dropped to the run's lower walk), the slabs stopping at the hexagon's parapet; a banner
  (5 x 14) on each face over the rock bank. The cloth goes to our house-colour model `DBHCGFWHub`
  (Draw tag `ModuleTag_Draw_HCGFWHub`).

Footprint unchanged, height 63.2 -> 75.4 (+19.3 %), 178 -> 1,704 triangles. `checks`: 41/41.

| Part | Healthy | Damaged (`_D1`) / snow / stonework | Construction (`_A`), really damaged, rubble (`_D2`, `_D3`) |
|---|---|---|---|
| body (`DBGFWHub`) | built, rendered, **awaiting review** | derived: our body on the variant sheets | the lifecycle framework's (not built here) |
