# Mordor fortress lava moat (`MordorFortressLavaMoat`)

Model `MBFLavaMoat`, mesh `MBFLAVAMOAT`, own texture `MBFortresE.tga` (from `MBFortress.tga`). An object of its own, spawned at the citadel's centre by its upgrade: EA's ring of rock from the wall's foot out to r 90..108 and its lava plane (`OBJECT01`, S3_Lava), kept whole. EA's sorcery flare `MBFLAVAMEFF` and ground decal `MBFLAVAMALPH` are kept in game and left out of bakes and renders (`bake_hidden`). New pieces
come from the Mordor kit and the add-ons' shared pieces ([`../shapes_addons.py`](../shapes_addons.py)).
EA's facts are in [`building.py`](building.py).

## What changed (`moat.py`)

- **Slag rafts**: dark crusts drifting on EA's lava across the channel (r_out - 26 .. - 16), one to
  three to every 5 degrees, and a glowing bubble every 15 degrees.
- **Basalt teeth** along the outer bank's crest, leaning out, lava glowing at each one's foot;
  **impaling stakes** (two barbs, a steel point) leaning out from the bank: both only between the
  expansions' pads.
- **Fire** (`fire_points`, 5): two thin `smoke` columns and three `embers` off the lava.
- EA's moat measured by raycast (`moat.py` RING: the outer edge and the crest's height every 5
  degrees).

## Kept clear

- The expansions' pads (EA's base file `bases\fortress_mordor`: -90, 180, 90, +-45, +-135 degrees,
  114.5 or 129 out; the bodies reach back to r 48.7, up to 22.7 to each side): teeth and stakes
  stand only between them; the rafts, flat on the lava, run under them.
- The ramp and the citadel's ramp stakes (17.7 and 19.2 degrees): no raft within 22 degrees of +X
  (the first pass had 30 face pairs through the stakes), no tooth or stake within 20. No face
  crosses the citadel's new faces now; the nearest citadel fire point is 10.2 away.

## Status

Designed, shape preview only (not built, not installed). Pass 1: 630 -> 4,869 triangles, height 16.9 -> 18.0 (+6.4 %), footprint unchanged, 9/9 preview checks. Checked on our citadel
(pass 7) with every add-on built at once. Review sheet: `build/assets/mordor/_review/addons_v2.jpg` (unchanged in pass 2).

- [x] healthy body designed (pass 1)
- [x] preview checks pass, reviewed on the sheet
- [ ] Max's review, then build and install

## Open

- EA's inner bank (z 3..12 at the wall's foot) covers the citadel's own lava channels at the -Y and +X wall feet once the moat is built: EA's moat, not ours; worth a look in game.
- Full build: bake, paint (no lifecycle models in its Draw).
