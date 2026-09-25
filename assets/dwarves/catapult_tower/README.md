# Dwarven catapult tower fortress expansion (`DwarvenCatapultExpansion`)

Model `DBFCTower`, redesigned mesh `DBFCTOWER`, `Tier.STANDARD`, painted from the faction atlas
`DBFortress1` onto its own textures `DBFortressC.tga` / `DBFortressC_NRM.tga`. The untextured
`P1` plane (the catapult's platform, at the `P1` bone) is left out of bakes and renders
(`bake_hidden`); it is not touched.

It stands on an expansion pad against the fortress; the catapult is a separate object on the
platform (floor z 50.0, x -37.8..8.6, |y| 18.7), which stays clear: everything new sits on the
outer 2.2 of the 3.8-thick rim or on the outer walls. The plain -X wall (x -41.5, the side against
the fortress) keeps its rim as it is.

## What changed (body, healthy)

- **Parapet:** the fortress walls' solid chevron parapet round the rim (both sides and the prow):
  a coping with a bronze band on angular corbels, then slabs with stepped-triangle tops (the
  fortress's `chevron_parapet`, lowered onto a shorter coping so the height stays in budget).
- **Rune frieze:** a gold rune band with bronze edges along both side walls, under EA's triangle
  frieze and above the carved panels.
- **Paint:** the faction style (honey granite, burnished gold and bronze, gold-inlaid runes).

Footprint unchanged (x -56.7..16.2, y -32.6..26.5), height 53.0 -> 61.8 (+16.6 %, limit 20 %),
242 -> 906 triangles. `checks`: 46/46 pass.

## Status (`python3 -m sagekit inventory dwarves/catapult_tower`)

| Part | Healthy | Damaged (`_D` sheet) / snow / stonework | Really damaged (`DBFCTower_D2`) | Construction (`_A`), rubble (`_D3`) |
|---|---|---|---|---|
| body (`DBFCTower`) | done, rendered, not installed | our body on the variant sheets | derived: carries our body | old (separate models, not derived by the pipeline) |

Note: the platform floor's gold disc picks up the style's grime/dirt layers (dark blotches in
`renders/new_rts.png`); that comes from the paint stack, not this recipe.
