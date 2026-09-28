# Elves green pasture (`ElvenGreenPasture`)

EA's stable remains whole: both hip-roofed wings, stall arches, pavilion gateway and blue lattice
dome. The fence is the chained `elves/green_pasture_fence` recipe, built after the stable.

## Current design

- A silver collar follows the dome's foot, leaving its lattice visible.
- A small lantern cupola crowns the dome: gilt collar, silver colonnettes, crystal, slate cap and
  gilt leaf finial.
- Crystal lanterns on silver posts stand on the pavilion's corners.
- Two player-colour leaf banners flank the existing gateway.
- Silver caps follow the wing ridges, with one gilt leaf finial on each.

The first pass's large crossing tower, dome-covering spire, pointed portal infill, stall frames
and extra banners were removed. EA's detailed body is kept whole.

## Models, lifecycle and night

The body `EBBSTABLES` in `EBStable_SKN` uses the own `EBStablH` texture family. The tilted bone
requires model-space design coordinates (`world_space`). Cloth goes to `EBHCStable`; trees,
upgrade crown, horses, feed and bones remain unchanged.

Construction, really damaged and rubble states carry the redesign; `_D1` derives the healthy
body. Night panes light the four front stalls, the gateway recess, the cupola crystal and front
corner lanterns. EA's two horn glow cards stay at their original locations.

## Verification (2026-09-26)

The cupola's column tops and cornice are closed solids, fixing exposed back faces without changing
validation limits. Current body: 1,116 → 3,994 triangles; height 58.30 → 68.66; footprint unchanged.
Checks: 163/163. Day, lifecycle and night comparisons are in
`build/assets/elves/green_pasture/renders/`. Awaiting player review; nothing installed.
