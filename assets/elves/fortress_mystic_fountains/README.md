# Elves fortress mystic fountains (`ElvenCitadel`, `ModuleTag_DrawMysticFountains`)

EA's eight half-round basins and swans remain whole, hung in the citadel ring's window recesses.
Own texture `EBFortresK` dresses the original body in ivory, mithril and mallorn gold.
EA's water meshes `EBFMFOUNT2` and `EBFMFOUNT3` are unchanged.

## Current design

- A rounded silver coping follows each basin's lip from wall to wall.
- Small starlight crystals in gilt cups stand at the coping's ends, below the swans' heads.
- A closed crystal-glass sheet sits over each basin floor, keeping the pool readable as water.
- No banners: the first pass's swan-covering cloth was removed.

The first pass's gilt bead was replaced by the citadel's silver coping. Height and footprint
remain unchanged; the earlier extra height allowance for banners is no longer needed.

## Lifecycle and night

Construction, really damaged and rubble states carry the redesign. The rubble recipe splits
solids over 5 units along EA's pieces: the coping and pool slabs follow the basin fragments.
The previous open pool sheets and whole slabs failed exposed-backface validation; closing the
slabs and fitting their splits fixed the geometry. Validation limits remain unchanged.

EA's model has no night meshes or night Draw names. The crystals are day-lit only.

## Verification (2026-09-26)

The pool sheets are closed on all sides. Current body: 1,520 → 4,304 triangles; height and
footprint unchanged. Checks: 97/97, including custom rubble. Day and lifecycle comparisons are in
`build/assets/elves/fortress_mystic_fountains/renders/`. Nothing installed; awaiting review.
