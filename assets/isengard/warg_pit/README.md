# Isengard warg pit (`IsengardWargPit`)

Model `IBWARGPIT`, mesh `IPWARGPIT` (EA's mesh name), own texture `IBWargPiH.tga` (DXT5, EA's
cut-out alpha kept); covers the Draw module `ModuleTag_Draw`. The door is its own Draw module
and model (`IBWARGPIT_DRC`, [warg_pit_02](../warg_pit_02/README.md)) and stays EA's. Palette A;
new pieces from the Isengard kit and [`shapes_industry.py`](../shapes_industry.py) and [`shapes_industry_big.py`](../shapes_industry_big.py). EA's pit is
kept whole: the palisade ring, the bones, the kennel hut and its walled run.

## Pass 4: destacked (2026-09-30)

Max after Mordor: "our furnace towers on everything look a lil stupid" and "super low quality
that tower". The rollout's needle stacks and stamped blade pairs read as bolted-on clones. Each
building now gets its own work instead (new pieces in [`shapes_trades.py`](../shapes_trades.py)),
smaller and fewer, its fire in its own forges, grates, braziers and pits.

- **Out**: the pair, the needle chimney behind the pit, the gatehouse's two blade towers.
- **In**: heavy gate posts carrying the lintel (a battered stone foot, an iron shaft with riveted
  bands past the lintel, a fire basket on each); gnawed bones heaped against the palisade
  (`bone_heap`: long bones, a ribcage, skulls, grey, not the Goblins' bleached bone); chain stakes
  with spiked collars lying in the dirt (`tether`). The yard's middle stays clear for the wargs.
- **Fire** 3 -> 4: the chimney -> the two gate baskets (brazier).

3,224 -> 7,561 triangles (pass 3: 7,114), height +1.6 % (pass 3: +19.7 %), footprint
unchanged, 9/9 preview checks. Sheet: `build/assets/isengard/_review/destack_v1.jpg` (installed
pass 3 against pass 4 at the RTS view).

## Pass 3: up to the citadel

Pass 2 read modest beside the citadel. Pass 3 applies its recipe: the pair, needle stacks,
the Hand in pointed-arch slots, fire. Sheet: `_review/production_v3.jpg`.

- **The pair** (the citadel's): pass 2's three thin pylons (sticks) are gone; two matching
  blades stand either side of the pit in the RTS view, its centre -+ 30 along the view:
  (-19.8, -5.8) on the palisade's front and (17.2, 41.5) outside its back, to z 55.5, two fins a
  face, the White Hand in a pointed-arch slot on each one's outer face.
- **Chimney**: a needle stack on the palisade behind the pit, on the view's axis (-23.7, 35.4),
  to z 50 with its crown and glowing throat (fire).
- The gatehouse over the run stays (its own blade pair either side of the run).
- **Fire** (3: chimney, 2 brazier).

3,224 -> 7,114 triangles, height 48.5 -> 58.0 (+19.7 %), footprint unchanged, 9/9 preview checks.

## Pass 2: the kennels

- **Gatehouse** (the new silhouette): two blade gate towers to z 56 on the run's walls, 9 inside
  the door (flat lozenges, broad faces to the camera, fins, ember slits, needles), a pointed stone
  lintel between them over the run (underside z 33), spikes along it, the White Hand on a shield
  hung from it. Pass 1's pylons at the door and their chain are gone.
- **Pylons**: lozenge blade pylons with silver collars and knife fins in the ring's three outer
  corners (to z 52).
- **Bands**: two iron bands girdle the palisade outside its stakes.
- A rail of meat hooks at the back of the yard; braziers in the yard's corners.
- **Fire** (2 points): the braziers. EA's house-colour banner stays the pit's only one.

3,224 -> 5,586 triangles, height 48.5 -> 58.0 (+19.7 %), footprint unchanged, 9/9 preview
checks. Pass 1 is `_review/production_v1.jpg`.

## Kept clear

- The run: wargs are made at (0, -37) and leave for (70, -37) through the door.
- The door leaf shut (x 31..36, y -46..-28) and swung open (x 33..37, y -30..-13).
- The yard's middle, where the wargs roam; the level-up watchtower on the hut (`V2`).
- EA's night torch posts (`N_WINDOW`).

## Status

- [x] pass 3 built in colour and installed (2026-09-29)
- [x] pass 4 designed (shape preview, 2026-09-30)
- [ ] pass 4 reviewed by Max, built in colour, installed
