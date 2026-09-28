# Elves fortress crystal moat (`ElvenFortressCrystalMoat`)

EA's water ring remains whole around the fortress, dressed as the citadel's outer garden.
Own texture `EBFortresM` paints the body; EA's water mesh `EBFCMOAT2` is unchanged.

## Current design

- A silver coping follows the parapet round the ring, leaving the gate gap open.
- Silver knotwork on sea-green enamel sits between gilt beads on the outer face.
- Small crystal lanterns on silver feet mark the parapet corners, including the gate gap's ends.
- A cluster of starlight crystal shards rises from the water at the middle of each ring face.
- No cloth: the first pass's leaf drapes were removed.

The lanterns and tallest crystals now rise above the first pass's low glints. The recipe's
explicit height allowance is 50%; the outer coping and band use a 0.5 footprint margin.

## Lifecycle and night

`EBFCMoat_D1`, `_D2` and `_D3` have no matching body pieces and remain EA's recoloured models.
This is a reported fallback, not custom rubble geometry. EA's model has no night meshes or
night Draw names, so the crystals are day-lit only. No house-colour model is needed.

## Verification (2026-09-26)

Current body: 158 → 5,528 triangles; height 5.00 → 7.43. Checks: 43/43.
Day comparisons are in `build/assets/elves/fortress_crystal_moat/renders/`. The pipeline does not
render unchanged EA fallback states; there are no added night lights.
Awaiting player review; nothing installed.
