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
`self.mesh(w, sk, name, keep=True)` starts from EA's mesh (its vertices, bones, skin weights and
triangles exactly; only the UVs move into the atlas), `keep=False` replaces it. `Mesh.face / box / tube`
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
- **Checks:** hierarchy and every non-mesh chunk EA's; kept bodies on EA's vertices and bones, their
  skin weights EA's byte for byte (two-bone vertices: both bones, weights, second-bone data);
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

## Construction workers

The little figures a building's `GettingBuiltBehavior` spawns (`WorkerName`) while it goes up. One
recipe per faction, `assets/<faction>/worker/design.py`, each matching that faction's builder:

| Recipe | EA's model | Ships as | Drawn by |
|---|---|---|---|
| `dwarves/worker` | `DUWorker_SKN` (the builder's dwarf) | in place | DwarvenWorker |
| `elves/worker` | `EUWorker_SKN` (the builder's Elf) | in place | ElvenWorker |
| `men/worker` | `GUWorker_SKN` | in place | GondorWorker, ArnorWorker, the neutral and civilian sites |
| `mordor/worker` | `MUOrcLabor_SKN` | `MUWorker_SKN` | MordorWorker, MordorWorkerNoSelect (repointed) |
| `goblins/worker` | `MUOrcLabor_SKN` | `WUWorker_SKN` | WildLaborer (repointed); GoblinLaborerNoSelect, GoblinFarmLaborerNoSelect (new) |
| `angmar/worker` | `MUOrcLabor_SKN` | `KUWorker_SKN` | AngmarWorker (repointed); AngmarLaborerNoSelect, AngmarFarmLaborerNoSelect (new) |
| `isengard/worker` | `MUOrcLabor_SKN` | `IUWorker_SKN` | IsengardWorkerNoSelect, IsengardFortressWorkerNoSelect (new; the Isengard pack names them) |

```sh
python3 -m sagekit unit <faction>/worker --render | --check | --stage
python3 -m sagekit unit <faction>/worker --install      # after review; one faction at a time is fine
python3 -m sagekit unit <faction>/worker --revert
```

EA's body, skeleton, skin weights and animations are kept (the checks prove it); each worker has a
private atlas and house mask, its own archive `!!!!!!!!!!!!sagekit-<faction>-worker.big`, and
player-colour cloth: a piece tagged `HC` (`sagekit/units/cloth.py`) samples a patch of EA's sheet
that EA's house mask covers fully, so the game tints it as it tints EA's tunic or apron. `drape`
gives each row of cloth its own bone and stretches the band between, so capes bend with the body.
The four orc workers share `sagekit/units/labourer.py` (EA's labourer: its anatomy, sheet regions,
tool grips and paint); each draws its own gear, HAMMER (shown while building) and AXE (idle, chop).
Sub-object names stay EA's, because the INI shows and hides them by name.

Recipe attributes the workers added (all opt-in, the builders unchanged): `anim_family` (the orc's
animations are `MUOrcLabor_*` on `MUGblnSlv_SKL`), `mask_source` and `mask_scale` (Gondor's mask
is a 64-pixel PNG; the sheet is painted at 256), and `ini_files(base)` (INI members of the unit's
own, composed on the game's text without unit archives).

**INI data.** Dwarves, Elves and Men: none (models replaced in place). Mordor, Goblins, Angmar: one
`Model =` line per repointed Draw in their worker INI, which no faction pack ships. Buildings that
called Mordor's workers get their own faction's: Isengard's (it has no worker object), the Goblin
cave, spider pit and mine shaft, and Angmar's Hall of Twilight and mill. The worker unit adds them in
`data\ini\object\evilfaction\units\mordor\worker_<faction>.ini` (`labourer.py children`):
ChildObjects of Mordor's workers (so they behave exactly as EA's) with MordorWorkerNoSelect's Draw
drawing our model; the file sorts after `worker.ini`, as the engine reads INIs in sorted order and
a child needs its parent first. The faction's own pack names them: `Style.workers` makes
`sagekit/install.py` swap `WorkerName` in the INIs it composes (op `worker`, `formats/ini.py
set_worker`), so no INI is in two archives. The pack therefore needs the unit: install
`<faction>/worker` first, then `sagekit install <faction>`; revert the pack before the unit. Both
refuse the wrong order (`Unit.defines`, `units/install.py workers_guard`). No upgrades. The
civilian lumber mill, furnace and slaughter house (parents of the evil factions' copies) and the
shared Evil sentry tower still call Mordor's workers.

Review sheets: `build/assets/_review_finish/workers/<faction>.jpg` (EA's worker, ours and our
builder: close, behind, building, and at the RTS camera; red simulates the player colour).

## Not covered yet

Troops and heroes; the lower-detail `_SKNM` / `_SKNL` models (only `_SKN` is redesigned); player
colour and wheel spin are checked in game only.
