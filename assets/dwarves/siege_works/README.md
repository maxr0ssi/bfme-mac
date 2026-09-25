# Dwarven siege works (`DwarvenSiegeWorks`)

Model `DBForge`, redesigned mesh `DWARFBUILDING`, painted from its own sheet `DBforge.tga`
(own textures `DBforgH.tga` / `DBforgH_NRM.tga`; variants `DBforgH_D1.tga`, `DBforgH_Snow.tga`).
`Tier.STANDARD`.

The building is a forge hall with a great chimney, standing behind a walled pit. The pit floor is
the two-leaf hatch (`DBForgeDr_SKN`) that the siege engines come up through. The engines then
leave down the front grille ramp toward the rally point at -Y. The mesh hangs from bone
`DWARFBUILDING` at (27.71, 38.31, 49.08), so in mesh coordinates the ground is at z = -49.1.
`building.py` lists every measurement it uses.

## What changed (body, healthy)

- **Chimney** (the silhouette): a battered crown ring on the cap, with a bronze band and a hexagon
  frieze. It has stepped-pyramid finials on the four chamfers and stepped gables on the four sides.
  Angular corbels sit under the cap, and a bronze-edged rune belt goes around the shaft. The flue
  (and the `SMOKE01` bone at its centre) stays open.
- **Hall roofline**: a coping along the hall front, with chevron (stepped-triangle) slabs and
  corbels. The slabs stop short of the left block that overhangs the roof. The anvil on the roof
  is left alone.
- **Pit enclosure**: chevron parapets with corbels on the outer edges of both side walkways and
  their front chamfers. The walkways' pit-side faces carry rune friezes, and a battered plinth runs
  under the +X wall.
- **Slab pairs** at the back corners of the pit: each pair is bound by a stepped hip cap (bronze
  band, two battered steps, a ridge with triangle frieze on its slopes).
- **Exit**: two squat battered pylons flank the grille ramp, like small versions of the fortress's
  gate pylons. Each has a stepped plinth, rune belt, triangle cornice and a stepped cap with a point.
- **Paint**: the faction style (honey granite, bronze trim, gold-inlaid runes), automatic.

Kept clear: the pit and the hatch leaves' swing (hinges at x = -52.5 and x = -2.7, open height
z ~ -19.7), the exit ramp, the stairs, the anvil, the smoke bone. No other mesh or bone touched.
`bake_hidden` leaves the effect cards (`N_GLOW`, `FIRE CARDS`) out of the bakes and renders.

Footprint unchanged, height +12 % (limit 20 %), 985 -> 2,937 triangles (budget 15,000).

## Status

| Part | Healthy | Construction | Damaged / really damaged | Rubble | Snow | LOD M/L |
|---|---|---|---|---|---|---|
| body (`DBForge`) | redesigned, built | our body (derived `DBForge_A`) | our body (derived `DBForge_D1`, `_D2`) | old | variant sheet | old |
| hatch (`DBForgeDr_SKN`) | old | old | | | | old |
| banner (`DBHCforge`) | old | | | | | |

Build: every check on `DWARFBUILDING` passes. The build as a whole still stops at `checks` (83/88)
because of 5 framework failures on EA's untouched meshes (see below). It is not installable until
those checks are fixed in `sagekit`.

## Framework issues found (sagekit, not this recipe)

1. `checks_suite`: "UV layers as the original, inside [0,1]" fails on EA's own meshes whose UVs
   tile outside [0,1] (ANVIL 138, ROCK 606, FIRE CARDS 12 out). Their mesh chunks are
   byte-identical to EA's. The check should compare against the original rather than require
   [0,1].
2. `checks_suite`: "parented to bone" fails for meshes EA attaches to the armature root with no
   bone (N_GLOW, N_WINDOW: original parent bone empty). It compares against ("BONE", "") instead of
   the original's parent type.
3. `render`: `Workspace.texture_map()` only knows the target's sheet. `game_material` then raises
   `KeyError: 'dbfortress1.tga'` on N_WINDOW (and would do the same on V2/ROCK/ANVIL:
   DBMineA/DBStoneA/EBForge). So the pipeline's render step fails for this model. The review
   renders were made with sagekit's own `render` job plus texture overrides for those meshes.
4. (Already fixed upstream during this run by `scene.plain_placeholders`.) The variant bake crashed
   Blender in `blf_font_draw_buffer` while filling several COLOR_GRID placeholder images at once.
