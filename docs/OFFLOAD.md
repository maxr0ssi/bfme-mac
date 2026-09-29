# The A100 offload

A faction's full-quality builds on Google Colab (an A100), finished on the Mac. Design and iterate on
the Mac; when a faction's recipes are settled, offload the final builds. Plan:
[FACTIONS-PLAN.md](FACTIONS-PLAN.md) (Tools); code: `sagekit/offload.py`, `sagekit/snapshot.py`,
`tools/colab/offload.ipynb`.

## What runs where

| Where | Steps | Why |
|---|---|---|
| Mac, `offload pack` | extract (every building), the game snapshot | reads the game; Real-ESRGAN's 4x upscale is a Mac binary |
| Colab | geometry → render (a chained recipe from extract, after its base) | the Blender steps (bake, lifecycle, checks, renders; renders take most of the time) |
| Mac, `offload unpack` | ship, shared, ini, cache, checks | redone on the real game files: the INI edits and asset.dat copies that install uses come from EA's own files, and checks verify |

Colab never sees the game install. The bundle carries a **game snapshot**: the full member index of
EA's archives plus the bytes the faction's builds read (every INI, the faction's models, their
skeletons, animations and textures, the pristine `asset.dat` files; about 150 MB raw for the Men).
With `SAGEKIT_GAME_SNAPSHOT` set, `game.Install` reads the snapshot instead of the `.big` files, in the
host steps and the Blender jobs alike, so every step runs unchanged. A member outside the snapshot
fails with its name (`sagekit/snapshot.py` `collect()` then needs it).

Not in the offload: `sagekit sheets` and `sagekit house` (faction-wide, Mac; their outputs travel in
the bundle and the renders use them), `install`.

## Running an offload

1. On the Mac, with the faction's recipes settled and `sheets` and `house` run:

   ```sh
   python3 -m sagekit offload pack goblins            # or --only wall_hub,wall_gate
   ```

   It extracts every building, then writes `build/offload/goblins-<date>.zip` and prints its size.
2. Put the zip in Google Drive, folder `sagekit/` (drag it into drive.google.com, or the Drive app).
3. Open `tools/colab/offload.ipynb` in Colab (File > Upload notebook), Runtime > Change runtime type >
   **A100**. In the first code cell set `BUNDLE` to the zip's Drive path; `BUILDS` and `SLOTS` (4-6)
   say how many buildings and Blender processes run at once. Runtime > Run all; allow Drive access.
   The notebook installs Blender 4.5.9 (the Mac's version, checksum-checked), the OpenSAGE W3D add-on
   v0.7.2 (byte-identical to the Mac's), ImageMagick and a font, unpacks, prints the GPU Cycles uses
   (OptiX), builds, prints a timing table per building and step, and puts
   `goblins-<date>-results.zip` next to the bundle in Drive.
4. Download the results zip to the Mac, then:

   ```sh
   python3 -m sagekit offload unpack ~/Downloads/goblins-<date>-results.zip
   ```

   Each building that built replaces its `out/ work/ renders/ cache/` in `build/assets/` (its `src/` is
   merged), then `build <b> --from ship --to checks` runs for each on the real game. `--print-only`
   prints those commands instead. Buildings that failed on Colab are left alone; their logs are in
   `build/offload/<results zip name>/logs/`.
5. Review the renders and the poster as usual; install after review.

Bakes (`work/bake/*.npy`, about 0.5 GB per building) stay on Colab unless `KEEP_BAKES = True`; without
them a later local iteration starts `--from bake`, not `--from paint`.

## Privacy

The bundle and the results hold EA's files (the snapshot, each building's `src/`, `work/ref/`). They
sit in your private Google Drive during a run: never share the folder or the zips, and delete both
zips (Drive and its trash) when the faction is installed. Nothing uploads anything by itself; you
move the zips.

## Differences from a local build

- The code path is the same: the Mac's own Blender run from an unpacked bundle, on the snapshot,
  gives the same models, INIs, cache records, checks and bake inputs as a local build (the proof
  below). Cycles' sampled passes (AO, bevel, colour bakes, renders) are not bit-reproducible even
  between two runs on the Mac (GPU scheduling), and OptiX samples differently from Metal: the
  textures and renders match in look, not in bytes.
- Render labels use DejaVu Sans Bold on Linux (Arial Bold on the Mac); `SAGEKIT_FONT` overrides.
- `scene.use_gpu()` picks Metal on the Mac, else the first of OptiX, CUDA, HIP, oneAPI with a device;
  `SAGEKIT_CYCLES_DEVICE=CUDA` forces one (try it if OptiX misbehaves in a bake).
- Colab's ImageMagick is 6 (a `magick` shim calls `convert`/`identify`); only labels and alpha
  extraction use it there.

## Proof without Colab (2026-09-28, men/well)

Scratch copies of the repo, the Mac's Blender 4.5.9, one Blender slot each:

1. `offload pack men --only well` in a scratch copy: 145 MB zip in 10 s (snapshot 1,424 of 32,409
   members, 153 MB raw; the well's `src/` 47 MB; recoloured sheets 36 MB).
2. Unzipped into an empty folder with no game (`prefixes/` absent), `offload run --builds 1`
   (`SAGEKIT_BLENDER_SLOTS=1`): ok in 352 s (geometry 8, bake 41, paint 14, lifecycle 23, checks 3,
   render 259). `offload results`: 193 MB (bakes left out).
3. `offload unpack` into the scratch copy: ship → checks on the real game, 108/108 checks passed.
4. Against a normal `build men/well` from the same inputs (356 s): the same 173 files; byte-identical
   are every model (healthy, derived, lifecycle), the INIs, the asset.dat copy, `src/`, the export,
   every `work/*.json` and `checks.ok`. The four shipped textures differ at bake-noise level
   (about 17 of 4.2 M texels, mean error 4e-6), as a second local bake of the same geometry does
   against the first (7 texels, 1.6e-6); renders differ by a mean 3e-6 to 1.3e-5. Geometry bakes
   (position, normal, tags, coverage, UVs) are identical.

Not proven here: Linux Blender, OptiX, Colab's ImageMagick 6 and the A100's speed. The first Colab
run is the proof of those; start it with one small building (`ONLY = "well"`) and read its timing
table before the whole faction.
