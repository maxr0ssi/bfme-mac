# Isengard fortress wall hub (`IsengardCastleWallHubExpansion`)

Model `IBFWHub`, mesh `IBFBALTOW01` (the wall hub's hexagon plus a wall stub toward the citadel,
x -42.2..-18.94; on a bone at z 25.47), own texture `IBFortresB.tga`. Palette A.

## Pass 1 (shape preview)

- The hexagon takes the wall hub's crown whole ([`shapes_walls.py`](../shapes_walls.py) `hub`):
  six horns, the stepped plinth and needle, ribs, spikes, silver arrises, ember slits. A citadel
  corner and the free-standing hubs read as one wall.
- The stub takes the walls' profile (`stub`, turned onto its run along x): two short knife fins
  a face, a buttress blade on EA's middle fin, ember slits, the silver lip and ridge, spikes,
  needles out of its three pyramids (the middle one to model z 64).
- No fire and no banners.

476 -> 2,314 triangles, height 62.6 -> 75.0 (+19.9 %), footprint unchanged (the stub's first
needle was narrowed to stay inside x -42.2), 9/9 preview checks.

## Kept clear

- The stub's end at x -42.2, where it meets the citadel; the hub's faces as for the wall hub.

## Status

- [x] healthy body designed (pass 1, shape preview)
- [ ] reviewed, built in colour, installed
