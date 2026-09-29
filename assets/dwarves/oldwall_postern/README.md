# Dwarven castle-wall postern (`DwarvenWallPosternGate`)

EA's object draws Gondor's placeholder `GBWallPG` (a box labelled "Men Wall PosternGate" across
Gondor's castle-wall section), which Men and Arnor draw too. Ours is an **own copy**
(`sagekit/owncopy.py`): `own_model = "DBWallPG2"`; mesh `GBWALLGATE`, `replaces` GBWALLUPGRD and
BOX01 (dropped from our copy). Own texture `DBWalP.tga`, painted from the faction atlas;
`Tier.STANDARD`.

## What changed

- **Wall and stairs:** the old castle wall's section unbroken along |y| <= 99.5 at EA's walkway
  (53.59), two statue pilasters and four banners per face, a Dwarven stair down each ramp. EA's
  middle block is not rebuilt: the porches take its place.
- **Porches** on both faces (x 23.77 .. 47, y +-18): battered plinth, a stepped pointed frame
  round a stone door with bronze straps, a banner either side, a corbelled hexagon cornice, a
  stepped gable (41.9, under the wall's corbels, which stop over the porch), corner pyramids.
- **Banners:** twelve; cloth in `DBHCWallPG2`.

## Kept clear

- EA's exit bones `POST01..04` (x +-52.3 / +-77.8, on the ground) are outside the porches
  (plinth to 49.3).

## Status

Installed with the Dwarven pack. 140 -> 4,824 triangles (EA's target mesh has 12), height
64.75 -> 65.33 (+0.9 %), footprint inside EA's (the label box reached x +-52.05), 54/54 checks.
The object has no other condition states.
