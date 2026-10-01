# Isengard burning forges: the forge (`IsengardFortressCitadel`)

Model `IBFBForgB`, mesh `IBFBFORGES`, own texture `IBFortresM.tga` (from `IBFortress.tga`).
`Tier.STANDARD`. The forge tower of the citadel's `FORTRESS_IMPROVEMENT_4` add-on
(`ModuleTag_DrawBurningForgesDescrutbiles`, EA's spelling) over the -X walk; its wheel is
[fortress_burning_forges](../fortress_burning_forges/README.md). EA's body is kept whole: the
battered block, the round stack, the timber frame and its cage of spikes, the chute, the pikes.

## What changed (`forge.py`)

- **Beacon**: a faceted fire-pot on the frame's roof (z 112.4), pointed merlons along the roof's
  edges between EA's corner spikes.
- **Stack** (pass 4, 2026-09-30, Max: "our furnace towers on everything look a lil stupid ... super
  low quality that tower"): pass 3's needle chimney carried on out of EA's round stack to z 138
  went. EA's stack is the forge's stack again, with its own fire in its mouth (z 85.3): two
  riveted iron bands and a silver lip round its rim, six iron spikes leaning out of the lip.
- **Forge**: a hearth with its hood and flue, an anvil with white-hot work, a bellows and ingots on
  the platform's -Y half.
- **Chute**: molten metal running down EA's chute on the +X face into a glowing pool.
- **Face**: three silver-edged knife fins and two ember vents on the -Y face.
- **Fire** (`fire_points`, 5): chimney (EA's stack's mouth, z 84.8), brazier (the beacon),
  hearth, embers (the anvil), crucible (the chute's pool).

## Kept clear

- The wheel's sweep: EA's wheel by y-slab is the disc, its lips and our ribs to r 16.5 over
  world y -4.3..4.2, and the hub drum to r 3.4 as far as y 15.2, about (-42.06, 4.52, 66.22): no
  vertex within 0.5 of it.
- The forge worker at `B_URUKALIGN` (-50.8, 12.8, 63.4).
- The wizard's tower and the excavations' drum (the fins start above its rim, z 21.5).
- The citadel's new solids and fire points: no vertex inside them either way.

## Status

Pass 3 built and installed (2026-09-29). Pass 4 designed, shape preview only: 969 -> 2,299
triangles (pass 3: 2,149), height unchanged (pass 3: +19.6 %), footprint unchanged, fire 5 -> 5,
9/9 preview checks. Sheet: `build/assets/isengard/_review/destack_v1.jpg`. Pass 3: `_review/addons_v3.jpg`.

## Open

- Full build: bake, paint, lifecycle (`IBFBForgB_A`, `_D2`, `_D3`); the fire's look in game.
