# Men stable (`GondorStable`, `ArnorStable`)

Level-ups: [`stable_level2`](../stable_level2/README.md) (V1), [`stable_level3`](../stable_level3/README.md)
(V2), chained on this recipe.

## What changed

EA's body is kept whole (central block and cupola, the two slate-roofed wings with their stall
arcades and porched gable ends). Added, in the citadel's kit:

- **Crown**: the citadel's machicolated gallery round the central block (corbels, a sable band of
  silver stars, parapet, square merlons), corbelled bartizans with slate spirelets on the two
  yard-side chamfers, pinnacles on the back two. Clear of V2's belfry base at level 3.
- **Cupola**: steel eave band, ribs, lantern, gilt orb and spike (inside V2 at level 3).
- **Wings**: steel ridge rolls with cresting and gilt knobs; a sable band of gilt stars along the
  eaves' fascia; keystones on the stall arches, capitals and consoles on the piers; two slate
  dormers with arched windows on the north-east wing's yard slope.
- **Gables**: pinnacles on EA's raking cornice's eave corners and on the south-east apex; a
  voussoir archivolt round each porch arch.
- **Banners**: one, over the stable door; with EA's house banner (on the north-east gable's apex)
  that is the cap of 2. Cloth in `GBHCStable`.
- **Paint**: EA's slate roofs stay charcoal slate (`with_tiles` mask hints on GBStable); the hay
  and gilt keep EA's colours (`pieces.KeepFire`).

## Kept clear

- Stall arches: nothing in the openings (the horse heads HRSHEADS come out of them); keystones
  stop at the arch crowns.
- Gables: V2's flag poles leave both gables at z 44.7 on their centre lines and the flags hang
  from z 28 in the centre plane: no apex piece on the north-east gable (EA's house banner stands
  there), the porch keystones end under z 28, nothing else on the centre lines.
- The yard (horse walker, the walking horse) is untouched.

## Status

Installed with the Men pack. `GBSTABLE` 2,186 -> 6,516 triangles, footprint EA's, height
61.6 -> 69.8 (+13.4 %, bartizans, cupola knob), 120/120 checks. Damaged, really damaged and
rubble are rebuilt along EA's pieces (`GBStable_D1`-`D3`).

- Own texture `GBStablH`. EA's damaged models draw `GBStable_D`, which no INI state swaps to, so
  the recipe adds its own copy (`levels.with_damaged`) as the barracks does.
- The model is symmetric about y = -0.56 except the south-east arcade, which stands 0.7 further
  back: the wing pieces are mirrored with their own face offsets.

## Known limits

- Construction (`GBStable_A`) stays EA's (recoloured): its horse piece (`GBSTABLE_05`, painted
  from the horse sheets too) has no variant of ours, and the rest fails the open-backs check at
  the finished frame (2.88 % of our area, EA's 0.03 %).

## Shared module here

- `pieces.py` (used by the stable, the forge and their level meshes): `mirrored`, `faces`,
  `dormer`, `gable_dress`, `keystone`, `archivolt`, `cornice` (motifs.cornice closed on top),
  `socle`, `drop_loose`, `KeepFire`.
