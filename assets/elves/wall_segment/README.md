# Elven wall segment (`ElvenCastleWallSegment`)

Model `EBWallN`, redesigned mesh `EBWALLN`, `Tier.STANDARD`, painted from `EBFortress.tga` onto its
own textures `EBFortresB.tga` / `EBFortresB_NRM.tga` (+ `_D`, `_snow`, `_U` variants), DXT5 (EA's
cut-out alpha kept).

EA's segment is a slender lancet wall: a wall face at |x| 3.06, piers to |x| 4.9 at the middle and
the ends, two tall lancet windows per face with lattice glass, pointed hoods over them and a V
cornice between, a low ridge on top. It keeps all of it and gets the walls' crown and the Elven
windows. Walls tile and the engine may stretch a segment along y, so only the crown reaches the
ends (y = +-19), and everything stays inside EA's footprint (x +-4.9, y +-19). Both faces are the
same (either may face the enemy).

## What changed (body, healthy)

- **Crown** (the shared profile below): a stone core burying EA's ridge, a filigree band (silver
  knots on sea-green enamel between two gilt beads), a silver-moulded coping, and ten lancet
  merlons on each face.
- **Windows:** a silver arch frame round each of EA's four lancet windows, sea-green enamel on its
  reveal and soffit, a slight leaf tip (ogee 0.25) and a gilt leaf finial under EA's hood.
- **Banners:** a leaf banner hung in each window recess in front of the lattice, on a gilt rod with
  leaf-bud ends and a gilt midrib (4 per segment). The cloth leaves the body for our house-colour
  model `EBHCWallN` (the player's colour), Draw tag `ModuleTag_Draw_HCWallSegment`.
- **Paint:** the faction style (moonstone ashlar, silver trim, sea-green enamel, mallorn gold).

Footprint unchanged, height 51.2 -> 59.0 (+15.2 %, limit 20 %), 326 -> 3,142 triangles
(48 cloth faces moved to `EBHCWallN`). `checks`: 84/84 pass.

## The wall profile (`wall.py`, shared by the segment, the wall end, the hub and the gate)

| Line | Value (z) | Where |
|---|---|---|
| EA's cornice | 42.0 -> 46.22 -> 49.1 | V cornice / pointed hoods, back to the face at the top edge 49.1 |
| core | 48.9 .. 51.3 | stone, buried in EA's cornice, burying EA's ridge (51.2) |
| filigree band | 49.3 .. 50.9 | 0.3 proud of the face line, gilt beads 0.48 |
| coping | 51.2 .. 53.0 | silver moulding, nose 0.45 out of the face line |
| lancet merlons | 53.0 .. 59.0 | 2.0 wide, fronts 0.1 out, backs 1.1 in; each run divides its length by about 4.0, half a gap at each end |
| window arch frames | 0 .. 37.1 (+ finial) | EA's windows: 9.8 wide, spring 30.81, apex 37.1; frame 0.9 wide, 0.8 proud |
| window banners | 29.6 .. 9.6 | in the recess, 1.5 in front of the lattice, 5.0 wide |

The face line is |x| 3.06 on straight pieces, a 20-gon of corner radius 22.3 on the hub and a
square of half size 9.7 round the gate's tower heads. The nose is kept small (0.45, beads 0.48)
because the hub's footprint (y +-22.83) leaves its crown only 0.24 past EA's rim; every piece takes
the same.

## Status (`python3 -m sagekit inventory elves/wall_segment`)

| Part | Healthy | Construction (`_A`) / damaged (`_D1`) / placement (`_CUR`) / snow / stonework | Really damaged, collapsing (`_D2`, `_D3`) |
|---|---|---|---|
| body (`EBWallN`) | done, rendered, not installed | derived: our body on the variant sheets (the cursor through `also_derived`) | rebuilt by the lifecycle step around our body |
| rubble (`GBWall_Rubble`) | not ours: shared by six factions | | |

## Night lights

TODO: EA's Elven wall objects name no `NightWindowName` and their models carry no night meshes,
so the night step has nothing to light (`work/night.json` names are empty). The crystal lanterns
on the hub, the gate and the wall end are the natural places for starlight once a wall piece gets
a night mesh of its own.
