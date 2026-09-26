# Dwarven castle-wall segment (`DwarvenCastleWallSegment`)

Model `DBWallRamp2`, redesigned mesh `GBWALLRAMP2`, `Tier.STANDARD`. Its sheet `DBWall.tga` is
EA's 256 placeholder (it reads "Dwarven Wall"): no face samples it any more; every face is new and
painted from the faction atlas `DBFortress1` onto the own texture `DBWalS.tga` (no normal map:
EA's sheet has none). The old castle walls are not built by players; map makers placed them
(Erebor, Withered Heath, Fornost, Helm's Deep), so they take the new walls' look.

## What changed (body, healthy)

EA's model is an unfinished stand-in: a core block (x +-23.77, y +-20.91, z -47.61 to the
walkway at 51.91), a 4.33 overhang on both faces under solid parapets (to z 63.92), and a ramp
from the walkway to the ground at each end (y +-20.91 .. +-62.93, x +-21.66). `wall.clear_target`
removes its faces in `design()` and every volume is rebuilt:

- **Wall section** (`wall.py`, shared with the gate's stubs): the new walls' profile at the old
  section's size - battered plinth down to the core's foot, three-step corbels (five per face)
  carrying a flat overhang, the rune band (Erebor-blue enamel, gold runes) on its face at 27.8,
  a bronze drip band, the coping (top 57.0, like the new walls) and the fortress's chevron
  parapet (five slabs per face, 56.6 .. 63.6).
- **Faces:** a dwarf-statue pilaster in the middle and a banner (4.4 x 17) in each bay; the cloth
  goes to our house-colour model `DBHCWallRamp2` (Draw tag `ModuleTag_Draw_DBHCWallRamp2`).
- **Ramps:** a Dwarven stair down each (18 treads between sloping side walls with bronze copings,
  a stepped newel with a gilded point at each foot).

Footprint EA's (x +-28.1, y +-62.93), ends and walkway unchanged; top 63.92 -> 63.6.
106 -> 1,432 triangles. `checks`: 29/29 pass.

## Profile (shared with `oldwall_gate`'s wall stubs, which are 0.13 lower: walkway 51.78)

| Line | z (segment) | Where (\|x\|) |
|---|---|---|
| walkway | 51.91 | EA's, \|x\| <= 23.77 |
| overhang underside, corbels | 44.69; corbels 39.1 .. 44.69 | 23.77 -> 27.8 |
| rune band | 44.69 .. 51.2 | face 27.8 |
| drip band | 51.2 .. 52.6 | 28.1 (EA's parapet face, the footprint) |
| coping | face 28.0 to 56.6, top 57.0 | walkway side 23.77 |
| chevrons | 56.6 .. 63.6 | 23.97 .. 28.0 |
| plinth | foot -47.61 .. 6.3 | foot 26.07 |

## Status (`python3 -m sagekit inventory dwarves/oldwall_segment`)

| Part | Healthy | Other states |
|---|---|---|
| body (`DBWallRamp2`) | done, rendered, not installed | none exist: the object has no other condition states and no `_A`/`_D*` models |

## Framework notes

- The three old castle-wall models are painted from a placeholder sheet, so the two-sheet build's
  "old faces keep their sheet" would keep the words "Dwarven Wall" on them. The recipes delete
  EA's faces inside `design()` (a side effect on the target mesh). A `Building` flag for this
  (rebuild everything, old sheet unused) would make it explicit.
- `add_solids` fans every kept polygon from its first point: a sweep's end cap of a non-convex
  profile can get a flipped triangle (hit on the gate's head; split into convex sweeps there).
