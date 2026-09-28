# Men wall gate (`MenWallGateSmall`, `ArnorWallGateSmall`)

Model `GBWallGateN`, mesh `GBFDOTOWA` (the two gate towers; the leaves BOX06-09 are EA's and
animated). Own texture `GBFortressC.tga` from `GBFortress1.tga`.

## Design (2026-09-27)

EA's towers kept whole (shafts, bases, belfries with their four openings, domes), made a Gondor
gatehouse with the walls' shared kit (`../wall_hub/dome.py`, `../wall_segment/wall.py`):

- each tower: the citadel's machicolated gallery at the shaft top (band of silver stars, merlons),
  voussoir arches with keystones and sills round EA's belfry openings (openings left open), a
  parapet of merlons round the dome's foot, four corbelled bartizans with slate spirelets, steel
  ribs, a lantern cupola, gilt orb and spike; arrow slits on the faces along the wall;
- a bridge between the towers over the gate (underside at 41, above the leaves' 40) carrying the
  walls' crown, with a winged-helm crest on a pedestal in the middle;
- two house-colour banners hung from the bridge over the gate, one on each face (|y| 7.3..7.7,
  outside the leaves' swing).

Footprint EA's; height 83.0 -> 97.0 (+16.9 %); 580 -> 8,894 triangles. Checks 90/90. `_D1`, `_D2`
derived, `_D3` rebuilt.

## Open

- The Men style has no `house_template`, so the gate has no house-colour model of its own yet:
  the banners' cloth stays in the body in the palette's preview navy until the integration pass
  (`sagekit house men`) has a template to copy.

## Status

- [x] healthy body designed, checks pass, renders in `build/assets/men/wall_gate/renders/`
- [ ] Max's review
