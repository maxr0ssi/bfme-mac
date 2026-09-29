# Goblin spider holes (`WildSpiderHolesExpansion`)

Model `WBSHole`, mesh `WBSHOLE`, own texture `WBFortresF.tga` (from `WBFortress.tga`).
`Tier.STANDARD`. A fortress expansion on its pad. EA's body is kept whole: the tall plated crest,
the scaled carapace, the brow over the dark spawn hollow, the low wavy ground ring.

## What changed

The carapace becomes a great dead spider the Goblins breed their spiders in.

- **Legs**: four pairs of jointed legs rise off the carapace to knees at z 44 and kink out and
  down to pointed feet on the ground ring, fanned like a spider's: crimson chitin, bleached bone
  knuckles and bristles, a spike on each knee, an iron band below it.
- **Cocoons**: two hide sacks hung on cords from the front legs' shins.
- **Pad** ([`../arrow_den/pad.py`](../arrow_den/pad.py)): a skirt of black rock along the ground
  ring's top and the back wall; skull piles and a bone by the legs' feet.
- **Gore**: the `Gore` paint layer under the piles and the cocoons.
- **Banners**: none (cap 0).

## Kept clear

- The spawn hollow at the front: nothing new at x > -2, |y| < 11.

## Status

Installed. 348 -> 4,139 triangles, height 46.8 ->
49.4 (+5.4 %, the knee spikes), footprint unchanged, 9/9 preview checks.

## Open

- Full build: bake, paint, lifecycle (`WBSHole_A`, `_D2`, `_D3`).
