# Men wall segment (`MenWallSegmentSmall`, `MenWallPosternGateSmall`, and Arnor's)

Model `GBWallN`, mesh `BOX01` (7.45 x 38, 49.5 high). Own texture `GBWalH.tga` from `GBWall.tga`
(the Elves draw it too). EA's curtain kept whole (end piers, painted corbel arcade, paved walk);
the walls' shared profile, [`wall.py`](wall.py), on both faces.

## What changed

- **Crown**, the citadel's: two-step corbels on EA's cornice, a black band of silver stars,
  breastwork, coping course, square merlons with capstones.
- **Faces**: a middle pilaster with the White Tree shield and a spiked pinnacle; two arrow slits;
  a string course at 24; a battered foot; moulded caps on EA's half piers.
- **Paint** ([`paintwall.py`](paintwall.py)): `MortarBoost`, a high-pass of EA's own sheet, sinks
  EA's joints again so the white stone keeps crisp blocks. Every wall recipe adds it in `decals()`.
- **Banners**: none.

## Kept clear

- Neighbours: merlons at an even pitch (4.2, half a gap at each end), so the next segment continues it.

## Status

Installed with the Men pack. 276 -> 2,281 triangles, height 49.5 -> 59.2 (+19.6 %), 82/82 checks.
Construction, damaged and the cursor `GBWallN_CUR` are derived; really damaged and the collapse
`GBWallN_D3` (also the [cliff cap](../wall_end/README.md)'s) are rebuilt. The Numenor variant ships
as `GBWalHFortress1_U.tga`, checked on the sheet only.
