# Angmar wall trebuchet (`AngmarWallCatapultSmall`)

Model `KBTrlSlingWall`, mesh `KBTROLLWALLSLIN` (identity bone), own texture `KBFortressJ.tga`.
Palette A2. EA's troll-sling bastion kept whole: the oval drum on its plinth, the platform where
the slinger stands, the parapet ring with its two field gaps, the blade spurs over the wall's
joints. The walls' shared pieces are in [`../shapes_walls.py`](../shapes_walls.py); EA's facts in [`building.py`](building.py).

## Pass 1

- Carn Dum merlons round the parapet ring, spaced wider (8.5) round the long curve so the ring
  is not a fence; none on the spurs or in the gaps.
- A corbel with icicles round the drum just under the parapet (straight runs, their joint caps
  hidden), ice drifts on the plinth's ledge on the four diagonals.
- Two cold braziers on the platform's rim on opposite diagonals, clear of the slinger and the
  gaps (`coldflame`). No peak, no banners: the troll is the bastion's story.

503 -> 1,977 triangles, height and footprint unchanged, 9/9 preview checks. `ICEWALL` (round the
drum and plinth to z 33) out of the bakes; own `KBFortressJ_Ice`.

## Status

- [x] healthy body designed (pass 1, shape previews; review `build/assets/angmar/_review/walls_v1.jpg`)
- [ ] reviewed by Max, built in colour, installed
- [ ] checked in game
