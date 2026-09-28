# Men fortress wall hub (`MenWallHubSmallExpansion`)

OBJECT03 is the free-standing hub's mesh, so the recipe subclasses `men/wall_hub`'s `WallHub`
and takes its design whole (parapet with silver stars and merlons, six bartizans, drum pilasters
and window frames, ribbed dome, lantern, orb, spike). BOX01 (the wall stub toward the citadel,
EA's) meets the hub's -X corner; that corner's bartizan rises from its top. Rebuild after any
change to `men/wall_hub`.

Decisions: EA paints this OBJECT03 from GBFortress1 with GBWall_NRM (the free hub uses
GBFortress1_NRM); the framework's own-sheet atlas only covers a different diffuse sheet, so the
recipe's `sheet_atlas` is the faction atlas with that normal map, and its own normal map is pinned
as `GBWalK_NRM.tga` (GBWall_NRM's length: W3D patches names in place). GBGFWHub_A and _D1 are
derived (EA's healthy body), _D2 and _D3 rebuilt. No banners.

## Status

- [x] healthy body designed (draft for Max's review; nothing installed)
- [x] lifecycle: construction, really damaged and rubble rebuilt along EA's pieces (`work/lifecycle.json`)
- [x] checks pass, renders reviewed (`build/assets/men/fortress_wall_hub/renders/compare_*.png`)

94 -> 2820 triangles; height 98.08 -> 110.22 (+12.4 %); checks 84/84; banners 0.
