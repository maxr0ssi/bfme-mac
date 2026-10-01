# The other factions: plan and tools

Dwarves (35 recipes, about 6,000 lines), Elves (23) and Men of the West (44, Arnor included) are
installed, and so are the Goblins (14). Isengard has 25 measured stubs, its palette and a citadel shape pass; Mordor has 25 stubs and
four palette options; Angmar is surveyed only. The engine map is
[ART.md](ART.md); every faction inherits the standards in it. The numbers below come from a
read-only survey of the game (2026-09-25).

## Factions not done

| Faction | Buildings in scope | Design units | Lifecycle models | Map castle pieces | Notes |
|---|---|---|---|---|---|
| Goblins | 14 | 14 | 51 | 18 | rock and caves; installed ([ROLLOUT](../assets/goblins/ROLLOUT.md)) |
| Isengard | 19 | 25 | 90 | 22 | borrows Mordor's lumber mill; 25 measured stubs, palettes and the citadel's first pass ([ROLLOUT](../assets/isengard/ROLLOUT.md)) |
| Mordor | 14 | 19 | 65 | 29 | no player walls; Barad-dur pieces up to 14k triangles; 25 stubs (the Haradrim palace and mumakil pen from `structures\evilmen`), palette options ([ROLLOUT](../assets/mordor/ROLLOUT.md)) |
| Angmar | 20 | 21 | 87 | 0 | ice effect meshes; three master sheets |

80 design units in all. Rohan is not a faction in RotWK; its art is map-placed civilian buildings
only.

## Tools

### Built

| Tool | Command | What it saves |
|---|---|---|
| Ownership map | `sagekit owners <faction>` | never recolouring another faction's sheet or model (the `eb` folder mixes Elves and Erebor; WBCave spans three factions) |
| Alpha safety | automatic | DXT5 cut-outs survive bake and paint (Elven, Isengard, Mordor, Angmar sheets) |
| House models by texture | automatic | finds EA's house models without an `HC_` name, and copies shared ones |
| Recipe scaffolder | `sagekit new <faction> --write` | one measured stub per design unit, flags and free names filled in |
| Auto-measurer | `sagekit measure <faction>/<building>`, `measured(self)` in design | EA's footprint, planes, levels, openings and heads; matched the Dwarven hand-typed numbers within 0.2 (one corner missed) |
| Floating-banner fix | automatic | previews draw only a building's own cloth |
| 32-bit TGA | automatic | 82 of EA's normal maps are 32-bit; no recipe workarounds |
| Shape preview | `sagekit preview <faction>/<building>` | the real geometry job, EA's model and ours in flat atlas-tag colours and the bake-free checks in 10-20 s instead of 5-10 min a build; iterate with it, full builds only for review |
| Style board | `sagekit board <faction>` | EA's buildings as they are in one labelled grid, before any recipe exists |
| Palette options | `sagekit palettes <faction>` | the style's `palettes` on EA's citadel side by side with swatches; the Goblins' were one-off scripts |
| A100 offload | `sagekit offload pack\|run\|results\|unpack` | a faction's full-quality Blender builds on a Colab A100: [OFFLOAD.md](OFFLOAD.md) |

### Next, in the order they pay off

1. **Role kits.** The Dwarven and Elven wall sets, fortress upgrades, expansions and old castle
   walls, parameterised by a faction profile (crown, band, parapet rhythm, banner placement).
   Every faction's wall segment tiles the same 38-unit slot; Mordor's and the Goblins' old castle
   walls are exact copies of the Dwarven placeholders. A new faction's walls start as one profile.
2. **Lifecycle review aid.** The lifecycle choice uses open backs only; thin shards and a big
   solid riding a small chunk need a human look. A contact sheet per faction of every state at
   its worst frame, generated with the build, makes that look quick.
3. **Night meshes of our own.** EA lights only models that have night meshes, so our lanterns on
   the Elven statue, mirror, walls and expansions stay dark. A framework option to add a night
   sub-object (and its INI `NightWindowName`) where EA had none.
