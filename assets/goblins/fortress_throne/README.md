# Goblin throne (`WildFortressCitadel`, the dragon's nest upgrade)

Model `WBFGThrone`, mesh `WBFGTHRONE`, own texture `WBFortresC.tga` (from `WBFortress.tga`).
`Tier.STANDARD`. Drawn on the [citadel](../fortress/README.md) once the upgrade is bought. EA's
sculpt is kept whole: the rearing dragon, its crest, wings, forelegs gripping the bowl, open
jaws, the flared nest and the niche where the fire drake idles. It is not skinned.

## What changed

- **Head** (`dragon.py`): two great crimson horns sweeping back to bleached tips, a spiked iron
  crown round the horn roots, a frill of bone spikes behind the jaw, bloodied bone fangs, two
  boar tusks, blood running off the lip.
- **Neck**: a riveted iron collar with four spikes; a chain across the chest with a skull at
  the throat.
- **Crest and wings**: bleached spikes from every tip of EA's crest; a bone spur on each wing
  tip, a skull on the left one.
- **Forelegs**: iron shackles chained to rings on the nest's flare; bloodied bone talons.
- **Nest** (`nest.py`): an iron band round the waist, great tusks rising off the rim like a
  ribcage, fire bowls on brackets, a horned troll skull over the front, skull heaps and bones
  round the foot on the courtyard floor (z 5..6.7).
- **Gore**: the `Gore` paint layer at the mouth, claws, pendant, troll skull and piles.
- **Banners**: none (the citadel carries three).

## Kept clear

- The drake's perch `B_DRAKE` (12.8, 0, 74.5) and the bowl round it (nearest new piece 13 away);
  the chest niche; `FXMOUTH` and the eyes `FXEYE01/02`; the mesh `P1`, which stays EA's.

## Status

Installed with the Goblin pack. 854 -> 8,690 triangles, height 173.5 unchanged (the horns stay
under EA's crown), footprint exactly EA's, 89/89 checks. Every lifecycle state carries the
redesign: construction (animated rise), really damaged and rubble are rebuilt along EA's pieces.
EA's UV overlap (1.42 %) is gone with `facet_islands = 8`. No night lights (no night meshes).

## Known limits

- EA's pale highlights recolour to bone white, so the snout reads light against the crimson.
