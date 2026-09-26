# Dwarven castle-wall tower (`DwarvenCastleWallTower`)

EA's object draws Gondor's placeholder `GBWallTwr` (a cylinder labelled "Men Wall Tower" on
Gondor's castle-wall section), which Men and Arnor draw too. Ours is an **own copy**
(`sagekit/owncopy.py`): `own_model = "DBWallTwr2"`, so the Dwarven object's Draw module is
repointed and Gondor's model stays EA's. Redesigned mesh `GBWALLGATE`; `replaces` GBWALLUPGRD
(the wall section) and CYLINDER01 (the label), which are dropped from our copy. Painted from the
faction atlas onto `DBWalT.tga`; `Tier.STANDARD`. EA's unused `DBWallTwr` is filed in BFME2's
asset cache with another layout, so that name is not free.

## What changed (body, healthy)

- **Wall and stairs** (`oldwall_segment/upgrade.py`): the old castle wall's section at EA's
  walkway (53.59) along |y| 28.2 .. 99.5, a statue pilaster and two banners per face and side,
  and a Dwarven stair down each of EA's ramps (to |y| 140.86).
- **Bastion:** EA's middle block (x +-38.02, rim to 42.35, y +-24) in the section's profile,
  chevrons on its rim and returns, stepped pyramids on the outer corners.
- **Upper tower** (x +-24, y +-17) from the bastion's platform: a rune belt, two banners on each
  outer face, corbels under a rune band, the drip band and coping, chevrons all round, corner
  pyramids, and wall_tower's stepped rune roof with a gilded point (108.4) in the middle of the
  fighting platform (z 90).
- **Kept clear:** EA's arrow bones `ARROW_01..12` (z 95.5, square +-11.2) stand on that platform,
  inside the parapet and outside the roof (half 9.4). P1 / R1 / R2 are EA's (hidden cards;
  `bake_hidden`).

House colour: 12 banners -> `DBHCWallTwr2` (Draw tag `ModuleTag_Draw_DBHCWallTwr2`).
Footprint inside EA's (x +-42.35, y +-140.86); height 100.09 -> 108.45 (+8.4 %, the limit counts
EA's cylinder); 200 -> 6,974 triangles (target 12 -> 6,974). `checks`: 51/51.

## Status

| Part | Healthy | Other states |
|---|---|---|
| body (`DBWallTwr2`, from `GBWallTwr`) | done, rendered, not installed | none exist (no condition states, no `_A`/`_D*` models) |
