# Dwarven Erebor tower fortress expansion (`DwarvenEreborTowerTowerExpansion`)

Model `DBFTower`, redesigned mesh `DBFTOWER`, `Tier.STANDARD`, painted from the faction atlas
`DBFortress1` onto its own textures `DBFortressE.tga` / `DBFortressE_NRM.tga`.

It stands on an expansion pad against the fortress: the low connecting wall on its -X side
(x -56..-17, the side facing the fortress) and the footprint are left exactly as they are. The
eight `ARROW_*` bones fire from the shield windows at z 99.5; nothing new is in front of them (the
cornice starts at 105.4, above the windows).

## What changed (body, healthy)

- **Head and crown:** the tower's head is EA's fortress-tower head (same core, shields and inner
  parapet), so it takes the redesigned fortress's own tower crown, lifted 0.2: a corbelled cornice
  carrying the hexagon frieze over the bronze shields, then a battered crown ring with a bronze
  step, stepped-pyramid corner blocks (enclosing the old corner posts) and a stepped gable in the
  middle of each side. From the RTS camera the tower now reads as one of the fortress's towers.
- **Pinnacle:** a gilded stepped pinnacle on the roof's flat top (over its square vent): a
  hexagon-chain tier, bronze step, a triangle-frieze tier, a plain tier and a squat point (top 142).
- **Flanks:** a rune panel between bronze bands, with a small stepped triangle over it, on each
  side above the stepped slabs; battered plinths at the foot of the side slabs, either side of the
  low cross buttress.
- **Banners:** a long Erebor-blue banner (gold rod, gold piping, rune band) on each of the four
  chamfered corners of the shaft under the head (z 54.4..77.0), hung in the corner's notch 2.6 out
  of the chamfer, its rod set into the facet that squares the corner out: the chamfers face the
  RTS camera square-on. The medallion and the flank rune panels stay clear; the points end above
  the connecting wall (z 52.2). The same banners as the hall's.
- **Paint:** the faction style (honey granite, burnished gold and bronze, gold-inlaid runes, Erebor-blue
  enamel behind every rune band).

Footprint unchanged (x -56.5..13.1, y -19.2..19.2), height 125.0 -> 142.0 (+13.6 %, limit
20 %), 549 -> 1,559 triangles. `checks`: 36/36 pass.

## Status (`python3 -m sagekit inventory dwarves/erebor_tower`)

| Part | Healthy | Damaged (`_D` sheet) / snow / stonework | Really damaged (`DBFTower_D2`) | Construction (`_A`), rubble (`_D3`) |
|---|---|---|---|---|
| body (`DBFTower`) | done, rendered, not installed | our body on the variant sheets | derived: carries our body | old (separate models, not derived by the pipeline) |
