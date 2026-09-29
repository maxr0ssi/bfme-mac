# Goblin burrows (`WildBurrowsExpansion`)

Model `WBFBurrow`, mesh `WBFBURROW`, own texture `WBFortresB.tga` (from `WBFortress.tga`).
`Tier.STANDARD`. A fortress expansion on its pad. EA's body is kept whole: the hunched hide roof,
the drapes and wings, the dark mouth under its hood, the stepped stone pad, the two skull poles.

## What changed

The burrow becomes the carcass of a great beast the Goblins dug into.

- **Ribcage** ([`../arrow_den/pad.py`](../arrow_den/pad.py), the expansions' pad): four pairs of
  bleached ribs arch over the roof from rocks either side, a knobbed vertebra and a bone spike
  where each pair meets; a skirt of black rock along the sides and back.
- **Spine and skull**: vertebrae along the ridge join the ribs and run down as the neck to the
  beast's horned skull (size 7) over the mouth's hood.
- **Jaws**: two pairs of iron-collared tusks rise either side of the steps and curl inward.
- **Trophies**: skull piles by the steps and behind; a carcass hung from the hood beside the
  mouth.
- **Gore**: the `Gore` paint layer under the skull, the carcass and the piles.
- **Banners**: none (cap 0).

## Kept clear

- The mouth and its steps: nothing new at x > -18, |y| < 9 below z 29, where units come out.
- EA's skull poles at (-16, +-17.9).

## Status

Installed. 588 -> 4,543 triangles, height 43.6 ->
51.6 (+18.4 %), footprint unchanged, 9/9 preview checks.

## Open

- Full build: bake, paint, lifecycle (`WBFBurrow_A`, `_D2`, `_D3`).
