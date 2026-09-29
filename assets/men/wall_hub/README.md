# Men wall hub (`MenWallHubSmall`, `ArnorWallHubSmall`)

Model `GBWallRmprtN`, mesh `OBJECT03` (on a bone at z 80.79: design in mesh coordinates, ground at
-80.72). Own texture `GBFortressE.tga` from `GBFortress1.tga`. EA's hexagonal tower kept whole
(ashlar, painted corbel arcade, drum with slit windows, slate dome), crowned with [`dome.py`](../dome.py).

## What changed

- **Rim**: a flush parapet with a black band of silver stars and square merlons.
- **Bartizans**: six on the corners (slit windows, steel cornices, slate spirelets).
- **Drum**: pilasters up the corners, a round-arched window frame on every face.
- **Dome**: steel eave band and ribs, a lantern cupola in place of EA's stone spike, mast, gilt
  orb and spike.
- **Banners**: none.

## Kept clear

- Where segments run in: merlons stay 4.4 from the corners; bartizans stay inside every face's
  plane and clear of the middle 15.8 of each face.

## Status

Installed with the Men pack. 94 -> 2,820 triangles, height 98.1 -> 110.2 (+12.4 %), 72/72 checks.
Construction is derived; really damaged and the collapse are rebuilt. `WallHub` is reused by
[`wall_hub_upgradeable`](../wall_hub_upgradeable/README.md) and
[`fortress_wall_hub`](../fortress_wall_hub/README.md); `dome.py` also serves the wall end, gate
and wall tower (functions are added, never renamed).
