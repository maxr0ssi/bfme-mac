# Dwarven castle-wall trebuchet platform (`DwarvenCastleWallCatapult`)

EA's object draws Gondor's placeholder `GBWallTreb` (Gondor's castle-wall section with its middle
block), which Men and Arnor draw too. Ours is an **own copy** (`sagekit/owncopy.py`):
`own_model = "DBWallTreb2"`; mesh `GBWALLGATE`, `replaces` GBWALLUPGRD (dropped from our copy).
Own texture `DBWalC.tga`, painted from the faction atlas; `Tier.STANDARD`.

## What changed

- **Wall and stairs** as the tower's (`oldwall_segment/upgrade.py`).
- **Bastion:** EA's middle block (x +-38.02, rim to 42.35, y +-24) in the section's profile:
  plinth, corbels, rune band, drip band, coping, chevrons on the rim and returns, stepped
  pyramids on the outer corners, two banners on each front.
- **Banners:** twelve; cloth in `DBHCWallTreb2`.

## Kept clear

- The platform (x +-38, y +-24 at 53.59) is open for the catapult the object creates at
  (0, 0, 52) (`OCL_DwarvenCatapultUpgrade`).

## Status

Installed with the Dwarven pack. 128 -> 5,140 triangles (EA's target mesh has 12), height
64.75 -> 65.44 (+1.1 %), footprint inside EA's, 54/54 checks. The object has no other condition
states.

## Known limits

- Not verified: the catapult's swing against the rim chevrons (6 over the platform, as the new
  walls' trebuchet bastion).
