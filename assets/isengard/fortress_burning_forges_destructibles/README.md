# Isengard burning forges: the forge (`IsengardFortressCitadel`)

Model `IBFBForgB`, mesh `IBFBFORGES`, own texture `IBFortresM.tga` (from `IBFortress.tga`).
`Tier.STANDARD`. The forge tower of the citadel's `FORTRESS_IMPROVEMENT_4` add-on
(`ModuleTag_DrawBurningForgesDescrutbiles`, EA's spelling) over the -X walk; its wheel is
[fortress_burning_forges](../fortress_burning_forges/README.md). EA's body is kept whole: the
battered block, the round stack, the timber frame and its cage of spikes, the chute, the pikes.

## What changed (`forge.py`)

- **Beacon**: a faceted fire-pot on the frame's roof (z 112.4), pointed merlons along the roof's
  edges between EA's corner spikes.
- **Stack**: four knife blades round the rim of EA's round stack, fire and smoke out of it.
- **Forge**: a hearth with its hood and flue, an anvil with white-hot work, a bellows and ingots on
  the platform's -Y half.
- **Chute**: molten metal running down EA's chute on the +X face into a glowing pool.
- **Face**: three silver-edged knife fins and two ember vents on the -Y face.
- **Fire** (`fire_points`, 5): chimney (the stack), brazier (the beacon), hearth, embers (the
  anvil), crucible (the chute's pool).

## Kept clear

- The wheel's sweep (a disc r 16.4 about (-42.06, 4.52, 66.22), y -6.2..15.2): no vertex in it.
- The forge worker at `B_URUKALIGN` (-50.8, 12.8, 63.4).
- The wizard's tower and the excavations' drum (the fins start above its rim, z 21.5).
- The citadel's new solids and fire points: no vertex inside them either way.

## Status

Designed, shape preview only (not built, not installed). 969 -> 1,943 triangles, height and
footprint unchanged, 9/9 preview checks.

## Open

- Full build: bake, paint, lifecycle (`IBFBForgB_A`, `_D2`, `_D3`); the fire's look in game.
