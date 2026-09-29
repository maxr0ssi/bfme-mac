# Isengard armory (`IsengardArmory`)

Model `IBArmory_SKN`, mesh `IBARMORY`, own texture `IBArmorH.tga` (DXT5, EA's cut-out alpha
kept). Palette A; new pieces from the Isengard kit and [`shapes_industry.py`](../shapes_industry.py) and [`shapes_industry_big.py`](../shapes_industry_big.py).
EA's body is kept whole; the treadwheel and grindstone meshes stay EA's.

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

- [x] healthy body designed (pass 3, shape preview)
- [ ] reviewed by Max, built in colour, installed
