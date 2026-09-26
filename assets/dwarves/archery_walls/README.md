# Dwarven archery range, level 2 yard walls (`V1A` of `DBArchRnge_SKN`)

The walls EA shows at `Upgrade_StructureLevel2` (`ModuleTag_ShowWalls`: `V1 V1A`) and at level 3.
They are redesigned on the level-3 tower's finished model: `base = "dwarves/archery_tower"`,
which is itself based on `dwarves/archery_range`. The chain is archery_range, then archery_tower,
then archery_walls. This building's `dbarchrnge_skn.w3d` is the one that ships. Rebuilding
either base means rebuilding this one after it.

Own texture: `DBArchRngW.tga` (`dbarchrngw.dds`, `dbarchrngw_nrm.tga`, snow `dbarchrngW_snow`).
Two-sheet build, tier STANDARD.

## What changed

EA's V1A is four plain battered walls round the shooting yard, 16.9 high with a ridged top:

| Wall | Position |
|---|---|
| west | x −32.7..−27.4 |
| south | y −52.4..−47.4 |
| east | x 18.5..23.8, up to the hall |
| north | y 47.6..52.5, under the gallery |

Two stepped plaques stand on the west and south walls.

- **Coping:** over every ridge. It has a gold rune band on blue enamel between bronze edges.
- **Chevron crest:** the fortress's solid stepped chevrons with gilded tips, scaled to a low
  wall. It runs from z 16.95 to z 20.2, within the 20 % height limit (20.29). It stops short of
  the V1 obelisks at the south corners, the gallery post the west wall ends in (y 27.6) and the
  hall's corner turret (y −25).
- **Battered plinth and bronze string course:** on the faces the footprint allows. Both faces of
  the south wall, the west wall's outer face, and the yard faces of the north and east walls. The
  outer north and east faces are the footprint's edge. On the west wall's yard face the plinth
  stops at y 16, where the range's ground ladder stands.
- **Niches:** EA's plaques become reliefs in stepped niches. Stone pilasters with bronze capitals
  stand either side, under a stepped lintel with the triangle frieze. The plaques themselves are
  EA's: their fronts are the footprint's edge, so nothing can go over them.
- **Banners:** four Erebor-blue banners, two on the south outer face and two on the west outer
  face. They hang free from under the coping, in front of the string course.

Footprint = V1A's. Height +19.5 %. V1A goes from 139 to about 1,870 triangles.

## Not changed: `V1`

`V1` (24 triangles) is the pair of obelisks at the yard's south corners. Its south faces lie on
its own footprint's edge (y −54.14, up to the point at z 59). No shell or belt can wrap an obelisk
without sitting on EA's face, where the two surfaces would flicker (z-fight). It stays EA's stone,
recoloured by the faction sheet.

## House colour

`house_tags = ()`: the cloth stays in V1A, in the palette's blue. The house-colour model is drawn
at every level, so cloth moved into it would show before the walls are built.

## Status

| Part | Healthy | Snow | Damaged |
|---|---|---|---|
| `V1A` (level 2) | built, checks pass, **awaiting review** | variant `DBArchRngW_snow` painted | our walls whole in `DBArchRnge_D1` (`also_derived`: EA's D1 walls are the healthy ones with 44 faces chipped off), `DBArchRngW_D` sheet, **awaiting review** |
| `V1` | EA's, recoloured | |

The renders show the whole model. The range's body renders grey in them because the render step
does not find the base's own textures; see `archery_tower/README.md`.
