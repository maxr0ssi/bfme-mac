# Goblin giant sentry (`WildGiantSentryExpansion`)

Model `WBFGSentry`, mesh `WBFGSENTRY`, own texture `WBFortresE.tga` (from `WBFortress.tga`).
`Tier.STANDARD`. A fortress expansion on its pad. EA's body is kept whole: the plated column
flaring at its foot, the crater the mountain giant stands in, the ring of great spikes round the
rim, the brace at the back.

## What changed

- **Crown**: six great crimson horns with bleached tips curling up and out of the rim's outer lip
  between EA's spikes, each in an iron collar; a totem on the back rim (a horned troll skull over
  a bone crossbar hung with two skulls, a ribcage lashed below) facing across the crater.
- **Pad** ([`../arrow_den/pad.py`](../arrow_den/pad.py)): four great ribs rise out of rocks and
  curl in to grip the column at z 25; a skirt of black rock round its foot and the brace's.
- **Rim**: skulls driven onto four of the great spikes, blood below them; five skulls hung on
  chains under the rim.
- **Foot**: three heaps of round boulders with thongs round the top one, the giant's ammunition;
  a great gnawed thigh bone leaning on the column's front.
- **Brace**: a skull on a spike on the post.
- **Banners**: one ragged house-colour banner with a white claw on the column's camera-side face
  under the rim (cap 1), in our own house model (`HOUSE_DRAW`).

## Kept clear

- The crater and the giant's stand (`P1`, z 29.5, x -17..13, y -14..15.5): nothing new over it;
  the horns root on the rim's outer lip (r 19.5 from the column's axis) and curl outward.

## Status

Designed, shape preview only (not built, not installed). 368 -> 6,079 triangles, height 53.5 ->
61.3 (+14.5 %), footprint unchanged, 9/9 preview checks.

## Open

- Full build: bake, paint, lifecycle (`WBFGSentry_A`, `_D2`, `_D3`), `sagekit house goblins`.
