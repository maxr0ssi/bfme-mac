# Men wall hub (`MenWallHubSmall`, `ArnorWallHubSmall`)

Model `GBWallRmprtN`, redesigned mesh `OBJECT03` (the mesh hangs on a bone at z 80.79: design in
mesh coordinates, ground at -80.72). Own texture `GBFortressE.tga` from `GBFortress1.tga`.

## Design (2026-09-27)

EA's hexagonal tower is kept whole (ashlar, painted corbel arcade, drum with slit windows, slate
dome) and crowned with the shared tower top, [`dome.py`](dome.py):

- a flush parapet round the rim with a black enamel band of silver stars (StarBand) and square
  merlons, kept 4.4 from the corners;
- six corbelled bartizans on the corners (slit windows, steel cornices, slate spirelets); they stay
  inside every face's plane and clear of the middle 15.8 of each face, where segments run in;
- pilasters up the drum's corners and a round-arched window frame (voussoirs, keystone, sill) on
  every drum face;
- a steel eave band, steel ribs up the six edges and faces of EA's dome, a lantern cupola, a steel
  mast, gilt orb and spike (EA's stone spike is cleared: `clear`, the lantern stands there).

No banners. Footprint EA's (x +-23.44, y +-20.3); height 98.08 -> 110.22 (+12.4 %); 94 -> 2,820
triangles. `WallHub.section/rim/drum/dome` are reused by `men/wall_hub_upgradeable` (a subclass)
and `men/fortress_wall_hub`.

## dome.py (shared, owned by the walls group)

`Section` (k-gon or chamfered square by half width), `Outline` (explicit polygon), `drum`,
`moulding`, `eave_band`, `dome`, `ribs`, `parapet`, `gallery` (the citadel's machicolated
gallery), `bartizans`, `pilasters`, `window_frames` (`panel=False` frames EA's real openings),
`crown` (eave band + ribs + lantern + finial), `spire` (a finial scaled to fit). Stable API:
functions are added, never renamed. Used by the hub, the upgradeable plot, the wall end's turret,
the gate towers and the wall tower.

## Status

- [x] healthy body designed; checks 72/72; renders `build/assets/men/wall_hub/renders/`
- [x] lifecycle: `_A` derived, `_D2` and `_D3` rebuilt (`work/lifecycle.json`)
- [ ] Max's review
