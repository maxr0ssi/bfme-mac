# Men forge (`GondorForge`, `ArnorForge`)

Draft for review, not installed. Renders: `build/assets/men/forge/renders/compare_*.png` (level 1:
`rts`, `close`, `gable`, `hearth`, `ingame`). The level-up meshes are chained on this recipe:
[`forge_level2`](../forge_level2/README.md) (V1, the corner towers and yard walls) and
[`forge_level3`](../forge_level3/README.md) (V2, the belfry); rebuild them after this one, in that order.

## What changed

EA's body is kept whole (the gabled hall, corner piers and parapet gables, the hearth and
chimney, the forge bed, the weapon platform). Added, in the citadel's kit:

- **Chimney**: steel and moulded bands, a sable band of gilt stars, a corbelled cornice under the
  cap, a gilt knob on the cap, a White Tree roundel on its front.
- **Roof**: a steel ridge roll with cresting and gilt knobs (stopping short of V2's belfry), two
  slate dormers with arched windows on the yard slope; EA's slate stays charcoal (`with_tiles`).
- **Yard front**: a voussoir archivolt round the door, surrounds round EA's four windows, a sable
  frieze of gilt stars and a dentilled cornice along the eaves, a cornice on the hearth's top.
- **Gables** (east and west): an archivolt round the door, surrounds round the three windows, a
  string course, EA's painted shield raised as a steel-framed sable shield with the White Tree,
  a pinnacle on the parapet's apex.
- **Piers**: moulded caps and gilt orbs round EA's finials (inside V1's towers from level 2).
- **Banners**: none added: EA's house banner (GBHCBlkSmith, in the yard's corner) is the cap of 1.
- **Paint**: the forge bed's glowing coals, the hearth's glow and the platform's planks keep EA's
  colours (`pieces.KeepFire`; the faction recolour turned the coals white).

## Clearances

- The smith (RUSAM01, hammer, tongs), the fire plane (FIREPLANE01, x -13.2..-1, y 7.6..13.3,
  z 6.7..28.6), the forge bed and its hood, the weapon racks (GPWEAPRACK1/3, PG02) and the house
  banner are untouched; nothing stands in the yard.
- The chimney's smoke emitters (CHIMNEY, CHIMNEY01-03 at z 48 round the stack) keep the band
  between 45 and 49.6 clear; E_SMOKE and the roof's smoke bones are untouched.

## Fit and status

- `GBBLKSMITH` 483 -> 5,205 triangles; footprint EA's; height +9.4 % (the chimney knob).
- 143/143 checks. Construction, really damaged and rubble rebuilt along EA's pieces, damaged derived.
  EA's damaged models draw `GBBlkSmithN_D`: the recipe adds its own copy, kept to EA's name length
  as `GBBlkSmithH_D` (`workshop/prodkit.same_length_variants`).
- EA's body carries four loose vertices (the platform's front edge) and the checks allow none on
  the target: `pieces.drop_loose` deletes them in `design()` (the geometry step's scene); `clear`
  removes faces only. Worth a framework look (see the report).
