# Dwarven sentry tower (`DwarvenSentryTower`, `dwarfsentrytower.ini`)

Model `DBTower`, redesigned mesh `DBFTOWER`, own texture `DBToweH.tga` (+ `_NRM`, `_D1`, `_snow`),
`Tier.STANDARD`. The far-off ground patch `DBTOWERG` (painted from `DBStoneA`, which is not
extracted) is left out of the bakes and renders (`bake_hidden`); it is untouched. The `close` view
is framed on the head (`views`); `rts` and `ingame` are the automatic cameras.

## What changed (body, healthy)

The slim tower keeps its shaft with the nested pointed door frames, the stepped gabled buttresses,
the slit windows and the shield, and its cross-planned head with the prow panels and archer
windows. The roofline is now a Dwarven crown:

- **Corner turrets:** in each notch of the cross, a turret rises from the old corner pillar
  (corbelled out a little, hexagon frieze at the top, bronze cornice) and ends in the fortress's
  stepped pyramid at 0.8 scale with a gilded point. The turrets stay 1.0 back from the arm ends,
  so the head still reads as a cross.
- **Arm ends:** a parapet slab carrying the hexagon frieze and a stepped triangle gable on each
  arm, between the turrets.
- **Roof:** a stepped crown in the middle: rune tier, bronze cornice, triangle-frieze tier, plain
  tier and a gilded pyramid point (the new highest point, z 124.0).
- **Under the head:** a chevron band of the triangle frieze follows the V-shaped lower edge of
  each head face; a keystone bracket under each V point carries it down to the shaft.

The archer bones (`ARROW_01..16`, on the arm-end faces at z 100.7-101.7) keep a clear field: nothing
is added in front of the arm ends below the roof. Nothing is added low on the (-X, +Y) corner
where the multiplayer banner (`DBHCTower`) hangs.

Footprint unchanged (x -16.69..16.72, y -16.62..16.63), height 109.44 -> 124.04 (+13.3 %, limit
20 %), 640 -> 1,656 triangles. `checks`: 55/55.

## Status (`python3 -m sagekit inventory dwarves/sentry_tower`)

| Part | Healthy | Construction | Damaged / really damaged | Rubble | Snow | LOD M/L |
|---|---|---|---|---|---|---|
| body (`DBTower`) | built, reviewed in renders, not installed | `DBTower_A` carries the new body | `DBTower_D1` / `_D2` carry the new body (own `_D1` sheet) | old | own `_snow` sheet | old |
| banner (`DBHCTower`) | old | | | | | |
