# Dwarven castle-wall postern (`DwarvenWallPosternGate`)

EA's object draws Gondor's placeholder `GBWallPG` (a box labelled "Men Wall PosternGate" across
Gondor's castle-wall section), which Men and Arnor draw too. Ours is an **own copy**
(`sagekit/owncopy.py`): `own_model = "DBWallPG2"`; redesigned mesh `GBWALLGATE`, `replaces`
GBWALLUPGRD and BOX01 (dropped from our copy). Painted from the faction atlas onto `DBWalP.tga`;
`Tier.STANDARD`.

## What changed (body, healthy)

- **Wall and stairs:** the old castle wall's section unbroken along |y| <= 99.5 at EA's walkway
  (53.59), two statue pilasters and four banners per face, a Dwarven stair down each ramp. EA's
  middle block is not rebuilt: the porches take its place.
- **Porches** on both faces (x 23.77 .. 47, y +-18): battered plinth, a stepped pointed frame
  round a stone door with bronze straps, a banner either side, a corbelled hexagon cornice, a
  stepped gable (41.9, under the wall's corbels, which stop over the porch), corner pyramids.
- **Kept clear:** EA's exit bones `POST01..04` (x +-52.3 / +-77.8, on the ground) are outside the
  porches (plinth to 49.3).

House colour: 12 banners -> `DBHCWallPG2`. Footprint inside EA's (the label box reached x +-52.05);
height 64.75 -> 65.33 (+0.9 %); 140 -> 4,824 triangles (target 12 -> 4,824). `checks`: 51/51.

## Status

| Part | Healthy | Other states |
|---|---|---|
| body (`DBWallPG2`, from `GBWallPG`) | done, rendered, not installed | none exist |
