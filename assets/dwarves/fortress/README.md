# Dwarven fortress (`DwarvenFortressCitadel`)

Model `DBFortress`, mesh `DBFORTRESS`, own texture `DBFortressH.tga` (from the faction atlas
`DBFortress1.tga`). `Tier.HERO` (4096 texture, 2048 normal map). The door (`DBFDoor_*`) is EA's.

## What changed

- **Walls**: solid chevron parapets on angular corbels, stepped buttresses on the long walls,
  battered plinths with a string course.
- **Towers**: a corbelled hexagon cornice, then a battered crown ring with stepped-pyramid corners
  and stepped gables; a gilded double-chevron sigil on every tower shield.
- **Gate**: battered pylons, a rune lintel with a stepped crown, king pillars with the statue
  relief, and a four-ring pointed arch round EA's opening.
- **Banners**: ten, one on each of the eight outer tower faces (point at z 59) and two poles at the
  mouth of the gate ramp (x 118); cloth in `DBHCFortress`.

## Add-ons

Each add-on is its own recipe and ships its own model:

- `fortress_braziers` (`DBFFlam`, improvement 1): gilded braziers either side of the gate.
  84 -> 1,292 triangles, 94/94 checks.
- `fortress_barrels` (`DBFRBarrel`, improvement 2): oil batteries on the four tower heads and an
  oil gate on each tower's outer face. 692 -> 3,956 triangles, 84/84 checks.
- `fortress_statues` (`DBFStatus`, improvement 3): EA's axe-bearer on a new stepped plinth over
  the gate. 455 -> 621 triangles, 88/88 checks.
- `fortress_monument` (`DBFGCap`, the Mighty Catapult keep): a crowned drum with six gilded spires
  (the fortress's highest point) and ten banners. 2,648 -> 4,038 triangles, 92/92 checks; cloth in `DBHCFGCap`.

## Kept clear

- The tower banners end above the oil gates (z 57.2); the gate ramp poles stand below the gate
  from the RTS camera. The gate leaves slots for the braziers and the statue plinth.

## Status

Installed with the Dwarven pack. 2,708 -> 8,266 triangles, height 108.71 -> 123.00 (+13.1 %),
106/106 checks. Construction, really damaged and rubble are rebuilt along EA's pieces; damaged
draws the body on its own `_D` sheet. The add-ons' lifecycle models are rebuilt too; the statue's
damaged state derives the new plinth.
