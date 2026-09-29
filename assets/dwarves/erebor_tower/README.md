# Dwarven Erebor tower fortress expansion (`DwarvenEreborTowerTowerExpansion`)

Model `DBFTower`, mesh `DBFTOWER`, own texture `DBFortressE.tga` (from the faction atlas
`DBFortress1.tga`). `Tier.STANDARD`.

## What changed

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
- **Banners:** four, a long banner (gold rod, gold piping, rune band) on each chamfered corner of
  the shaft under the head (z 54.4..77.0), hung in the corner's notch 2.6 out of the chamfer, its
  rod set into the facet that squares the corner out, so the chamfers face the RTS camera
  square-on. Cloth in `DBHCFTower`. The [hall](../hall/README.md) carries the same banners.

## Kept clear

- The low connecting wall on the -X side (x -56..-17, facing the fortress) and the footprint.
- The eight `ARROW_*` bones fire from the shield windows at z 99.5; the cornice starts at 105.4.
- The medallion and the flank rune panels; the banner points end above the connecting wall (z 52.2).

## Status

Installed with the Dwarven pack. 549 -> 1,543 triangles, height 124.98 -> 142.00 (+13.6 %), 84/84
checks. Construction, really damaged and rubble are rebuilt along EA's pieces; damaged draws the
body on its own `_D` sheet.
