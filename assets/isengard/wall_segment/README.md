# Isengard wall segment (`IsengardCastleWallSegment`)

Model `IBWallN`, mesh `IBWALLN` (identity bone), own texture `IBFortresC.tga`. Palette A; the
walls' shared profile lives in [`shapes_walls.py`](../shapes_walls.py) (`run`), so the segment, the
wall end and the stubs of the fortress wall hub and the tower read as one wall. EA's body is kept
whole: the battered face, its knife fins, the corbelled parapet, the ridge and its three pyramids,
the fork plates at the ends.

## Pass 1 (shape preview)

- **Face**: two short knife fins between EA's (triangular section, silver edge, EA's lean), EA's
  middle fin carried up past the lip as a buttress blade, four pointed ember slits low in the bays.
- **Crest**: a silver edge along both lips and the ridge, six iron spikes leaning out of each lip,
  lozenge needles out of EA's pyramids (the middle one to z 66 with silver edges and collar, the
  outer two to 57.5). Down a long wall the crest reads fork, needle, NEEDLE, needle, fork.
- **Forks**: silver on the horns' outer edges (half a fork per end, as EA's plates).
- No fire and no banners: segments repeat many times (fire is on the gate and the tower).

376 -> 1,218 triangles, height 59.3 -> 66.1 (+11.4 %), footprint unchanged, 9/9 preview checks.
Sheet: `build/assets/isengard/_review/walls.jpg`.

## Kept clear

- The ends (y +-19): only the lip and ridge runs reach them, so a neighbour, a hub or the gate
  meets it without a seam and a stretched segment still joins. Everything stays inside EA's
  footprint (x +-8.32); both faces alike.

## Status

- [x] healthy body designed (pass 1, shape preview)
- [ ] reviewed, built in colour, installed
