# Goblin arrow den (`WildArrowDenExpansion`)

Model `WBFADen`, mesh `WBFARRDEN`, own texture `WBFortresX.tga` (from `WBFortress.tga`).
`Tier.STANDARD`. A fortress expansion on its pad. EA's body is kept whole: the plated octagonal
stalk, the flared bowl, the ring of glowing eyes the arrows fly from, the spiked roof, the brace
down to the ground at the back.

## What changed

- **Pad** ([`pad.py`](pad.py), shared by the four expansions): a skirt of black rock round the
  stalk's foot and the brace's; four great bleached ribs rise out of rocks on the diagonals and
  curl in to grip the stalk at z 30, each with an iron collar and a rope lashing.
- **Stalk**: two riveted iron hoops and one under the bowl; a skull on a bloodied iron spike out
  of its front.
- **Bowl**: sixteen bone fangs round its underside, below the eyes; four skulls hung on chains.
- **Roof**: four great crimson horns with bleached tips and four iron spikes round the deck; an
  iron spike out of its middle to z 106 with a big skull driven onto it (the citadel spires'
  mark).
- **Brace**: a skull on a spike on the post, three bone spikes along the beam, a gibbet cage
  with a skeleton hung under it.
- **Banners**: one ragged house-colour banner with a white eye on the post's camera-side face
  (cap 1), in our own house model (`HOUSE_DRAW`: EA gives the expansions none).

## Kept clear

- The eye ring (`EYES`, r 12.9, z 72.5..82.5) and the eight arrow bones at r 11.8, z 76.8:
  nothing new between r 11 and 25 from z 71 to 87.

## Status

Designed, shape preview only (not built, not installed). 499 -> 4,804 triangles, height 89.3 ->
106.0 (+18.7 %), footprint unchanged, 9/9 preview checks.

## Open

- Full build: bake, paint, lifecycle (`WBFADen_A`, `_D2`, `_D3`), `sagekit house goblins` for
  the banner's house model. No night lights (EA's model has no night meshes).
