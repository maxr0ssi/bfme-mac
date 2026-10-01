# Angmar wall hub (`AngmarWallHubSmall`)

Model `KBWallHubN`, mesh `WALL HUB` (on a bone turned 90.5 degrees and lifted 48.1: the design is
built in model space and turned into the mesh's frame, `FRAME`), own texture `KBFortressC.tga`.
Palette A2. EA's octagonal hub kept whole. The walls' shared pieces are in [`../shapes_walls.py`](../shapes_walls.py); EA's facts in [`building.py`](building.py).

## Pass 1 (`shapes_walls.hub`, shared with fortress_wall_hub)

- **Peak**: EA's three horns (120 degrees apart, curving in over the roof to points round the axis)
  frozen from z 84 to their points: an ice casing with a ragged frost line, rime toward the points,
  crystals growing out (`freeze`), the citadel tines' frozen tips on the crown EA already gave the
  hub. No new spike.
- **Fire**: a sorcerer's cold brazier in the roof's middle under the horns' points (a claw of five
  iron prongs out of black stone shards, `coldflame` at (0, 0, 69.2) model space).
- **Battlement and ice**: Carn Dum merlons on the parapet of every face (none where the horns
  stand), icicles under the parapet's overhang all round, ice drifts on the four diagonal faces
  (the faces on the axes stay clear for walls run into them).
- No banners (hubs repeat along every wall).

352 -> 1,818 triangles, height 96.05 -> 97.0 (+1.0 %), footprint unchanged, 9/9 preview checks.
No Ice Walls mesh on this model; own `KBFortressC_Ice`.

## Status

- [x] healthy body designed (pass 1, shape previews; review `build/assets/angmar/_review/walls_v1.jpg`)
- [ ] reviewed by Max, built in colour, installed
- [ ] checked in game
