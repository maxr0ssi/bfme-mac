# Angmar forge works (`AngmarForgeWorks`)

Model `KBForge`, mesh `BASE` (a skin: docs/ART.md, "A skinned body"), own texture `KBForgH.tga`
(from `KBForge.tga`). Palette A2. EA's hall, furnace drum and troll yard are kept whole.

## Pass 1: the crowned furnace

- **Four forged tines** of the Witch-king's crown with frozen tips rise from the furnace drum's rim
  round EA's own fire ([`../shapes_addons.py`](../shapes_addons.py)), clear of the level-2 horns
  either side of the drum.
- **EA's six roof horns** are frozen from about 60 % of their height (`freeze`), **icicles** hang
  under both eaves of the long roof, and **ice drifts** climb the hall's feet.
- **The yard walls** carry Carn Dum's merlons (flush on the west wall, EA's footprint edge) and a
  corbel with icicles on the south wall, as on the mill's ring.
- **The bellows lever** gets two iron bands and a frosted iron head with spurs. They ride EA's
  `BONEPUMP` and rise and fall with the troll's pumping (`renders/anim/compare_kbforge_idle_yard.png`).

6,492 triangles (EA 1,991). Footprint unchanged, height +1.2 %. The build-up, damaged, really damaged
and rubble models are all rebuilt along EA's pieces. No new fire: EA's furnace fire burns in the drum.

## Status

- [x] skinned body: EA's bones, animation and skin weights byte for byte (checks)
- [x] healthy body designed (pass 1), built in colour, lifecycle, staged
- [ ] reviewed by Max
- [ ] checked in game
