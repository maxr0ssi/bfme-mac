# Modding the art: BFME2 1.06 and RotWK 2.02 under Wine

The manual route and background for one-off mods. Faction redesigns go through sagekit
([ART.md](ART.md)), which automates §g. Both titles run EA's **SAGE** engine with Westwood's
**W3D** asset format.

## a. Where the art lives

Archives sit next to the game in `prefixes/w10/drive_c/Program Files (x86)/Electronic Arts/{BFME2,RotWK}`.
They are uncompressed `BIGF`/`BIG4` containers — `tools/bigtool.py list|extract|replace|pack`
reads and rewrites them. Counts below are from this install.

| Archive | Holds |
|---|---|
| `W3D.big` | every model, skeleton and animation (12,743 `.w3d` in BFME2) under `art\w3d\<2 letters>\` |
| `Textures1-4.big` | compiled textures: ~3,750 `.dds` + ~570 `.tga` under `art\compiledtextures\<2 letters>\` |
| `Textures0.big` | `.jpg`/`.png` loading-screen and menu art |
| `Terrain.big` | 1,669 terrain `.tga` tiles |
| `ini.big` | 564 `.ini` + 101 `.inc`: `data\ini\object\…`, `gamedata.ini`, `gamelod.ini`, and `data\ini\mappedimages\…` (icon atlases: image name → sheet + pixel rect) |
| `Window.big` | 18 `.wnd` UI layouts, plus the APT/Flash screens |
| `Data1.big` | fonts (`.ttf`/`.otf`), `.cah` create-a-hero templates, XML scripts |
| `Shaders.big`, `Maps.big`, `Bases.big`, `Libraries.big`, `Audio.big`, `Music.big`, `AmbientStreams.big`, `lotrsec.big` | precompiled `.fxo`/`.pso`/`.vso`, maps, AI base layouts, AI scripts, 6,148 sounds, music, the licence blob |

Patches are overlay archives in the same folder: BFME2 `_patch101.big`, `_patch103.big`; RotWK
`_patch201.big`, `_patch201ini.big`, `_patch201maps.big`, `__patch202.big` (694 ini, 558 tga,
545 w3d, 1,489 maps), `_202music.big`. The **HD Edition** adds `___hdrotwk.v.0.9.big` and
`!!!!!!!!rotwk_hd_edition_2.02.big` (503 w3d, 366 dds, 99 tga — mostly same-named replacements).
The leading `!`/`_` characters are the community's way of forcing an archive to the end of the
name-sorted load order, so it wins over the stock files; loose files on disk beat archives.

Inside `.w3d`: chunked binary — mesh (`*_skn.w3d`), skeleton (`*_skl.w3d`), animation (`*_ANM.w3d`),
plus HLod/hierarchy, collision boxes, dazzles and aggregates.

## b. Blender: the OpenSAGE `io_mesh_w3d` add-on

<https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin> — "Imports & exports the W3D/W3X format to
and from Blender". This is the only live Blender route.

- **Blender versions**: the README states 2.93 through 5.2. On 4.2+ the release zip installs as a
  native Blender *extension* (drag and drop); on older builds as a legacy add-on.
  <https://raw.githubusercontent.com/OpenSAGE/OpenSAGE.BlenderPlugin/master/README.md>
- **Both directions**, and it handles "meshes, skeletons and skinned animations (with different
  compression types)" — the importer walks the W3D chunk tree and takes the skeleton from the
  HLOD and animation headers. Bones and animations round-trip. <https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin/wiki/Exporting-files>
- **Install**: download `io_mesh_w3d-X.X.zip` from Releases (not the source zip) → Blender
  Preferences → Add-ons → Install from File → enable "Import-Export: Westwood 3d (.w3d)".
  <https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin/wiki/Installing-the-Plugin>
- **Limits**: the README calls it beta ("behaviour may change between releases"). Every referenced
  file (skeleton, textures) must sit in the *same folder* as the file you import, and a frequent
  export bug is misalignment — Ctrl+A → All Transforms first.
  <https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin/wiki/Troubleshooting>
  BFME-era niceties (auto texture lookup from `.big`, armature generation, effect bones, DDS↔TGA
  on export) live in an **open, unmerged** PR:
  <https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin/pull/280>

## c. Registering new assets: `asset.dat`

BFME2 and RotWK index their art in a compiled cache, `asset.dat`, at the game root. The engine
looks up models and textures through it, so an asset the cache does not know about shows up
missing or pink even when the bytes are in the archive.
<https://forums.revora.net/topic/100132-assetdat-can-someone-please-explain-this-sorcery/>

On this install: magic `ALAE`, version `0x102`, then one record per asset (name length, name,
timestamp, chunk list). BFME2's is 4.0 MB / 17,677 entries; RotWK's is 6.4 MB / 28,261 entries
and is the **single cache shared by 2.02 and the HD Edition** — the HD `.big` carries its own
1.25 MB copy as a member, but the loose file at the game root is what the engine opens, and the
HD art mostly reuses existing names, so it needs no new entries.

`tools/asset_dat.py patch|texture` updates records in place (§g); that is the route used here.
Windows tools that rebuild the whole cache (run under Wine in the game's prefix): EA's
[AssetCacheBuilder](https://forums.revora.net/topic/72843-eas-assetcachebuilder-from-the-sdk/)
from the mod SDK, [bfme2-patcher](https://github.com/DarkAtra/bfme2-patcher) (open source), and
[Sy's Asset Builder](https://forums.revora.net/topic/82657-sys-asset-builder/) (reported broken on
modern Windows).

## d. Limits an artist should know

- **Poly/vertex budgets** (BFME2 SDK art guidelines, per LOD tier — Normal/Medium/Low):
  heroes 1200/575/325 verts, horde infantry 375/225/150, cavalry 643/386/225, medium monsters
  600/450/300 (one 256px texture), large monsters 2250/1125/700 (up to 3 textures).
  <https://forums.revora.net/topic/62814-modeling/>
- **How hard that ceiling is**: *reported* — a modder measured 60,000-poly units, 1.8 M polys
  on screen, for ~2.3 fps; unit count, pathfinding and AI bind long before mesh density.
  Practical community numbers are 1.5–3 k polys for horde units, 3–6 k for heroes.
  <https://forums.revora.net/topic/104083-sage-engine-limitations/>
- **Textures**: DDS (DXT1 opaque/cutout, DXT3 hard alpha, DXT5 smooth alpha) and TGA. Authored at
  512², shipped at 128–256 for line units and 512 for heroes. Power-of-two sizes are typical of
  DXT-era engines but **unverified** for BFME2 specifically — assume them.
  <https://w3dhub.com/forum/topic/417101-dds-files-and-dxt-compression/>
- **Frame rate: 30 FPS**, `FramesPerSecondLimit` in `gamedata.ini`, and it is the simulation rate —
  animation speed, movement and build times all scale with it. Author animations at 30 fps and do
  not change the limit. <https://www.the3rdage.net/item-858?addview=>
- **Max bones per skeleton**: no documented figure found in the SDK guidelines or the community
  threads. Treat it as unknown; if a hero rig misbehaves, suspect it.

## e. Multiplayer

Peers must run identical *game data*; a "mismatch" error means the game data differs
([MULTIPLAYER.md](../MULTIPLAYER.md)).
In practice: pure art changes — swapping a `.w3d` mesh or a `.dds` texture for one with the same
name, same bone names, same asset entry — are cosmetic and desync-safe, which is exactly why the
HD Edition can differ between players. Anything that touches an `.ini` (`gamedata.ini` camera
limits, `gamelodpresets.ini`, any object/weapon/armour value) changes the simulation and **must**
be byte-identical on both machines, as our edited `ini.big` / `__patch202.big` already are. If in
doubt, send the other players the same files `scripts/install-mod.sh` put in.

## f. The big mods

The large SAGE mods are Windows installers aimed at a retail install. **Edain** (RotWK) needs the
*official* 2.01 patch and BFME2 1.06 — explicitly **not** the unofficial RotWK 2.02 this repo runs, which
must be uninstalled first (<https://www.moddb.com/mods/edain-mod>). **Age of the Ring** went
standalone at 9.0 and ships its own installer plus a launcher
(<https://www.moddb.com/mods/the-horse-lords-a-total-modification-for-bfme>). Both, and online
play, are normally driven by the **T3A:Online / All-in-One launcher** (<https://t3aonline.net/en/>),
which hooks the game `.exe`. **Caution:** those launchers are C# desktop apps
(<https://github.com/Ravo92/aio-lotr-launcher>), and this setup disables Wine Mono
(`WINEDLLOVERRIDES=mscoree,mshtml=` in `env.sh`) — a .NET launcher will not start until Mono is
installed and that override removed. Installing a mod's `.big` files directly with
`scripts/install-mod.sh` sidesteps the launcher entirely. Finally, **BFME: Reforged** is *not* a
mod: it is a fan remake in Unreal Engine 4 (<https://github.com/BFME-Reforged>), so none of this
pipeline applies to it.

## g. Re-exporting a model from Blender — verified pipeline (2026-09-23, Dwarven fortress)

Blender 4.5.9 LTS + OpenSAGE `io_mesh_w3d` 0.7.2 (installs as a legacy add-on; operators
`import_mesh.westwood_w3d` / `export_mesh.westwood_w3d`). For a model with its own skeleton, export
mode `HM`, and name the output file after the model in capitals (`DBFORTRESS.w3d`): the add-on takes
the hierarchy and container names from the file name.

1. **Import, edit, export** (headless works: `Blender -b --python script.py`). The fortress round
   trip keeps every mesh, vertex and triangle count, all 37 bones and the HLOD table.
2. **`tools/w3d_fixup.py original.w3d exported.w3d`** repairs what the add-on changes: it drops
   `BumpScale` and renames legacy texture references to the loaded file (`.tga` -> `.dds`), writes mesh
   version 4.2 instead of BFME2's 5.0, re-tags surface types, drops pivot fixups, and **drops the
   AABTREE collision trees**, which BFME2 needs (the untouched fortress minus only its AABTREEs does
   not render; Generals' loader would rebuild them, BFME2's does not). The fixer regenerates them
   the way WW3D2's `AABTreeBuilderClass` lays them out.
3. **`tools/asset_dat.py patch <game>/asset.dat file.w3d`**. `asset.dat` caches, per model, the byte offset and size of every top-level chunk
   (`H*<hierarchy>`, each `container.mesh`, the HLOD), and the engine reads those ranges blind. Any
   edited model therefore changes layout and is read at stale offsets: it loads, is selectable by
   its footprint, and draws nothing. Patch the record in the asset.dat of the game that *owns* the
   model (the fortress is BFME2 content: `BFME2/asset.dat`, even when playing RotWK). Model and
   record must change together; `asset_dat.py check` verifies they match, `asset.dat.orig` is the
   untouched copy.
4. Pack it as an override archive that sorts first (e.g. `!!!!!!!!!!!name.big` next to RotWK's
   archives) and install with `scripts/install-mod.sh`. A RotWK-folder archive overrides BFME2's.

Debugging without launching the game: `asset_dat.py check` plus the structural checks above catch
every failure met so far; the game only needs to confirm the result. Everything that failed here
failed silently (no crash, no log): the model is simply invisible.
