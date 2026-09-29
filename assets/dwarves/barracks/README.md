# Dwarven barracks (`DwarfBarracks`)

Model `EBBarracks_SKN` (skinned, skeleton `EBBarracks_SKL`), mesh `EBBARRAKA` (the gate in the rock
and the two stair wings), own texture `EBBarrackH.tga` (from `EBBarracks.tga`). `Tier.STANDARD`.
The rock, `V1` (level 2), `V2` (level 3), racks, torches and the animated dwarf are EA's.

## What changed

- **Gate**: a deep stepped pointed portal (two triangle-frieze rings, an outer stone ring), a gold
  rune tympanum and lintel, a bronze cornice with gilded pinnacles, and a stepped frontispiece
  with a gilded finial at z 46.
- **Stair wings** (B mirrors A): a keel buttress on each prow, a rune band and bronze coping round
  the rim, chevron parapets with gilded tips, five piers with rune belts.
- **Banners**: four, one on each gate jamb and one on each wing's nose pier; cloth in `EBHCBarracks`.

## Kept clear

- EA's doorway (|u| <= 4.6, head z 20.4), the torches and their fires, the night windows in the rock.
- `V1`'s lap and forearms at level 2: the lintel, cornice and frontispiece stay in front of them.
- u = (x + y)/sqrt 2 runs across the front, d = (x - y)/sqrt 2 towards the camera.

## Status

Installed with the Dwarven pack. 828 -> 3,314 triangles, height 41.16 -> 46.00 (+11.8 %),
204/204 checks, 5 night lights. Damaged derives the new body; construction, really damaged and
rubble are rebuilt along EA's pieces.

## Known limits

- EA's own house flag in `EBHCBarracks` now shows in skirmish too and hides the right jamb's
  banner from the RTS camera.
