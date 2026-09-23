# Modding the art: BFME2 1.06 and RotWK 2.02 under Wine

For a 3D artist who wants to change what the game looks like. Both titles run EA's **SAGE** engine
with Westwood's **W3D** asset format. Everything here happens on the Mac side except the Windows
`.exe` tools in §c, which run in the same Wine prefix as the game.

## a. Where the art lives

Archives sit next to the game in `prefixes/stable/drive_c/Program Files (x86)/Electronic Arts/{BFME2,RotWK}`.
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
  HLOD and animation headers. So bones and animations round-trip, which is what matters for a
  hero model. <https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin/wiki/Exporting-files>
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
- **Maintenance**: last tagged release v0.7.2, 2025-05-01 (marked prerelease); `master` has commits
  as recent as 2026. <https://github.com/OpenSAGE/OpenSAGE.BlenderPlugin/releases>
- **Alternative**: the historic pipeline was RenX / the official 3ds Max W3D exporter (Max 7 and 8
  only), which your friend does not need if Blender works.
  <https://www.moddb.com/addons/renx-3ds-max-8-edition>

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

**Rebuild tools** — all Windows `.exe`, so run them with `WINE_BUILD=w10 . ./env.sh; wine <tool>`
in the same prefix as the game:

- **EA `AssetCacheBuilder`**, from the official BFME2 mod SDK. Point it at an art folder holding
  the originals plus your replacements; it emits a merged `asset.dat`.
  <https://forums.revora.net/topic/72843-eas-assetcachebuilder-from-the-sdk/> ·
  <https://www.the3rdage.net/item-807?apage=827>
- **Sy's Asset Builder** (community): <https://forums.revora.net/topic/82657-sys-asset-builder/>.
  Reported broken on modern Windows (missing `COMDLG32.OCX`); expect the same under Wine.
- **`bfme2-patcher`** (modern, open source) builds a `mod_asset.dat` and merges it with the
  original: <https://github.com/DarkAtra/bfme2-patcher>
- **FinalBIG** edits `.big` archives, not `asset.dat` — `tools/bigtool.py` already does that job
  natively here. <https://www.the3rdage.net/item-52>

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

Peers must run identical *game data*, and a "mismatch" error is data, not network (MULTIPLAYER.md).
In practice: pure art changes — swapping a `.w3d` mesh or a `.dds` texture for one with the same
name, same bone names, same asset entry — are cosmetic and desync-safe, which is exactly why the
HD Edition can differ between players. Anything that touches an `.ini` (`gamedata.ini` camera
limits, `gamelodpresets.ini`, any object/weapon/armour value) changes the simulation and **must**
be byte-identical on both machines, as our edited `ini.big` / `__patch202.big` already are. If in
doubt, send the friend the same files `scripts/install-mod.sh` put in.

## f. First milestone: one hero, round-tripped

1. `python3 tools/bigtool.py list W3D.big | grep -i <hero>` to find the mesh, skeleton and anims.
2. `python3 tools/bigtool.py extract W3D.big "art\w3d\..._skn.w3d" -o ~/w3dwork` — extract the
   skeleton and the textures it names into the *same* folder (the add-on requires that).
3. Import in Blender with `io_mesh_w3d`, change nothing, export straight back out. Diff the sizes;
   confirm the bone names survived. This is the step that proves the pipeline before any art time
   is spent.
4. `python3 tools/bigtool.py replace W3D.big "art\w3d\..._skn.w3d" newfile.w3d` (it keeps a `.bak`),
   or `pack` a small overlay archive named so it sorts last and drop it in with
   `scripts/install-mod.sh rotwk <dir>` — that backs up as `.premod.bak` and has a `--revert`.
5. Rebuild `asset.dat` with `AssetCacheBuilder` in the same Wine prefix (§c) — only needed if a
   *name* is new; a same-name replacement usually does not need it. Keep the old `asset.dat`.
6. `scripts/play-rotwk.sh`, start a skirmish, buy the hero, look at it. Then change something
   obvious (a texture tint) and repeat to confirm you are really seeing your file.

## g. The big mods

The large SAGE mods are Windows installers aimed at a retail install. **Edain** (RotWK) needs the
*official* 2.01 patch and BFME2 1.06 — explicitly **not** the unofficial 2.02/1.09 we run, which
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
