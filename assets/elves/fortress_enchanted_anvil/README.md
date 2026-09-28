# Elves fortress enchanted anvil (`ElvenCitadel`, `ModuleTag_DrawEnchantedAnvil`)

The smithy on the back of the ring: a work platform over the ring's cap (anvil, weapon rack, the
smith on the fortress's `POSITIONBONE`) and the forge chimney standing in the courtyard. Own texture
`EBFortresL.tga` (DXT5). EA's anvil (`EBFANVIL2`, painted from `EBForge.tga`) and the smith are untouched.

## Design (2026-09-26, the citadel's standard)

Reworked to the approved citadel's recipe (`assets/elves/fortress/README.md`): EA's body kept
whole, a handful of additions in the citadel's silver and gold, one banner. The citadel's ring
crown stops at the anvil's face (180: no coping lantern there), so the anvil takes it up.

## What changed (body `EBFANVIL1`, healthy)

- **The citadel's coping on the platform's parapet.** Swept along the parapet from the chimney
  round the front and back (top z 59.0): a silver nose 0.5 proud and a silver top, its underside
  buried in the wall, the profile of the citadel's ring coping.
- **The citadel's ring lantern** on the parapet's front (-49.73, 0), over the middle of the ring's
  face 180: a slender silver post, a starlight crystal in a gilt cup and a gilt leaf tip (to z
  71.7), so the ring's crown reads lantern, gable, lantern the whole way round.
- **Chimney crown.** A moulded silver collar round the rim (open over the flue), six upright gilt
  leaf blades round it, and a starlight crystal rising from the flue (to z 114.65): the "enchanted"
  forge.
- **One banner.** A gilt pole on a silver foot on the platform's floor at (-47, -5.5), clear of the
  anvil, the rack and the smith: a leaf finial (z 96.5) and a leaf banner (5.6 x 15, house colour)
  facing the courtyard.
- **Removed from the first pass:** the second pole and both pennants (two banners and two
  pennants -> one banner); the pole's foot now stands on the floor (z 56), not 1.9 over it.

## Numbers

- Footprint: the coping's nose and the lantern's foot pass the parapet's front by 0.78
  (`footprint_margin = 0.8`; the anvil stands on the citadel's ring, whose own coping reaches x
  -53.1, and its collision is the fortress's). Height 106.19 -> 114.65 (+8.0 %, the flue's crystal).
- Triangles 999 -> 2,505 (budget 5,000).
- Checks: 90/90. House colour: one banner -> `EBHCFortress` (the citadel's four + this one).
- Lifecycle: `EBFAnvil_A`, `_D2` and `_D3` carry the redesign.

## The alpha check

EA's own material draws `EBFANVIL1` with alpha test off (NormalMapped.fx, `AlphaTestEnable` 0), so
no hole of EA's sheet shows on it in the game, EA's or ours. The checks report the cut-out agreement
as information only for such a target (sagekit/blender/alpha.py).

## Night lights

No night meshes in EA's model; none declared.

## Status

| Part | Healthy | Construction | Damaged | Really damaged / rubble |
|---|---|---|---|---|
| smithy (`EBFAnvil`) | built, checks pass, **awaiting review** | ours (`_A`) | texture swap | ours (`_D2`, `_D3`) |

Renders: `build/assets/elves/fortress_enchanted_anvil/renders/compare_{rts,close,ingame}.png`.

## Original animation caveat (2026-09-26)

The really damaged animation's enormous coordinates are present in EA's
`EBFAnvil_D2AN` translation keys, not introduced by this recipe. Its `BONE_3` leaves the
scene from frame 5 and `BONE_2` from frame 32. The source channel layout agrees with the
OpenSAGE reader; lifecycle checks report identical EA/ours extents. The original animation
bytes remain unchanged. Paired lifecycle previews show the remaining structure and debris;
a passing relative extent check does not establish sensible absolute animation bounds.
