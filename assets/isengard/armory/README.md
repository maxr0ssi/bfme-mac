# Isengard armory (`IsengardArmory`)

Model `IBArmory_SKN`, mesh `IBARMORY`, own texture `IBArmorH.tga` (DXT5, EA's cut-out alpha
kept). Palette A; new pieces from the Isengard kit and [`shapes_industry.py`](../shapes_industry.py) and [`shapes_industry_big.py`](../shapes_industry_big.py).
EA's body is kept whole; the treadwheel and grindstone meshes stay EA's.

## Pass 4: destacked (2026-09-30)

Max after Mordor: "our furnace towers on everything look a lil stupid" and "super low quality
that tower". The rollout's needle stacks and stamped blade pairs read as bolted-on clones. Each
building now gets its own work instead (new pieces in [`shapes_trades.py`](../shapes_trades.py)),
smaller and fewer, its fire in its own forges, grates, braziers and pits.

- **Out**: the pair and the needle stack through the hall's roof.
- **In**: a grinding wheel in the +X gable's yard (a stone disc with silver rims on an iron axle
  between A-frames, a crank, a trough of water, a blade on the rest, sparks), a firebox in the
  gable's mouth (the hall's own fire), a shield rack facing the camera, a rack of seven pikes
  under the -Y eaves. The banner moved to (34.5, 41.5).
- **Fire** 6 -> 7: the chimney became the hall's firebox (furnace); the wheel's sparks (embers)
  are new.

468 -> 4,149 triangles (pass 3: 5,183), height +13.2 % (pass 3: +19.4 %), footprint
unchanged, 9/9 preview checks. Sheet: `build/assets/isengard/_review/destack_v1.jpg` (installed
pass 3 against pass 4 at the RTS view).

## Pass 3: up to the citadel

Pass 2 read modest beside the citadel. Pass 3 applies its recipe: the pair, needle stacks,
the Hand in pointed-arch slots, fire. Sheet: `_review/production_v3.jpg`.

- **The pair** (the citadel's): two matching blades either side of the hall's +X gable in the
  RTS view, (17.5, 27.9) and (28.5, 42.1), the gable's middle -+ 9 along the view, to z 54.4 (the
  +20 % limit: EA's armory is low), two fins a face, ember slits, the White Hand in a
  pointed-arch slot on each one's outer face; the gable's own great Hand between them.
- The hall's ridge lowered to z 44 and its crest shortened so the pair reads over it; its corner
  fins went (the blades clasp that corner).
- The banner moved to (34.3, 32.5), 7 wide, clear of the right blade and inside the footprint.
- **Fire** (6: chimney, hearth, crucible, 3 brazier).

468 -> 5,183 triangles, height 46.9 -> 56.0 (+19.4 %), footprint unchanged, 9/9 preview checks.

## Pass 2: the Uruk armoury

- **Hall** (the new silhouette): the shed becomes an iron hall, a steep pointed roof (42 degrees
  at the apex) from eaves at z 17 to a ridge at z 45.5, silver eaves, a crest of blades, stone
  gables with silver edges; the White Hand great in a pointed-arch slot in the +X gable over the
  shed's opening; layered stone fins at its +X corners.
- **Stack**: a lozenge needle stack up through the hall's -Y slope.
- **Forge** in the open yard: hearth, anvil with white-hot work, bellows, a square crucible,
  ingots, quench trough, tool rack.
- **Arms**: three Uruk harnesses on stands (breastplate, pauldron blades, pointed helm, shield
  with the Hand, pike); a shield rack and a cleaver rack on the deck, pikes along its fence.
- One banner on an iron frame, three braziers.
- **Fire** (6 points): chimney, hearth, crucible, three braziers. EA's sparks at the grindstone stay.

468 -> 3,481 triangles, height 46.9 -> 54.8 (+17.0 %), footprint unchanged, 9/9 preview
checks. Pass 1 is `_review/production_v1.jpg`.

## Kept clear

- The treadwheel (`IBARMORYWHEEL1`), the grindstone (`IBARMORYWHEEL2`) and its sparks, the slave
  who works it.
- The level-up tower (`V1A`, `V2`: x -26..9, y -51..-9).
- EA's night torch posts (`N_WINDOW`).

`work/measure.json` still describes the treadwheel (the scaffolder's first pick); the recipe's
docstring has IBARMORY's facts.

## Status

- [x] pass 3 built in colour and installed (2026-09-29)
- [x] pass 4 designed (shape preview, 2026-09-30)
- [ ] pass 4 reviewed by Max, built in colour, installed
