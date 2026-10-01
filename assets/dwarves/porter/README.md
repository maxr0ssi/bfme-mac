# Dwarven builder (`DUPorter_SKN`)

Redesign of the selectable builder: a timber cart with open-spoke wheels, a stone and tool load,
a leather apron, a hammer and beard clasps. The original helmet is kept. The body, skeleton,
bucket and animation files are EA's. Construction workers (`DUWorker_SKN`) are not part of it.

## Commands

From the repository root (a unit recipe: [docs/UNITS.md](../../../docs/UNITS.md)):

```sh
python3 -m sagekit unit dwarves/porter --render     # build, check, posed before/after renders
python3 -m sagekit unit dwarves/porter --check
python3 -m sagekit unit dwarves/porter --stage      # the archive into _install/, nothing installed
python3 -m sagekit unit dwarves/porter --install
python3 -m sagekit unit dwarves/porter --revert
```

Needs the local game assets, ImageMagick, Blender and its OpenSAGE add-on. Outputs stay in
`build/assets/dwarves/porter/`. `design.py` is the recipe: the pieces, their bones and the atlas
paint. The build checks the source hashes, mesh indices, UVs, bone bindings, the kept body and that
the helmet, bucket and hierarchy chunks are unchanged; the renders pose both models with the same
lighting and cameras in EA's idle, running, hammering, water and death poses. `unit.py` and
`preview.py` are only the troop scripts' imports of the shared mesh primitives and motion decoder.

## Player colour

Every private atlas name maps to `HC_DUCrafts.tga`: EA's DUPorter mask tiles across the left half,
and exact transparent-white pixels keep the material swatches neutral. The archive's own
`housecolor.ini` is EA's plus these lines; the shared `!!!!!!!!!!!!!sagekit-units.big` carries
every installed unit's lines, so install order no longer matters.

## Status

Installed (separate archive `!!!!!!!!!!!!sagekit-dwarf-builder.big`) by the old standalone
installer, before the shared house-colour INI: its `housecolor.ini` also holds the Elven builder's
lines. The framework rebuilds the model, atlases and mask byte for byte; a fresh `--stage` differs
from the installed archive only in that INI member (EA's plus the Dwarven lines). `--revert` takes
the installed one out (its `_install/receipt.json` proves it ours) and puts its asset.dat records
back as EA's, in any order with the other installs.

## Known limits

- Not checked in game: wheel rotation, effects, player colour.
