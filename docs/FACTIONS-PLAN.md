# The other factions: plan and tools

The Dwarves took three days and about 6,000 lines of recipes for 26 design units (35 recipes). The
Elves, with the first tools below, took one night: 23 recipes designed by five agents in parallel,
then one integration pass. Five playable factions are left, about 106 design units. This plan says
what every faction inherits, which tools exist, which come next, and in what order the factions go.
The map of the engine is [ART.md](ART.md); the numbers come from a read-only survey of the game
(2026-09-25).

## What is left

| Faction | Buildings in scope | Design units | Lifecycle models | Map castle pieces | Notes |
|---|---|---|---|---|---|
| Men of the West (Gondor) | 28 | 26 | 109 | 38 | Arnor reuses these models 1:1, so it comes free |
| Isengard | 19 | 26 | 90 | 22 | borrows Mordor's lumber mill and furnace |
| Mordor | 14 | 19 | 65 | 29 | no player walls; Barad-dur pieces up to 14k triangles |
| Goblins | 14 | 14 | 51 | 18 | rock and caves; smallest set |
| Angmar | 20 | 21 | 87 | 0 | ice effect meshes; three master sheets |
| Elves (done, not installed) | 22 | 23 | 90 | 3 | review the poster, then install |

Rohan is not a faction in RotWK; its art is map-placed civilian buildings only.

## What every faction inherits (the Dwarven standards)

- **One palette** per faction, in its `style.py`, with its own twist (shapes, atlas, kit).
- **Player colour:** cloth goes to house-colour models; walls and expansions get house models of
  our own, and a house model another faction also draws gets an own copy.
- **Night lights** built on our geometry, glow colour set by the faction.
- **Lifecycle:** construction, light damage, heavy damage and rubble carry the redesign and keep
  EA's animations and effects.
- **Own copies:** a faction never changes a model or sheet another faction draws.
- **Names:** `sagekit names <faction> --write`; `validate` rejects clashes and another faction's
  sheets or models.
- **Checks and renders** for every model shipped, before anything is installed.

## Tools

### Built

| Tool | Command | What it saves |
|---|---|---|
| Ownership map | `sagekit owners <faction>` | never recolouring another faction's sheet or model (the `eb` folder mixes Elves and Erebor; WBCave spans three factions) |
| Alpha safety | automatic | DXT5 cut-outs survive bake and paint (Elven, Isengard, Mordor, Angmar sheets) |
| House models by texture | automatic | finds EA's house models without an `HC_` name, and copies shared ones |
| Recipe scaffolder | `sagekit new <faction> --write` | one measured stub per design unit, flags and free names filled in: set the Elves up in minutes |
| Auto-measurer | `sagekit measure <faction>/<building>`, `measured(self)` in design | EA's footprint, planes, levels, openings and heads; matched the Dwarven hand-typed numbers within 0.2 (one corner missed) |
| Floating-banner fix | automatic | previews draw only a building's own cloth |
| 32-bit TGA | automatic | 82 of EA's normal maps are 32-bit; no more recipe workarounds |

### Next, in the order they pay off

1. **Draft mode.** The Elven night showed the real bottleneck: about 15 builds queued on 4 Blender
   slots, so one design iteration took 20-40 minutes. Draft mode renders with fewer samples at
   half size, skips bakes whose geometry and atlas are unchanged (hash the inputs), and runs checks
   without renders; full quality only for the review build. Expected: iteration builds about 3x
   faster, so the same agents do three times the iterations.
2. **Role kits.** The Dwarven and Elven wall sets, fortress upgrades, expansions and old castle
   walls, parameterised by a faction profile (crown, band, parapet rhythm, banner placement).
   Every faction's wall segment tiles the same 38-unit slot; Mordor's and the Goblins' old castle
   walls are exact copies of the Dwarven placeholders. A new faction's walls start as one profile.
