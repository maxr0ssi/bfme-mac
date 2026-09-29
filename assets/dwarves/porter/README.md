# Dwarven builder (`DUPorter_SKN`)

Redesign of the selectable builder: a timber cart with open-spoke wheels, a stone and tool load,
a leather apron, a hammer and beard clasps. The original helmet is kept. The body, skeleton,
bucket and animation files are EA's. Construction workers (`DUWorker_SKN`) are not part of it.

## Commands

From the repository root:

```sh
python3 -B -m assets.dwarves.porter.unit --render
python3 -B -m assets.dwarves.porter.unit --check
python3 -B -m assets.dwarves.porter.install --selfcheck
python3 -B -m assets.dwarves.porter.install --check
python3 -B -m assets.dwarves.porter.install
python3 -B -m assets.dwarves.porter.install --revert
```

Needs the local game assets, ImageMagick, Blender and its OpenSAGE add-on. Outputs stay in
`build/assets/dwarves/porter/`. `unit.py` checks the source hashes, then verifies mesh indices,
UVs, bone bindings and that the helmet, bucket and hierarchy chunks are unchanged. `preview.py`
renders both models with the same lighting and cameras in EA's idle, running, hammering, water
and death poses.

## Player colour

Every private atlas name maps to `HC_DUCrafts.tga`: EA's DUPorter mask tiles across the left half,
and exact transparent-white pixels keep the material swatches neutral. The installer composes the
current house-colour INI and keeps every existing mapping. Install it after the Elven builder:
the Dwarven archive wins the shared INI's load order, so later installers must keep that
composition.

## Status

Installed (separate archive `!!!!!!!!!!!!sagekit-dwarf-builder.big`). The installer patches every
duplicate builder record, registers the private textures and leaves the faction packs untouched.
Backups and the receipt are in `build/assets/dwarves/porter/_install/`. There is no building
registry entry: do not use the whole-faction installer for this unit.

## Known limits

- Not checked in game: wheel rotation, effects, player colour.
- `--revert` also accepts the older `install/` receipt, and refuses if the cache changed since.
