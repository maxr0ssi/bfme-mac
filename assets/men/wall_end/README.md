# Men wall end (`MenWallCliffCap`, `ArnorWallCliffCap`)

Model `GBWallNE`, mesh `GBWALLNE` (two segments end to end, y -19..57, faces running down the
cliff to z -46.13; its bone turns it 180 degrees). Own texture `GBWalX.tga` from `GBWall.tga`.
EA's body kept whole; the faces take the segment's profile, so the joint is exact.

## What changed

- **Faces**: both carry the walls' shared profile ([`../wall_segment/wall.py`](../wall_segment/wall.py)):
  machicolated crown (corbels, black band of silver stars, breastwork, merlons in the segments'
  rhythm), a pilaster with the White Tree shield and a pinnacle in each bay, arrow slits, the
  string course and pier caps. No battered foot (the faces go on down the cliff).
- **End turret** from [`../dome.py`](../dome.py): a chamfered-square tower
  corbelled out over the cut end, arched window frames, its own machicolated gallery with stars
  and merlons, a steel-ribbed slate dome, gilt orb and spike.
- **Banners**: none.

## Status

Installed with the Men pack. 554 -> 5,397 triangles, height 95.6 -> 114.4 (+19.7 %), footprint
unchanged, 63/63 checks. Construction and damaged are derived, really damaged is rebuilt. EA draws
the segment's `GBWallN_D3` for this piece's collapse; [`wall_segment`](../wall_segment/README.md) ships it.
