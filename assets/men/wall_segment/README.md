# Men wall segment (`MenWallSegmentSmall`, `MenWallPosternGateSmall`, and Arnor's)

Model `GBWallN`, mesh `BOX01` (7.45 x 38, 49.5 high; identity bone). Own texture `GBWalH.tga` from
`GBWall.tga` (the Elves draw it too). The placement cursor `GBWallN_CUR` is derived
(`also_derived`).

## Design (2026-09-27)

EA's curtain kept whole (end piers, painted corbel arcade, paved walk); the walls' shared profile,
[`wall.py`](wall.py), on both faces:

- the citadel's machicolated crown: two-step corbels on EA's cornice, a slab whose front is a
  black band of silver stars, breastwork, coping course, square merlons with capstones in an even
  rhythm (PITCH 4.2, half a gap at each end, so neighbours continue it);
- a pilaster in the middle of each face with the White Tree shield and a pinnacle with a steel
  spike over it; two arrow slits a face (surrounds, lintels, sills); a string course at 24; a
  battered foot with a course; moulded caps on EA's half piers.

No banners. Footprint EA's (x +-7.45: the piers' fronts); height 49.5 -> 59.2 (+19.6 %).

## Decisions

- EA's mesh carries three zero-area triangles; `clear = [Degenerate()]` drops them (the checks
  want none).
- `is_body` leaves the cliff caps (`MenWallCliffCap`, Arnor's) to men/wall_end; this recipe ships
  `GBWallN_D3`, which the cliff cap also draws for its collapse.
- Paint: the recolour lifts EA's dark ashlar to white stone and its joints faded, so EA's
  bevelled normal-map blocks read as soft pillows. [`paintwall.py`](paintwall.py)'s MortarBoost
  (a high-pass of EA's own sheet) darkens and sinks EA's joints again: EA's blocks, crisp. Every
  walls-group recipe adds it in `decals()`. EA's pilaster faces take `stoneB` (EA's wall ashlar).
- ROLLOUT item 5: the Numenor variant ships as `GBWalHFortress1_U.tga`. At the wall's UVs
  `GBWall` has `GBFortress1`'s layout (the same arcade wall), so the ratio carries EA's Numenor
  look (paler stone, green bands) rather than a stray pattern; checked on the sheet, not rendered.

## Shared modules

`wall.py` (crown, merlon_row, corbels, string_course, foot, pilaster, slit, pier_cap, face,
straight, run_sweep) and `paintwall.py`, owned by the walls group; used by the segment, the wall
end, the gate's bridge and the trebuchet's slits.

## Status

- [x] healthy body designed; checks pass; renders in `build/assets/men/wall_segment/renders/`
- [ ] Max's review
