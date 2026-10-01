# Isengard lumber mill (`IsengardLumberMill`)

EA's Mordor mill `MBLumMill_SKN`, mesh `LUMBERMILL`, shipped as our own model `IBLumMill_SKN` on
our own sheet `MBLumberMilX.tga`, with an own house copy of `MBHCLumberMill` (Goblins and Mordor
draw EA's; the Goblins' copy is `WBLumMill_SKN` on `MBLumberMilH.tga`). Palette A. EA's yard is
kept whole: the lean-to shed and its log stacks, the stumps, the great log on its sawhorses,
the fire pit (`FIRE01` stays EA's).

## Pass 4: destacked (2026-09-30)

Max after Mordor: "our furnace towers on everything look a lil stupid" and "super low quality
that tower". The rollout's needle stacks and stamped blade pairs read as bolted-on clones. Each
building now gets its own work instead (new pieces in [`shapes_trades.py`](../shapes_trades.py)),
smaller and fewer, its fire in its own forges, grates, braziers and pits.

- **Out**: both spire stacks, the second kiln, the blade crane (a blade tower as its mast).
- **In**: a felled giant of Fangorn across the front yard (`fangorn_trunk`: root plate, broken
  limbs, iron dogs, a chain), the great frame saw standing in its trunk (`trunk_saw`), its limbs
  burning on a slash pyre beside it; one charcoal kiln, its own throat alight; an iron gantry over
  the crib of felled Fangorn, a trunk slung from it. The kiln's bands now sink into its faces (a
  sliver of sky showed their backs once the stacks were gone).
- **Fire** 5 -> 5: two kiln chimneys -> the kiln's throat and the slash pyre (hearth).

1,204 -> 3,893 triangles (pass 3: 4,784), height +10.8 % (pass 3: +18.8 %), footprint
unchanged, 9/9 preview checks. Sheet: `build/assets/isengard/_review/destack_v1.jpg` (installed
pass 3 against pass 4 at the RTS view).

## Pass 3: up to the citadel

Pass 2 read modest beside the citadel. Pass 3 applies its recipe: the pair, needle stacks,
the Hand in pointed-arch slots, fire. Sheet: `_review/production_v3.jpg`.

- **The pair** (the citadel's): the two square kilns are lowered to feet (17 high, a corner to
  the camera, iron bands, corner blades, ember vents) and a great spire stack rises out of each
  (`spire_stack`, z 2 to 47.5, a crown of blades round a glowing mouth, two rows of ember
  slits), mirrored either side of the banner at the yard's front. Pass 2's kilns read as black
  boxes at the RTS view. The fire moved from the kilns' throats to the stacks' mouths.
- Slits only below the taper: higher ones stood out of the shaft and showed their open backs.
- **Fire** (5: 2 chimney, hearth (EA's fire pit), 2 brazier).

1,204 -> 4,784 triangles, height 50.0 -> 59.4 (+18.8 %), footprint unchanged, 9/9 preview checks.

## Pass 2: Fangorn's end

Pass 1's charcoal kilns were round; its log pile and gantry vanished at the RTS view.

- **Kilns**: a pair of steep square charcoal kilns (to z 27) on the +X-Y front, a corner to the
  camera, a battered plinth, iron bands, a blade out of each corner past the glowing throat,
  pointed ember vents on every face; the banner on its iron frame between them.
- **Crane**: a lozenge iron mast to z 55 on the +X side, flared and spurred, a laced iron jib
  over the logs, stays to the mast head, a trunk slung from the jib's head.
- **Logs**: a crib of felled Fangorn in five crossed courses under the jib, a pointed iron stake
  at each corner.
- **Crest**: eleven iron blades along the shed's front beam.
- **Saw**: a great frame saw over a trunk on trestles in the -Y yard.
- **Fire** (5 points): chimney in each kiln, hearth at EA's fire pit, two braziers.

1,204 -> 3,836 triangles, height 50.0 -> 59.4 (+18.8 %), footprint unchanged, 9/9 preview
checks. Pass 1 is `_review/production_v1.jpg`.

## Kept clear

- The yard between the stumps and the log, where the orcs work.
- The level-up watchtower's corner (`V2`, x -57..-22, y -51..-16).
- EA's night torch posts (`N_WINDOW`).

## Status

- [x] pass 3 built in colour and installed (2026-09-29)
- [x] pass 4 designed (shape preview, 2026-09-30)
- [ ] pass 4 reviewed by Max, built in colour, installed
