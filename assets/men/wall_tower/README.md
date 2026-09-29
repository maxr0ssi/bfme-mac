# Men wall tower (`MenWallTowerSmall`, `ArnorWallTowerSmall`)

Model `GBWallTwrN`, mesh `GBFARTOWA` (not the arrow tower's mesh of that name). Own texture
`GBFortressX.tga` from `GBFortress1.tga`. EA's tower kept whole (shaft, corner buttresses, the
carved emblem on the field faces, the belfry with its painted windows, the slate dome), crowned
from [`../dome.py`](../dome.py).

## What changed

- **Gallery**: the citadel's, round the shaft top (band of silver stars, merlons).
- **Bartizans**: four, corbelled on the diagonals over EA's buttresses.
- **Belfry and dome**: a parapet of merlons round the belfry's top; steel eave band and ribs on the
  dome, a lantern cupola (its collar wraps EA's dome point), a steel mast, gilt orb and spike.
- **Banners**: one, from the gallery on the +x face, ending above EA's emblem (z 40.2); cloth in
  `GBHCWallTwrN`.

## Status

Installed with the Men pack. 238 -> 3,174 triangles, height 93.6 -> 110.5 (+18.0 %), footprint
unchanged, 79/79 checks. Damaged is derived; really damaged and the collapse are rebuilt.

## Known limits

- `BOX01`, EA's wall stub under the tower, stays EA's; a chained recipe could carry `wall.py`'s
  crown through it.
