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
- **Paint:** the faction palette (honey granite, burnished gold and bronze, gold-inlaid runes),
  dressed-stone blocks, baked occlusion and edge wear, grime under ledges, a gilded double-chevron
  sigil on every tower shield.

Footprint unchanged, height +13 % (limit 20 %), 7,704 triangles (budget 15,000).

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
