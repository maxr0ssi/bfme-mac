# Selectable Dwarven builder

Redesign of HD Edition's `DUPorter_SKN`: timber cart, open-spoke wheels,
stone and tool load, leather apron, hammer and beard clasps. The original helmet is
retained at Max's request. The body anatomy, skeleton, bucket and animation files remain
original. Construction workers (`DUWorker_SKN`) and Elven art are outside this recipe.

From the repository root:

```sh
python3 -B -m assets.dwarves.porter.unit --render
python3 -B -m assets.dwarves.porter.unit --check
python3 -B -m assets.dwarves.porter.install --selfcheck
python3 -B -m assets.dwarves.porter.install --check
python3 -B -m assets.dwarves.porter.install
python3 -B -m assets.dwarves.porter.install --revert
```

Requires the existing local game assets, ImageMagick, Blender and its installed OpenSAGE
add-on. Outputs stay under ignored `build/assets/dwarves/porter/`: source copies, a rebuilt
W3D, private diffuse textures, structural checks and paired previews. The separate installer
adds only this builder to RotWK after review. It preserves the current asset cache, patches
all duplicate builder records and registers private textures without changing other records.
The archive is `!!!!!!!!!!!!sagekit-dwarf-builder.big`; existing faction packs are untouched.
Scoped backups and installation receipt live in `build/assets/dwarves/porter/_install/`.
The earlier `install/` receipt and backup remain available for a guarded legacy revert.
The colour repair upgrades the existing reviewed archive without rebuilding its model or
DDS textures. Its scoped revert restores the pre-upgrade builder archive and current-cache
snapshot; it refuses later cache/archive changes rather than removing other installations.

All private atlas names map to `HC_DUCrafts.tga`: the original DUPorter mask tiles across
the left half, while exact transparent-white pixels keep the material swatches neutral.
The installer composes the currently effective house-colour INI and preserves every existing
mapping. Install this repair after the Elven builder because the Dwarven archive wins the
shared INI's load order. Later installers must preserve that composition or reject shadowing.
`--check` generates only the missing mask and stages the upgrade, proving the existing model
and diffuse bytes are unchanged and checking every decoded mask row.
There is no building registry entry; do not use the whole-faction installer for this unit.

`unit.py` checks the supported source hashes before rebuilding and verifies mesh indices,
finite coordinates, UVs, bone bindings, original body positions and unchanged helmet,
bucket and hierarchy chunks. `preview.py` uses identical lighting and cameras for both
models, with original idle, running, hammering, water and death animation poses. It reuses
the installed OpenSAGE decoder for motion channels the existing building animation reader
does not support, and checks finite transforms across the rendered animations. The shared
reader is unchanged. Earlier static previews made without these channels were not valid
animation checks; the current previews decode actual motion.

The previews use game diffuse materials with approximate lighting. They do not certify
runtime wheel rotation, effects, player colours, clipping throughout every animation or
performance. Those need one player-run game review. Max approved the restored-helmet design
and requested the Dwarven-only installation. No game has been launched. Static asset costs
are recorded in `docs/PERFORMANCE.md`; no frame-rate result is claimed.
