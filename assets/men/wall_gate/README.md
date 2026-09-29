# Men wall gate (`MenWallGateSmall`, `ArnorWallGateSmall`)

Model `GBWallGateN`, mesh `GBFDOTOWA` (the two gate towers; the leaves BOX06-09 are EA's and
animated). Own texture `GBFortressC.tga` from `GBFortress1.tga`. EA's towers kept whole (shafts,
bases, belfries with their four openings, domes), made a Gondor gatehouse with the walls' shared
kit (`../dome.py`, `../wall_segment/wall.py`).

## What changed

- **Towers**: the citadel's machicolated gallery at the shaft top (band of silver stars, merlons),
  voussoir arches with keystones and sills round EA's belfry openings (left open), a parapet of
  merlons round the dome's foot, four corbelled bartizans with slate spirelets, steel ribs, a
  lantern cupola, gilt orb and spike; arrow slits on the faces along the wall.
- **Bridge** between the towers over the gate, carrying the walls' crown, with a winged-helm crest
  on a pedestal in the middle.
- **Banners**: two, hung from the bridge over the gate, one on each face; cloth in `GBHCWallGateN`.

## Kept clear

- The leaves' swing: the bridge's underside is at z 41 (the leaves reach 40); banners at |y| 7.3..7.7.

## Status

Installed with the Men pack. 580 -> 8,862 triangles, height 83.0 -> 97.0 (+16.9 %), footprint
unchanged, 90/90 checks. Damaged and really damaged are derived; the collapse is rebuilt.
