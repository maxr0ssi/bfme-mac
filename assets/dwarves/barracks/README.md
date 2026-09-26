# Dwarven barracks (`DwarfBarracks`)

Model `EBBarracks_SKN` is skinned, with a separate skeleton `EBBarracks_SKL`. The redesigned mesh
is `EBBARRAKA`. It is the rigid body: the gate cut into the rock and the two stair wings. It gets
its own texture, `EBBarrackH.tga` / `EBBarrackH_NRM.tga`, plus the snow variant
`EBBarrackH_Snow`. This is a two-sheet build: EA's `EBBarracks` sheet for the old faces, and the
fortress atlas for the new ones.

Nothing else changes: the rock, the level-2 seated dwarf `V1`, the level-3 watch tower `V2`, the
weapon racks, the torches, the night windows, the animated dwarf and the bones.

## What changed (body, healthy)

- **Gate.** EA's small doorway becomes a monumental door:
  - a deep, stepped, pointed portal: two triangle-frieze rings with bronze reveals, and an outer
    stone ring with stepped plinths at the jamb feet;
  - a gold rune tympanum and a rune lintel;
  - a bronze cornice with a gilded pinnacle at each end;
  - above it, a stepped frontispiece (triangle tier, bronze tier, stone gable) with a gilded
    finial at z 46;
  - an Erebor-blue banner on each jamb.
- **Stair wings** (wing B is built as the mirror of wing A in the line y = -x). Each prow gets:
  - a keel buttress on its nose: plinth, battered body, bronze step;
  - a bronze corbel, a gold rune band and a bronze coping round its rim;
  - solid chevron parapets with gilded tips;
  - five piers with rune belts and gilded points. The nose pier is a tall diamond that flies a
    small banner.
- **Banner cloth.** It moves to `EBHCBarracks` (`house_tags`) and takes the player's colour.

## What stays usable

- **Doorway.** EA's doorway (|u| <= 4.6, head at z 20.4) stays open.
- **Torches.** The torch pedestals (d >= 36.8) and their fires (to z 10.4) are in front of the
  portal (d <= 36.6).
- **Night windows.** They are in the rock at |u| 13..22, z 9..18, and nothing new stands there.
- **Racks and yard.** The racks and pikes are untouched, and the yard stays empty.
- **`V1` at level 2.** Its lap and forearms reach d 31 / 33 / 35 at z 28-32 / 32-36 / 36-40.
  The lintel, cornice and frontispiece stay in front of those planes.
- **`V2`.** Nothing new comes near it.

Here u = (x + y)/sqrt 2 runs across the front and d = (x - y)/sqrt 2 runs towards the camera.

## Numbers

- **Footprint:** unchanged.
- **Height:** 41.16 -> 46.0 (+11.8 %, limit +20 %).
- **Triangles:** `EBBARRAKA` 828 -> 3314 (budget 15,000).
- **Texel density:** median 12.3 px/unit.
- **Checks:** 146/146.

## Status

| Part | Healthy | Construction | Damaged | Really damaged / rubble | Snow | LOD M/L |
|---|---|---|---|---|---|---|
| body (`EBBarracks_SKN`) | built, checks pass, **awaiting review** | old (`EBBarracks_ASKN` carries `EBBARRAK`, not this mesh) | old (see below) | old | `EBBarrackH_Snow` painted | old |
| banner (`EBHCBarracks`) | our 4 banners' cloth added | | | | | |

## Framework notes (worked around here, `fixes.py` and `derived_models`)

1. **32-bit normal map.** EA's `ebbarracks_nrm.tga` is 32-bit (BGRA, alpha 255 everywhere,
   descriptor 0x08). This was first worked around here; `sagekit/paint/imageio.py` now reads and
   writes 32-bit TGAs itself (82 of EA's normal maps are 32-bit), so the workaround is gone.
2. **EA's degenerate triangles.** EA's `RACKPIKE` has 2 zero-area triangles of its own. The
   "zero-area faces" check counts them against us, even though the mesh chunk is byte-identical.
   `fixes.py` discounts them for that mesh only.
3. **Damaged state.** EA's `EBBarracks_D1` draws this body with one plain texture
   (`ebbarracks_d1.tga`, no normal map), while our export carries a diffuse + normal pair.
   `Derive` renames only the texture names found in EA's file, so the spliced D1 body would keep
   `EBBarracks.tga` on our new UV layout (garbage in game). `derived_models` leaves D1 to EA for
   now, so the damaged state shows EA's old body.

## Note for review

When the house step is installed, EA's own house banner in `EBHCBarracks` shows in skirmish too,
not only in multiplayer (`MultiPlayerOnly = No`). That banner is a tall flag on a pole in the yard,
in front of the right jamb, and from the RTS camera it hides that jamb's banner. In multiplayer
it was always there.
