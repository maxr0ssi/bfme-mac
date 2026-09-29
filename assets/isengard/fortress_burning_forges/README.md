# Isengard burning forges: the wheel (`IsengardFortressCitadel`)

Model `IBFBForges`, mesh `IBFBFORGESA`, own texture `IBFortresL.tga` (from `IBFortress.tga`).
`Tier.STANDARD`. The turning wheel of the citadel's `FORTRESS_IMPROVEMENT_4` add-on
(`ModuleTag_DrawBurningForges`); the forge it turns in is
[fortress_burning_forges_destructibles](../fortress_burning_forges_destructibles/README.md).
EA's wheel is kept whole: the twelve-sided disc, its ribs, rods and hooked lobes, the hub drum.

## What changed (`wheel.py`)

- Six silver-edged iron ribs on each face between EA's ribs.
- Six pointed ember vents glowing in each face.
- A riveted hexagonal iron boss round EA's axle end on the -y face.

## Kept clear

- The forge's slot: `IBFBForges_AN` turns the wheel once every 180 frames about its bone's y axis,
  through a slot in the forge tower (world |y| < 3.8, z 49..62). Every piece turns with the wheel,
  stays within r 16 of the hub, and below the hub stands at most 0.8 off the faces.

## Status

Designed, shape preview only (not built, not installed). 957 -> 1,513 triangles, height and
footprint unchanged, 9/9 preview checks. No fire: a fire rig would stand still while the wheel
turns; the forge carries the fire.

## Open

- Full build: bake, paint, lifecycle (`IBFBForges_A`).
