# Angmar hallof twilight v1 (`AngmarHallofTwilight`)

Stub from `python3 -m sagekit new angmar`: nothing redesigned yet (`design()` returns no solids).

- Source model `KBTemple`, target mesh `V1` (1499 triangles), sheet `KBTemple.tga` -> own `KBTemplX.tga`.
- Role barracks; nearest Dwarven recipe `barracks`.
- EA's body measured: `python3 -m sagekit measure angmar/hallof_twilight_v1` -> `work/measure.json`.

## Decision (2026-10-01)

Not a building: the Hall of Twilight's level-2 piece (`V1`, shown at level 2, hidden at 3). It stays
EA's. The Hall's own design ([`../hallof_twilight`](../hallof_twilight)) stands on `BASE`, clear of `V1`
and `V2`, and reads the same at every level, so nothing here needs matching yet.

## Status

- [ ] healthy body designed
- [ ] checks pass, renders reviewed
