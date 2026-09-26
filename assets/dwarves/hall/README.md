# Dwarven fortress hall expansion (`DwarvenHallExpansion`)

Model `DBFGBunk`, redesigned mesh `DBFGBUNK`, `Tier.STANDARD`, painted from the faction atlas
`DBFortress1` onto its own textures `DBFortressG.tga` / `DBFortressG_NRM.tga` (the fortress owns
`DBFortressH`).

It stands on an expansion pad against the fortress: the low connecting wall on its -X side
(x -55..-27, the side facing the fortress) and the footprint are left exactly as they are. The
eight `ARROW_*` bones fire from the head's windows (z 80.3) and `ENTERBONE` sits at the door foot
(-2, 0, 0): nothing new stands in front of either (the crown starts at 85.1, the door frame
surrounds the opening without entering it).

## What changed (body, healthy)

- **Crown:** the fortress's tower crown lowered onto the hall's head (top 85.1): a battered crown
  ring with a bronze step, stepped-pyramid corner blocks and a stepped gable in the middle of each
  side, so the hall reads as one of the fortress's towers from the RTS camera.
- **Roof:** a battered stepped ziggurat over the old carved pyramid: rune belt, bronze step, a
  tier with the gold triangle frieze, a plain tier and a squat gilded point (top 104.5).
- **Door:** a pointed stepped frame round the door recess: two rings with the triangle frieze and
  bronze reveals, then a frame slab with a flat lintel, all in the 0.8 units between the door slab
  and the head's front (the bounding box). The opening itself is untouched.
- **Flanks:** a rune panel between bronze bands, with a small stepped triangle over it, on each
  side of the tower above the stepped slabs; battered plinths at the foot of the side slabs,
  either side of the low cross buttress.
- **Banners:** a long Erebor-blue banner (gold rod, gold piping, rune band) on each of the four
  chamfered corners of the shaft under the head (z 42.5..61.4), hung in the corner's notch 2.6 out
  of the chamfer, its rod set into the facet that squares the corner out: the chamfers face the
  RTS camera square-on. The medallion over the door and the flank rune panels stay clear. The same
  banners as the Erebor tower's.
- **Paint:** the faction style (honey granite, burnished gold and bronze, gold-inlaid runes, Erebor-blue
  enamel behind every rune band).

Footprint unchanged (x -55.4..0.6, y -19.1..19.2), height 94.0 -> 104.6 (+11.2 %, limit 20 %),
379 -> 1,457 triangles. `checks`: 36/36 pass.

## Status (`python3 -m sagekit inventory dwarves/hall`)

| Part | Healthy | Damaged (`_D` sheet) / snow / stonework | Really damaged (`DBFGBunk_D2`) | Construction (`_A`), rubble (`_D3`) |
|---|---|---|---|---|
| body (`DBFGBunk`) | done, rendered, not installed | our body on the variant sheets | derived: carries our body | old (separate models, not derived by the pipeline) |
