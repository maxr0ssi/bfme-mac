# Elves green pasture fence (`ElvenGreenPasture`)

EA's carved branch rails and open filigree gateway remain whole. This is mesh `FENCE` of
`EBStable_SKN`, chained on `elves/green_pasture`; build it after the stable.

## Current design

- A gilt leaf finial crowns the existing gate.
- A small crystal lantern hangs on a gilt rod under the crown, clear of the passage.
- Gilt collars and leaf finials crown the corner posts.
- No cloth.

The first pass's stone hood and pointed moulding were removed because they hid EA's filigree.
The gate stays open. The allowed footprint margin accommodates the crown finial's blade.

## Models, lifecycle and night

Own texture `EBStable_AlphH` preserves the original cut-out alpha; there is no normal map.
The tilted bone requires model-space design coordinates. `always_shown` permits the chained
fence's lantern to glow at every upgrade level: a crystal pane and a small free glow card.
Lifecycle builds combine the stable and fence recipes along EA's pieces.

## Verification (2026-09-26)

Current body: 1,332 → 2,210 triangles; height 35.46 → 39.66. Checks: 159/159.
Construction, damaged, really damaged and rubble states carry the chained redesign.
Day, lifecycle and night previews are in `build/assets/elves/green_pasture_fence/renders/`.
Nothing installed; awaiting player review.
