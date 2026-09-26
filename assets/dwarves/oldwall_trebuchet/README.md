# Dwarven castle-wall trebuchet platform (`DwarvenCastleWallCatapult`)

EA's object draws Gondor's placeholder `GBWallTreb` (Gondor's castle-wall section with its middle
block), which Men and Arnor draw too. Ours is an **own copy** (`sagekit/owncopy.py`):
`own_model = "DBWallTreb2"`; redesigned mesh `GBWALLGATE`, `replaces` GBWALLUPGRD (dropped from our
copy). Painted from the faction atlas onto `DBWalC.tga`; `Tier.STANDARD`.

## What changed (body, healthy)

- **Wall and stairs** as the tower's (`oldwall_segment/upgrade.py`).
- **Bastion:** EA's middle block (x +-38.02, rim to 42.35, y +-24) in the section's profile:
  plinth, corbels, rune band, drip band, coping, chevrons on the rim and returns, stepped
  pyramids on the outer corners, two banners on each front.
- **Kept clear:** the platform (x +-38, y +-24 at 53.59) is open for the catapult the object
  creates at (0, 0, 52) (`OCL_DwarvenCatapultUpgrade`). Not verified: the catapult's swing
  against the rim chevrons (6 over the platform, as the new walls' trebuchet bastion).

House colour: 12 banners -> `DBHCWallTreb2`. Footprint inside EA's; height 64.75 -> 65.44
(+1.1 %); 128 -> 5,140 triangles (target 12 -> 5,140). `checks`: 51/51.

## Status

| Part | Healthy | Other states |
|---|---|---|
| body (`DBWallTreb2`, from `GBWallTreb`) | done, rendered, not installed | none exist |
