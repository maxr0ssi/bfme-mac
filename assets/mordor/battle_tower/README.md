# Mordor battle tower (`MordorBattleTower`)

Model `MBSentry`, mesh `CYLINDER01`, own texture `DolGolGatH.tga` (from `DolGolGate.tga`, which
Angmar draws too); new faces map to the faction's master sheet. EA's star-shafted tower is kept
whole. EA's facts are in [`building.py`](building.py), the design in [`tower.py`](tower.py), the
group's pieces in [`../shapes_harad.py`](../shapes_harad.py).

## Pass 1: the citadel's claw on the roof

- **Claw**: eight jagged spikes (the citadel's Horn) rise from inside the roof's dish (r 7, z 111)
  and lean in over the fire. Four are tall (tips z 136), with a steel outer edge, teeth, a hook and
  a lava seam; four are short (z 128).
- **Fire bowl**: a jagged seven-sided iron bowl with a brass lip sits in the dish (z 112..122,
  r 5.4). It burns orange (`furnace`) with a dark smoke column (`smoke`).
- **The Eye** sits in the head's valley that faces the camera (330 degrees, z 94..107).
- **Lava** wells out along the four diagonals from the foot (r 10..18, `embers`), and a seam glows
  up the shaft's rib on the camera side.

680 -> 2,565 triangles. Height 122.8 -> 136.1 (+10.8 %). Footprint unchanged. 9/9 preview checks.
6 fire points. Review sheets: `build/assets/mordor/_review/harad_v1.jpg`, `harad_v2.jpg` (unchanged in pass 2).

## Kept clear

- The archers' bones `ARROW_01`..`16` (r 7..8.3, z 89.2 and 91.7, inside the head).
- The house banner `MBHCSentry` (x -21..-10, y -19.5..-7.6).

## Status

- [x] healthy body designed (shape preview, pass 1)
- [x] coordinator's review of `harad_v1.jpg`: keep
- [ ] Max's review, then build, colour, install
