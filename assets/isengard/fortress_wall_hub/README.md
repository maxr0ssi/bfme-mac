# Isengard fortress wall hub (`IsengardCastleWallHubExpansion`)

Model `IBFWHub`, mesh `IBFBALTOW01` (the wall hub's hexagon plus a wall stub toward the citadel,
x -42.2..-18.94; on a bone at z 25.47), own texture `IBFortresB.tga`. Palette A.

## Pass 3 (shape preview)

- The hexagon takes the wall hub's blade cluster whole ([`shapes_walls.py`](../shapes_walls.py)
  `hub`): a needle stack between two lozenge blades on the roof to model 84, the walls' needles on
  the parapet's six corners, spikes, silver arrises, ember slits. A citadel corner and the
  free-standing hubs read as one wall. Pass 1's crown of six horns is gone (still a drum).
- The stub takes the walls' profile (`stub`, turned onto its run along x): two short knife fins
  a face, a buttress blade on EA's middle fin, ember slits, the silver lip and ridge, spikes,
  needles out of its three pyramids (the middle one to model z 64); the -X corner's needle
  stands just inside the stub's ridge.
- No fire and no banners.

476 -> 3,976 triangles, height 62.6 -> 84.2 (+34.6 %, `max_z_growth` 0.35), footprint unchanged,
9/9 preview checks. Sheet: `build/assets/isengard/_review/walls_v3.jpg`.

## Kept clear

- The stub's end at x -42.2, where it meets the citadel; the hub's faces as for the wall hub.

## Status

- [x] healthy body designed (pass 3, shape preview)
- [ ] reviewed, built in colour, installed
