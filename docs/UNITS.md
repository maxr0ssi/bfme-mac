# Units: how a builder recipe works

A unit is a skinned model the game animates. Its redesign keeps EA's body, skeleton and
animations and adds rigid pieces bound to EA's bones, so every animation still plays. The building
pipeline does not apply; `sagekit/units/` does. The Dwarven builder
([assets/dwarves/porter/design.py](../assets/dwarves/porter/design.py)) is the template.

```sh
python3 -m sagekit unit list                          # recipes, their models, what is installed
python3 -m sagekit unit men/porter --render [STATES]  # build + checks + renders/compare_<state>.png
python3 -m sagekit unit men/porter --check | --stage | --install | --revert [--dry-run]
```

## The recipe

`assets/<faction>/porter/design.py` holds one `Unit` subclass (`sagekit/units/__init__.py`):

| Attribute | Says |
|---|---|
| `model`, `skeleton`, `expected` | EA's model and skeleton, and their SHA-256 (any other source is refused) |
| `anims` | the animations extracted for the renders (`<skeleton family>_<anim>.w3d`) |
| `own_model`, `objects` | for a model other factions draw too: the name ours ships under, and `{object: (INI, Draw tag)}` whose `Model =` is repointed |
| `textures` | `{EA sheet: private name}` swapped in every rebuilt mesh (not longer than EA's name) |
| `mask`, `house` | `(EA's mask, ours)` and `{private sheet: our mask}`, the `housecolor.ini` lines |
| `archive` | the unit's own archive, `!!!!!!!!!!!!sagekit-<unit>-builder.big` |
| `views`, `labels`, `smooth`, `opaque` | the render poses (`View(anim, frame, ...)`), titles, shading |

`design(w, sk)` returns `{MESH NAME: Mesh}`; meshes it leaves out stay EA's byte for byte.
`self.mesh(w, sk, name, keep=True)` starts from EA's mesh (its vertices, bones and triangles
exactly; only the UVs move into the atlas), `keep=False` replaces it. `Mesh.face / box / tube`
add pieces in the model's rest space, each on a bone (`bone="CART"`, default the recipe's `bone`).
A rigid EA mesh (one HLOD bone, like the orc cart) takes pieces on that bone only; `skin=True`
makes it a skin. `paint(b)` writes the atlas and returns its path: 2048 x 1024, EA's character
sheet tiled 4 x 4 on the left (`keep_uv`), 16 swatch tiles on the right (`uv_for(tag)`), painted
from the faction's palette ramps (`sagekit/units/paint.py`). `check(b, original, new, sk)` adds
recipe checks. A stub (`design` returns `{}`) renders EA's unit against itself and never installs.

## What the framework does

- **Build** (`build.py`): EA's model, skeleton, animations, sheets and mask into `src/` with their
  hashes (`sources.json`), our model and atlas DDS (one per private name) and the house mask (EA's
  tiled exactly under the body, transparent white under the swatches) into `work/`.
- **Checks:** hierarchy and every non-mesh chunk EA's; kept bodies on EA's vertices and bones;
  finite geometry, valid indices, UVs in the atlas, only private sheets on rebuilt meshes; bone
  indices in the skeleton; animation hierarchies; the mask; then the recipe's own.
- **Renders** (`render.py`, `sagekit/blender/unit_pose.py`): one Blender process poses EA's model
  and ours from the animation bytes (OpenSAGE's decoder, every frame checked finite and moving) and
  renders both with one camera; `compare_<state>.png` side by side.
- **Install** (`install.py`): the archive holds the model, atlas, mask, the repointed INIs and
  `housecolor.ini` (EA's plus the unit's lines). The shared `!!!!!!!!!!!!!sagekit-units.big` sorts
  first and carries EA's `housecolor.ini` plus every installed unit's lines, rebuilt on each unit
  install and revert, so any number of builders install in any order (before it, each archive's
  INI shadowed the others'). asset.dat: our model's record patched (or filed as a copy of EA's),
  the private sheets and mask registered, the meshes' dependencies switched, every other record
  untouched. `--revert` checks the records are still the ones it wrote and puts exactly those back
  as `asset.dat.orig` has them (`records.py`), so units revert in any order, around faction packs.
- **Release:** `install.release()` gives `sagekit/pack.py` the staged archive, its cache ops and
  its `housecolor.ini` lines.

## Not covered yet

Construction workers (`DUWorker_SKN`, `GUWorker_SKN`, `MUOrcLabor_SKN`), troops and heroes; the
lower-detail `_SKNM` / `_SKNL` models (only `_SKN` is redesigned); player colour and wheel spin
are checked in game only.
