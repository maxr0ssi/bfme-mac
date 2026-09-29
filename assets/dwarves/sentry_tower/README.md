# Dwarven sentry tower (`DwarvenSentryTower`, `dwarfsentrytower.ini`)

Model `DBTower`, mesh `DBFTOWER`, own texture `DBToweH.tga` (from `DBTower.tga`), `Tier.STANDARD`.
The far-off ground patch `DBTOWERG` (painted from `DBStoneA`, which is not extracted) is left out
of the bakes and renders (`bake_hidden`); it is untouched. The `close` view is framed on the head
(`views`); `rts` and `ingame` are the automatic cameras.

## What changed

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
- **Banners:** four, on the corner pillars flanking the -Y and +X arm panels; cloth in `DBHCTower`.

## Kept clear

- The archer bones (`ARROW_01..16`, on the arm-end faces at z 100.7-101.7): nothing is added in
  front of the arm ends below the roof.
- The (-X, +Y) corner, where EA's house banner hangs: nothing added low there.

## Status

Installed with the Dwarven pack. 640 -> 1,848 triangles, height 109.44 -> 124.04 (+13.3 %), 86/86
checks. Construction and damaged derive the new body; really damaged and rubble are rebuilt along
EA's pieces.
