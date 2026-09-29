# Isengard wall end (`IsengardWallCliffCap`)

Model `IBWallNE`, mesh `IBWALLN` (two segments end to end, y -19..57, their faces carried on below
the ground for the cliff; on a bone turned 180 degrees about z), own texture `IBFortresF.tga`.
Palette A.

## Pass 1 (shape preview)

- Both segments take the walls' profile ([`shapes_walls.py`](../shapes_walls.py) `run`), so the
  joint with the next segment is exact; the short knife fins run on down the cliff face to where
  EA's faces end (z -46.2 under the first segment, rising to the ground at the cut end).
- At the cut end a blade tower stands on the parapet (flared foot at z 39.5, buried in the roof)
  to a needle at z 80: a lozenge along the wall, three layered fins a face, silver edges front and
  back, ember slits, a collar. The crest's spikes and needles stop short of it (EA's third pyramid
  is inside it). The crest steps up to it: needle 57.5, needle 66, tower 80.
- No fire and no banners.

822 -> 3,296 triangles, height 105.4 -> 126.2 (+19.7 %), footprint unchanged, 9/9 preview checks.
Pass 0 put the tower on a corbel at z 31; its fins hung in the air over the face, so it moved up.

## Kept clear

- The joint end (y -19) as the segment's; the cut end (y 57): the tower's foot stops at y 56.1.

## Status

- [x] healthy body designed (pass 1, shape preview)
- [ ] reviewed, built in colour, installed
