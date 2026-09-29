# Isengard citadel (`IsengardFortressCitadel`, `IsengardFortress`)

Model `IBFortress`, mesh `IBFORTRESS`, own texture `IBFortresH.tga` (from `IBFortress.tga`).
`Tier.HERO`. Palette A "Orthanc black and silver" ([`style.py`](../style.py)); new pieces come from
the Isengard kit ([`shapes.py`](../shapes.py), [`shapes_works.py`](../shapes_works.py),
[`shapes_yard.py`](../shapes_yard.py)). EA's body is kept whole; the back wedge tower is built
up into the foundry.

## Pass 3 (shape preview only)

Pass 2 read as a silo (a plain drum hiding EA's spire), the Hand was painted across it, and the
story pieces stood at ground level where the RTS camera loses them.

- **Foundry tower** (`foundry.py`), in EA's Gothic: an undercroft (a solid back half, four piers,
  pointed arches, furnace mouths glowing in its back wall; one pier corbelled from z 15.5 and
  none at 315 degrees, over the excavations upgrade's rails and derrick), tier 1 (z 24..50) with
  lancets and stepped buttresses to spiked pinnacles, merlons with spikes on its ledge, tier 2
  (z 50..80) set back with lancets, silver corner shafts, the White Hand small in a pointed-arch
  panel, merlons and a pinnacle on every corner. The roof stays open at z 80 for the orcfire
  cauldron, and EA's spire rises out of it. The great stack (spiked collar) on the back corner,
  a crane boom rising diagonally over the courtyard with a crucible, a bellows house on the walk.
- **Walks** (`yard.py`): -Y a log stack and frame saw (felled Fangorn), a gantry lifting a
  crucible off a floor grate, a tool rack, an anvil, a fire grate at the stack, a brazier; +Y a
  shield rack, a forge, a winch, a brazier, pipes from the stack to the forge and the bellows
  house; front a shield rack, a floor grate, a brazier. Spiked collars on both side stacks, a
  cable from the +Y stack to the great stack.
- **Walls and towers** (`yard.py`, `walls.py`): the dammed Isen on the -Y wall face (a flume from
  a sluice box in the wall onto an overshot water wheel, z 19..37, turning two gears);
  scaffolding up the +X -Y tower's outer face to z 58 with a half-built siege ladder; silver caps
  on EA's curtain pinnacles and collars under the towers' points; lanterns on brackets; spikes;
  two banners.

3,876 -> 14,506 triangles (budget 15,000), height 91.4 -> 121.7 (+33.1 %), footprint
unchanged, 9/9 preview checks, no upgrade (excavations, burning forges, wizard's tower) inside
the new solids. Review sheet: `build/assets/isengard/_review/citadel.jpg` (earlier passes:
`citadel_v1.jpg`, `citadel_v2.jpg`).

## Kept clear

- The courtyard: the upgrades stand there (the wizard's tower `IBFWTower` at the centre to
  z 175.7, the excavations, the burning forges over the -X wall, orcfire munitions on the walls).
- The orcfire munitions upgrade: a cauldron on each tower top ((+-37.4, +-37.7), z 80.2..93.7,
  fire to z 110). Pass 1's stack on the -X -Y tower stood in it; pass 2 moved it.
- The gate opening (x > 73, |y| < 11, z < 43).

## Status

- [x] palette chosen (A, with silver)
- [x] healthy body designed (pass 3, shape preview)
- [ ] built, renders reviewed
