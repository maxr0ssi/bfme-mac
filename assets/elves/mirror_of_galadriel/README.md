# Mirror of Galadriel (`ElvenMirrorOfGaladriel`, `galadrielswell.ini`)

Model `EBGalMirr` has four meshes on identity bones, all painted from `EBGalMirr.tga` (+ `_NRM`).
The redesigned mesh is the stair, `EBGALMIRR1`. Its own texture is `EBGalMirH.tga` (+ `_NRM`,
`_Snow`); new faces are mapped onto the faction atlas. `Tier.STANDARD`.

The basin and pedestal (`EBGALMIRR3`), the octagonal dais (`EBGALMIRR2`) and the mallorn roots that
grip it (`EBGALMIRR4`) stay EA's, byte for byte: the water, the knotwork and the living roots are
kept.

## The original (measured, model coordinates)

- **Pedestal and basin:** round (-13.85, 0), radius 7.8, z 5.6..28.0, on the dais (corners on the
  axes at radius 10.45, top z 5.6).
- **Stair:**
  - a landing (top z 4.9) whose point is at (9.6, 0);
  - two mirrored flights of five chevron slabs, 0.7 apart (tops 4.2 .. 1.3), running out to
    y +-31.6.
  - Its box, x -3.41..24.22, |y| <= 31.57, is the footprint.
  - Each flight's outer side follows the slabs' points and its inner side their tails (`TIPS`,
    `TAILS` in `building.py`, from EA's vertices).

## What changed (body, healthy)

- **Balustrades:** each flight has a silver balustrade down both sides. Turned balusters stand on
  every tread at about 1.55 apart, each on the slab under it. A rounded rail 2.5 over the treads
  falls straight from the top to the foot, with gilt caps at its ends.
- **Lanterns:** a lantern column (moulded pedestal, fluted shaft, gilt leaf capital, crystal
  lantern) stands at both corners of each flight's foot. A taller one stands on the landing where
  the flights part.
- **Banner poles:** two gilt banner poles on the landing's back corners, in front of the dais. Their
  leaf banners face the approach and their pennants fly along +y. The cloth goes to `EBHCGalMirr`
  (house colour).
- **Paint:** the slabs are repainted in the Elven moonstone.

Footprint unchanged. Stair height 4.92 -> 20.64. `max_z_growth` is 3.4 because the stair is only
4.9 high while the model is the basin's 28.0; the model's height is unchanged. Triangles 236 ->
8,382 (`tri_budget` 11,000; the balusters are most of it). Texel density median 29.6 px/unit.
`checks`: 63/63.

## Status

| Part | Healthy | Construction | Damaged / really damaged / rubble | Snow | LOD M/L |
|---|---|---|---|---|---|
| stair (`EBGalMirr`) | built, checks pass, **awaiting review** | derived (`EBGalMirr_A`) | EA's (`_D1`, `_D2`, `_D3`: the lifecycle step found no pieces of this body in them) | `EBGalMirH_Snow` painted | old |
| banner (`EBHCGalMirr`) | our 2 banners' cloth added (shown after `sagekit house elves`) | | | | |

## Notes

- **An earlier version** took the roots as the target and set the dais in a two-tier moonstone
  terrace with a curved balustrade. It buried the roots and could not reach the stair: the roots'
  box stops at |y| 17.7, and the check allows no new geometry past the target's box. The stair
  target keeps the roots alive and makes the stair the design.
- **Night.** The model has no night meshes (`N_*`), so no lights are declared and the crystal
  lanterns stay dark at night.
