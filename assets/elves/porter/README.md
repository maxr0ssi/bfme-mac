# Elven builder (`EUPorter_SKN`)

The selectable builder: EA's Elf (face, hair, anatomy, held tools) on the shared Gondor porter rig,
in an ivory tunic and green wrap, with a curved birch cart: silver wheel rims and fittings, gold
leaf ribs, dressed stones, tied timber, a joiner's chest and rolled plans. The worker spawned while
a building goes up (`EUWorker_SKN`) is not part of this recipe.

```sh
python3 -B -m assets.elves.porter.unit --render
python3 -B -m assets.elves.porter.unit --check
python3 -B -m assets.elves.porter.install --check
python3 -B -m assets.elves.porter.install
python3 -B -m assets.elves.porter.install --revert
```

Outputs are in `build/assets/elves/porter/`: before/after images in `renders/`, gallery `review.html`.

## What changed

- **Body**: EA's triangles, vertex positions, bone assignments and HLOD are kept; the bucket and
  hammer bytes are unchanged. Statistics, collision, INI behaviour and shared animations are untouched.
- **Cart**: the wheels sit where the cart's geometry puts them, not on the offset wheel pivots;
  every cart and load bone set matches EA's.
- **Texture**: a private `EUCrafts.tga` atlas, so other workers and factions keep theirs; EA's
  tiled cloth UVs still tile.
- **House colour**: `HC_EUCrafts.tga` repeats EA's mask exactly in the character region, neutral
  for the new props. The installer appends its mapping to the house-colour INI and keeps every
  other block.
- The mesh primitives and motion decoder are the [Dwarven builder](../../dwarves/porter/README.md)'s,
  reused without changing Dwarven files.

## Status

Installed, in its own archive `!!!!!!!!!!!!sagekit-elf-builder.big`, separate from the Elven
building pack. 1,722 -> 7,544 triangles. The checks cover source hashes, EA's body, rig and tools,
mesh/UV/bone indices, the exact house mask and unrelated cache records. The previews pose idle,
fidget, walk, run, water and both deaths, with every decoded frame checked finite.

## Known limits

- Not checked in game: wheel rotation, effects, player colour.
- Revert order: undo the Dwarven builder's house-colour repair first (its archive has the higher
  priority), then this builder, then the Elven buildings. A revert refuses if a later install
  changed the shared cache.
