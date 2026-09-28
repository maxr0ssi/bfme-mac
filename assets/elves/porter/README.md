# Selectable Elven builder

Review build for `EUPorter_SKN`: original Elf, face, hair, anatomy, held tools and shared
Gondor porter rig; ivory tunic, green wrap, curved birch cart, silver wheel rims and fittings,
gold leaf ribs, individual dressed stones, tied timber, joiner's chest and rolled plans.
The worker spawned during building construction (`EUWorker_SKN`) is outside this recipe.

```sh
python3 -B -m assets.elves.porter.unit --render
python3 -B -m assets.elves.porter.unit --check
python3 -B -m assets.elves.porter.install --check
# Only after visual review:
python3 -B -m assets.elves.porter.install
python3 -B -m assets.elves.porter.install --revert
```

Outputs: `build/assets/elves/porter/`. Before/after images are in `renders/`; the gallery is
`review.html`. The player approved installation on 2026-09-26; the pack is installed.
No game session has been launched.

The recipe reuses the Dwarven builder's rig-bound mesh primitives and motion decoder without
changing Dwarven files. Original body triangles, vertex positions, bone assignments and HLOD
are retained; the bucket and hammer mesh bytes are unchanged. The cart's wheel locations use
its source geometry rather than the offset wheel pivots. All cart/load bone sets match the
original. The unit's statistics, collision, INI behavior and shared animation files are untouched.

A private `EUCrafts.tga` diffuse atlas prevents changes to other workers/factions. Source cloth
is repeated and mapped affinely, preserving tiled UVs. Shorter legacy texture aliases are NUL
padded to preserve chunk sizes. `HC_EUCrafts.tga` repeats the original house mask identically
in the character region, with transparent-white neutral pixels for new props. The installer
appends its mapping to the active house-colour INI and preserves every existing block.

Checks cover source hashes, original body/rig/tools, valid mesh/UV/bone indices, exact RGBA
house-mask layout and unrelated cache-record preservation, including duplicates. Preview poses
cover idle, fidget, walk, run, water and both death animations using the OpenSAGE motion decoder;
finite transforms are checked across every decoded frame. Header-only animation inspection
incorrectly suggested the crushed-death cart was hidden; actual motion channels override those
legacy visibility keys and show it. Paired previews use the actual decoded visibility.

These opaque legacy materials ignore their source diffuse alpha in game. The preview disables
Blender's image-alpha interpretation; otherwise the original character appears falsely black.
The pictures show diffuse materials without simulating the game's player-colour blend. Exact
mask preservation and mapping are checked; runtime colour, wheel rotation and effects still
need the player's game review. Static costs are recorded in `docs/PERFORMANCE.md`.

Installation is separate from the Elven building pack. The builder archive is
`!!!!!!!!!!!!sagekit-elf-builder.big`. It stages against current caches, rejects active source
or private-name conflicts, and uses the shared transactional backup/rollback helper. Revert
refuses later cache/archive changes. It never resets the cache to `.orig`.

## Combined installation

The Dwarven builder's missing `ducrafts*` house-colour mappings were repaired during the
combined installation. Its higher-priority archive preserves this builder's mapping as well.
The Elven installer rejects a new mapping that an earlier archive would hide. Undo the Dwarven
repair before reverting this builder, then revert the Elven buildings if desired; scoped
receipts refuse to overwrite later shared-cache changes.
