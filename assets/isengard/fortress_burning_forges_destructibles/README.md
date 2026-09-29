# Isengard burning forges: the forge (`IsengardFortressCitadel`)

Model `IBFBForgB`, mesh `IBFBFORGES`, own texture `IBFortresM.tga` (from `IBFortress.tga`).
`Tier.STANDARD`. The forge tower of the citadel's `FORTRESS_IMPROVEMENT_4` add-on
(`ModuleTag_DrawBurningForgesDescrutbiles`, EA's spelling) over the -X walk; its wheel is
[fortress_burning_forges](../fortress_burning_forges/README.md). EA's body is kept whole: the
battered block, the round stack, the timber frame and its cage of spikes, the chute, the pikes.

## What changed (`forge.py`)

- **Beacon**: a faceted fire-pot on the frame's roof (z 112.4), pointed merlons along the roof's
  edges between EA's corner spikes.
- **Stack** (pass 3): EA's round stack carried on as the citadel's needle chimney: a lozenge
  flange over its rim (z 84), an ember-lit spiked collar, fins up its sharp edges, a crown of
  blades round a glowing throat at z 138 (the crown to z 148), past the frame's roof (112.4): the
  forge's one tall mass. A pair of blades on the block's -X corners, tried first, stood beside the
  citadel's own pair and read as a bundle of needles.
- **Forge**: a hearth with its hood and flue, an anvil with white-hot work, a bellows and ingots on
  the platform's -Y half.
- **Chute**: molten metal running down EA's chute on the +X face into a glowing pool.
- **Face**: three silver-edged knife fins and two ember vents on the -Y face.
- **Fire** (`fire_points`, 5): chimney (the stack's throat, z 133.8), brazier (the beacon),
  hearth, embers (the anvil), crucible (the chute's pool).

## Kept clear

- The wheel's sweep: EA's wheel by y-slab is the disc, its lips and our ribs to r 16.5 over
  world y -4.3..4.2, and the hub drum to r 3.4 as far as y 15.2, about (-42.06, 4.52, 66.22): no
  vertex within 0.5 of it.
- The forge worker at `B_URUKALIGN` (-50.8, 12.8, 63.4).
- The wizard's tower and the excavations' drum (the fins start above its rim, z 21.5).
- The citadel's new solids and fire points: no vertex inside them either way.

## Status

Designed, shape preview only (not built, not installed). Pass 3: 969 -> 2,149 triangles, height
124.0 -> 148.3 (+19.6 %), footprint unchanged, 9/9 preview checks. Review sheet: `build/assets/isengard/_review/addons_v3.jpg` (pass 3; `addons.jpg` is pass 1).

## Open

- Full build: bake, paint, lifecycle (`IBFBForgB_A`, `_D2`, `_D3`); the fire's look in game.
