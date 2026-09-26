# Dwarven fortress (`DwarvenFortressCitadel`)

The faction's hero building (`Tier.HERO`: 4096 texture, 2048 normal map), own textures
`DBFortressH.tga` / `DBFortressH_NRM.tga`.

## What changed (body, healthy)

- **Walls:** solid parapets with stepped-triangle (chevron) tops and angular corbels instead of
  the flat coping; stepped buttresses on the long walls; battered plinths with a string course.
- **Towers:** a corbelled cornice carrying the hexagon frieze, then a battered stepped crown ring
  with stepped-pyramid corner blocks and stepped gables.
- **Gate:** battered pylons (stepped plinth, rune belt, pilaster ribs, corbelled frieze, stepped
  cap), a rune lintel with a stepped crown, king pillars with the statue relief, and a deep
  four-ring pointed arch frame around the original opening.
- **Banners:** a long Erebor-blue banner (gold rod, gold piping, rune band; 7 x 22) on each of the
  eight outer tower faces, hung free 3.6 out of the shaft under the point of the face's shield
  (rod set into the rib under it, point at z 59: above the walls' parapets and the barrel
  upgrade's oil gates, which reach z 57.2). Two banner poles (height 42, banners 6 x 18) flank the
  mouth of the gate's approach ramp at x 118, on the rock beside the paving: from the RTS camera
  they stand below the gate, not across it. The gate, its braziers and statue are untouched;
  checked against the rebuilt barrel, monument, brazier and statue add-ons at the same origin.
- **Paint:** the faction palette (honey granite, burnished gold and bronze, gold-inlaid runes,
  Erebor-blue enamel behind every rune band),
  dressed-stone blocks, baked occlusion and edge wear, grime under ledges, a gilded double-chevron
  sigil on every tower shield.

Footprint unchanged, height +13 % (limit 20 %), 8,306 triangles (budget 15,000); `checks`: 57/57 pass.

## Status (`python3 -m sagekit inventory dwarves/fortress`)

| Part | Healthy | Construction | Damaged | Really damaged / rubble | Snow / stonework | LOD M/L |
|---|---|---|---|---|---|---|
| body (`DBFortress`) | done, in game | old | old look (texture swap misses) | old | old | old |
| door (`DBFDoor_*`) | old | old | old | old | – | – |
| flame launchers (`DBFFlam*`, improvement 1) | old | | | | | |
| oil casks (`DBFRBarrel*`, improvement 2) | old | | | | | |
| statues (`DBFStatus*`, improvement 3) | old | | | | | |
| catapult tower (`DBFGCap*`, monument) | old | | | | | |
| banner (`DBHCFortress`) | old | | | | | |

The healthy body was first built by two agent rounds (their scripts are the ancestors of
`sagekit`); this recipe reproduces it through the framework.
