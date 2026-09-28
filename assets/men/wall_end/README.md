# Men wall end (`MenWallCliffCap`, `ArnorWallCliffCap`)

Model `GBWallNE`, mesh `GBWALLNE` (two segments end to end, y -19..57, faces running down the
cliff to z -46.13; its bone turns it 180 degrees). Own texture `GBWalX.tga` from `GBWall.tga`.

## Design (2026-09-27)

EA's body kept whole. Both faces carry the walls' shared profile
([`../wall_segment/wall.py`](../wall_segment/wall.py)), so the joint with a segment is exact:
machicolated crown (corbels, black band of silver stars, breastwork, merlons in the segments'
rhythm), a pilaster with the White Tree shield and a pinnacle in each bay, arrow slits, the string
course and pier caps. No battered foot (the faces go on down the cliff). The cut end gets an end
turret from [`../wall_hub/dome.py`](../wall_hub/dome.py): a chamfered-square tower corbelled out
over the wall, arched window frames, its own machicolated gallery with stars and merlons, a
steel-ribbed slate dome, gilt orb and spike.

No banners. Footprint EA's (x +-7.45, y -19..57); height 95.63 -> 114.43 (+19.7 %); 554 -> 5,397
triangles.

## Decisions

- EA draws the segment's `GBWallN_D3` for this piece's collapse: `lifecycle` skips it here
  (men/wall_segment ships it, and its `is_body` leaves the cliff caps to this recipe).
- `_A`, `_D1` derived; `_D2` rebuilt. Checks 63/63.

## Status

- [x] healthy body designed, checks pass, renders in `build/assets/men/wall_end/renders/`
- [ ] Max's review