3. **A100 offload** (Colab, about 10-20 A100 hours; Max's idea). The loop: design and iterate on
   the Mac in draft mode; when a faction's recipes are settled, offload the full-quality builds.
   - `sagekit offload pack <faction>`: a bundle of the repo, the extracted EA sources under
     `build/assets/<faction>/*/src` and the building list, as one zip for Google Drive.
   - `tools/colab/offload.ipynb`: installs Linux Blender 4.5 and the W3D add-on, unpacks the
     bundle, runs the Blender steps with 4-6 builds at once (`SAGEKIT_BLENDER_SLOTS`), zips `out/`,
     `work/` and `renders/` back to Drive.
   - `sagekit offload unpack <zip>`: puts the results in `build/`, then the host-only steps that
     touch the game run on the Mac (ship, shared, ini, cache) and checks verify.
   - Needs: `scene.use_gpu()` picks OptiX on Linux next to Metal; `paths` finds Blender through
     `SAGEKIT_BLENDER`. First a proof of concept: one render timed on the A100, no game files.
   - Caveat: EA's source files sit in Max's private Drive during a run.
4. **Lifecycle review aid.** The lifecycle choice uses open backs only; thin shards and a big
   solid riding a small chunk need a human look. A contact sheet per faction of every state at
   its worst frame, generated with the build, makes that look quick.
5. **Night meshes of our own.** EA lights only models that have night meshes, so our lanterns on
   the Elven statue, mirror, walls and expansions stay dark. A framework option to add a night
   sub-object (and its INI `NightWindowName`) where EA had none.
6. **DXT1 where alpha never shows.** 22 of the 23 Elven targets are drawn with alpha test off;
   shipping DXT1 for those halves their diffuse memory with no visible change (Max's call).

## Builders, per faction

Max's call (2026-09-26): each faction gets its own builder, the unit players see most. The first
one exists as a review-only recipe, `assets/dwarves/porter/` (HD Edition's `DUPorter_SKN` as an
Erebor master builder: gold-trimmed timber cart, spoked wheels, stone and plans, the original
helmet kept). It runs as standalone scripts (`unit.py`, `preview.py`) outside the building
pipeline, with no installer yet.

Units differ from buildings: skinned bodies whose animations (idle, run, hammer, death) must keep
working, and player colour on the unit itself. The plan:

1. **Finish and install the Dwarven builder** from the porter recipe: asset-cache records and a
   reviewed, reversible install, like `sagekit install`. Max checks it in game.
2. **A unit track in sagekit**: a `Unit` recipe next to `Building`, reusing what the porter proved
   (source hashes, bone bindings, animation-pose previews) plus the building pipeline's paint,
   house colour, own names and install. Construction workers (`DUWorker_SKN` and each faction's
   equivalent) come with it.
3. **One builder per faction**, in the faction's palette and kit, designed with its citadel pilot
   so they share a look (the Elven builder in soft white, silver and gold).

## Per faction, the loop

1. **Style session with Max:** palette, the faction's twist, accent and glow colours; a style
   board of EA's buildings and the kit (the Elven board is the template).
2. **Scaffold and measure:** `sagekit new` and `sagekit measure`; check the scaffolder's target
   pick where the stub says it is ambiguous (the Elven statue and mirror picked the wrong mesh).
3. **Pilot one building first** (the faction's citadel) and get Max's yes on it. Every design agent's
   brief includes the Dwarven before/after renders (`build/assets/dwarves/{fortress,citadel,barracks,
   statue,wall_gate}/renders/compare_*.png`) as the bar: keep EA's detailed body and enhance it like
   that (added ornament, metal accents, a few strong silhouette pieces, 2-4 banners), never strip it.
4. **Design in parallel:** 4-5 agents by role group (fortress and add-ons, expansions, walls,
   production, towers and specials), draft mode, checks as they go.
5. **Integration pass:** one agent fixes what the groups reported in the shared framework, runs
   `sagekit house`, rebuilds everything and makes the poster.
6. **Final builds** (local, or the A100), Max reviews the poster, install, Max checks in game.

## Lessons from the Elves

- Recipes reuse each other: the fortress wall hub subclasses the wall hub, the pad expansions
  share one arch helper, production buildings share a motifs module. Plan shared modules per
  role group before the agents start.
- Kit bugs cost the most time (a crack at the arch spring, collinear soffit points, tiled leaf
  blades): every group worked around them separately. Test a new kit's pieces in a real build
  before fanning out.
- Framework options changed under running agents (`layout._seams` three times). Freeze the
  framework while design agents run; framework fixes go to the integration pass.
- A syntax error in one faction's in-progress file broke every build (the `shared` step imports
  all factions). Worth isolating.

## Suggested order

1. **Men of the West** next: closest to the Dwarves (stone, walls, same fortress pattern), the
   biggest map castle set, and Arnor comes free.
2. **Isengard, then Mordor, then Goblins:** they share sheets (WBCave, the lumber mill), so the
   ownership map gets exercised early, and the old castle walls port straight over.
3. **Angmar.**
