# Angmar mill (`AngmarMill`)

Model `KBMill`, mesh `BASE` (a skin: docs/ART.md, "A skinned body"), own texture `KBMilH.tga` (from
`KBMill.tga`). Palette A2. EA's ring wall, capstan, thralls and shed are kept whole.

## Pass 1: the thrall mill

- **The ring wall** becomes a stretch of Carn Dum's frozen wall, in the walls group's pieces
  ([`../shapes_walls.py`](../shapes_walls.py)): merlons on the inner edge over the yard (V1 wraps the
  wall in a thicker one from level 2, so the inner edge is the one that reads at every level), a
  corbel with a rime crust and icicles under the outer edge, ice drifts up both feet. The raised
  blocks under V1's horns and the stretches V2's buttresses lean on stay plain.
- **The capstan** wears a crown of five small forged tines with frozen tips on the post's head, and a
  ring of iron barbs on the great ring beam. Both ride EA's `BONE_POST01`, so they turn with the
  capstan as the thralls push (`renders/anim/`).
- **Two cold braziers** on the back walk (`coldflame`).

4,318 triangles (EA 580). Footprint unchanged, height +15 % (the crown on the post).
`KBMill_A` is rebuilt with `fill` (cut along EA's pieces, the merlons kept slivers); `KBMill_D1` takes
our body whole; `KBMill_D2` and `KBMill_D3` are rebuilt along EA's pieces. `PICK_BOX`, a closed box
round the shed's walls, is left out of the bakes.

## Status

- [x] skinned body: EA's bones, animation and skin weights byte for byte (checks)
- [x] healthy body designed (pass 1), built in colour, lifecycle, staged
- [ ] reviewed by Max
- [ ] checked in game
