# Angmar fortress spikes (`AngmarFortressSpikes`)

Model `KBFSpike`, mesh `KBFSPIKES`, own texture `KBFortressQ.tga` (from `KBFortressX.tga`). An object
of its own, spawned at the citadel by `Upgrade_AngmarFortressSpikes`: EA's 26 clumps of curved spikes
on stone feet round the wall feet (r 80..108, the gate left open), kept whole. EA's facts are in
[`building.py`](building.py).

## What changed

- **Frozen spikes** (the bold mass): every tall spike (21, to z 33.5..46.2) is cased in ice from
  about half its height to its point, under a ragged frost line, rime on the last stretch, three
  crystals growing out of the casing. The casing follows each spike's own section, read from EA's
  mesh at design time (`frozen_spikes` in [`../shapes_addons.py`](../shapes_addons.py)), so it hugs
  every curve. The moat's chill (EA's slowing aura) made visible; the same frost as the citadel's
  tines and the ice at its feet.
- No fire: the chill is EA's aura, the cold fire burns in the citadel's crown.

## Kept clear

- Inside EA's footprint (casings and crystals clamped to it).
- No new face crosses the citadel's new faces.
- **Open, not ours to fix**: EA's clumps stand among the citadel's wall-foot ice clusters and
  frost fissures (fortress/walls.py; 1,009 of EA's faces cross them, as EA's spikes cross EA's own
  plinth). Spikes frozen into the ice read as one, but it is a crossing.

## Status

Pass 1, shape preview only (not built, not installed): 1,326 -> 3,657 triangles, z 45.7 -> 46.9
(+2.6 %), footprint unchanged, 9/9 preview checks. Review sheet:
`build/assets/angmar/_review/addons_v1.jpg`.

- [x] healthy body designed (pass 1)
- [x] preview checks pass, reviewed on the sheet
- [ ] Max's review, then build and install

## Open

- Full build: bake, paint; its house model (HOUSE_DRAW, from the style's template).
- The crossing with the citadel's wall-foot ice (citadel).
