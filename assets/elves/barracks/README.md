# Elves barracks (`ElvenBarracks`)

EA's hall, carved porches, lattice gables, weapon racks, palisade yard and mallorn stay whole.
The approved citadel's ivory, mithril and mallorn gold palette dresses the original detail.

## Current design

- Silver caps follow the ridge's two waves, with a gilt leaf finial on each peak.
- Six silver-framed lancet windows and silver sills dress the hall front behind EA's racks.
- Two leaf banners hang on the front corner piers.
- Crystal lanterns stand on the porch pedestals and hang from the gable horns.
- Gilt leaf finials crown the yard's two obelisks.

The earlier balustrade, intermediate columns, extra ridge leaves and obelisk pennants were
removed from the first pass to retain EA's detail and keep the additions modest.

## Models, lifecycle and night

The body is `NBELVNBARXA`, shipped as `EBElvnBarx_SKN` with its own `nbelvnbarH` texture family.
The shared Arnor model and cloth stay untouched: the Elven body and house colour use own copies,
`EBElvnBarx_SKN` and `EBHCElvnBarx`. Only Elven Draw modules are repointed.

Construction carries the redesign. `_D1` derives the healthy body with its damaged texture;
`_D2` and `_D3` have no matching body pieces and remain EA's recoloured models. Cloth is hidden
in moving construction/break states. EA's trees and upgrade crown remain unchanged.

At night, the horn lanterns, east porch lanterns and five front windows glow. The sixth window
is behind EA's rack. Free glow cards stay at the two horn lanterns' original locations.

## Verification (2026-09-26)

Current body: 2,211 → 4,881 triangles; height 60.07 → 61.33; footprint unchanged.
Checks: 169/169. Day, lifecycle and night comparisons are in
`build/assets/elves/barracks/renders/`. Awaiting player review; nothing installed.