4. **DXT1 where alpha never shows.** 22 of the 23 Elven targets are drawn with alpha test off;
   DXT1 would halve their diffuse memory with no visible change. Needs the owner's decision.
5. **Isolate the `shared` step.** It imports every faction, so a syntax error in one faction's
   in-progress file breaks every build. Make it import only the factions being built.

## Units

| Unit set | State | Where |
|---|---|---|
| Unit framework | built: recipe, checks, posed renders, install and revert in any order | `sagekit/units/`, [UNITS.md](UNITS.md) |
| Dwarven builder | installed, not checked in game; ported, rebuilds byte for byte | [assets/dwarves/porter/](../assets/dwarves/porter/) |
| Elven builder | installed, not checked in game; ported, rebuilds byte for byte | [assets/elves/porter/](../assets/elves/porter/) |
| Men builder (Gondor and Arnor, `GUPorter_SKN`) | stub: EA's, rendered | [assets/men/porter/](../assets/men/porter/) |
| Goblin builder (`WUPorter_SKN` as `WUBuilder_SKN`) | stub: EA's, rendered | [assets/goblins/porter/](../assets/goblins/porter/) |
| Isengard builder (`WUPorter_SKN` as `IUBuilder_SKN`) | stub: EA's, rendered | [assets/isengard/porter/](../assets/isengard/porter/) |
| Mordor builder (`WUPorter_SKN` as `MUBuilder_SKN`) | stub: EA's, rendered | [assets/mordor/porter/](../assets/mordor/porter/) |
| Dwarven, Elven and Men troops | staged, not installed | `assets/<faction>/troops/README.md` |
| Heroes | not started | |

Units differ from buildings: skinned bodies whose animations (idle, run, hammer, death) must keep
working, and player colour on the unit itself. A unit recipe (`Unit` in `sagekit/units/`, next to
`Building`) reuses what the first two builders proved: source hashes, pieces bound to bones,
animation-pose renders, a private atlas and mask, its own archive and records. Isengard, Mordor,
the Goblins and Angmar share EA's orc porter, so each of the three ships its own copy and repoints
its own object; Angmar keeps EA's. Construction workers (`DUWorker_SKN` and each faction's
equivalent) come later.

## Per faction, the loop

1. **Style session:** palette, the faction's twist, accent and glow colours; a style board of EA's
   buildings and the kit (the Elven board is the template). The owner picks the palette.
2. **Scaffold and measure:** `sagekit new` and `sagekit measure`; check the scaffolder's target
   pick where the stub says it is ambiguous (the Elven statue and mirror picked the wrong mesh).
3. **Pilot one building first** (the faction's citadel); the owner approves it before the rest.
   The bar is the Dwarven before/after renders (`build/assets/dwarves/{fortress,citadel,barracks,
   statue,wall_gate}/renders/compare_*.png`): keep EA's detailed body and enhance it (added
   ornament, metal accents, a few strong silhouette pieces, 2-4 banners), never strip it.
4. **Design in parallel** by role group (fortress and add-ons, expansions, walls, production,
   towers and specials), with shape previews and checks as they go.
5. **Integration pass:** fix what the groups reported in the shared framework, run
   `sagekit house`, rebuild everything and make the poster.
6. **Final builds** (local, or the A100); the poster is reviewed, then installed and checked in game.

## Lessons from the Elves

- Recipes reuse each other: the fortress wall hub subclasses the wall hub, the pad expansions
  share one arch helper, production buildings share a motifs module. Plan shared modules per
  role group before design starts.
- Kit bugs cost the most time (a crack at the arch spring, collinear soffit points, tiled leaf
  blades): every group worked around them separately. Test a new kit's pieces in a real build
  before fanning out.
- Framework options changed while groups were designing (`layout._seams` three times). Freeze the
  framework during design; framework fixes go to the integration pass.

## Order

1. Goblins (in progress).
2. Isengard, then Mordor: they share sheets (WBCave, the lumber mill), so the ownership map gets
   exercised early, and the old castle walls port straight over.
3. Angmar.
