# Dwarven wall end (`DwarvenWallCliffCap`)

Model `DBWallNE`, redesigned mesh `DBWALLNE`, `Tier.STANDARD`, painted from the faction atlas
`DBFortress1` onto its own textures `DBFortressN.tga` / `DBFortressN_NRM.tga` (+ `_D`, `_Snow`,
`_U` variants). The first building built with `world_space = True`.

EA's cliff cap is two wall-segment bays end to end, the piece a wall run ends in where it meets a
cliff: bay A (y -19..19) takes the next segment's slot and meets it at **y = +19** with the
segments' half buttress; bay B (y -57..-19) runs on into the cliff and ends in a plain cut at
y = -57 (no buttress). Its buttresses reach down to z -53 for the falling ground at the cliff's
foot (the object's geometry box is offset to Y -20, Z -40 to match).

`DBWALLNE` hangs under a bone rotated by (-0.5, 0.5, 0.5, -0.5), offset z +0.01: mesh-local
(x, y, z) = world (-y, z - 0.01, -x). All numbers here are world axes (read off the imported
object's `matrix_world`): x -8.34..8.3, y -57..19, z -53..53.01.

## What changed (body, healthy)

- **The wall profile, unchanged:** the segment's own constants (imported from
  `wall_segment/building.py`): coping with bronze drip band and chamfer (top 57.0) on both faces,
  the solid `chevron_parapet` (56.6..63.6), five corbels under the rune band about each niche
  (bay B's plain run to the cut gets two more), the battered plinth in each bay, and a banner
  beside each niche (4 per face, cloth to the house-colour model `DBHCWallNE`, Draw tag
  `ModuleTag_Draw_HCWallNE`).
- **Joint (y = +19):** as the segment's ends: only the coping and the chevron slabs reach it,
  at the segment's exact heights and depths, so the parapet line runs straight on into the
  neighbouring segment (its coping cap meets ours back to back). The plinth stops inside the
  buttress (|y| 11.4) as on the segment.
- **Cut end (y = -57):** a stepped terminal block across the walkway over both parapets: a
  stone tier (52.9..61.0, 0.25 behind the coping face and the cut), a tier with the triangle
  frieze on its end and sides (to 63.6), two stepped tiers (to 66.6, 68.4) and a gilded point at
  72.4. The chevrons start inside it. The coping and bay B's plinth end 0.1 short of the cut, so
  their end caps lie inside the wall and band where they cross EA's end face (no shared plane).
- **Paint:** the faction style, in world axes (horizontal ashlar courses, blue rune band).

Footprint unchanged, height (world z) 106.0 -> 125.4 (+18.3 %, limit 20 %), 296 -> 1,480
triangles (+ 40 cloth faces moved to `DBHCWallNE`). `checks`: 44/44 pass.

## EA's own inconsistency, handled here

The INI's snowy construction state swaps to `DBFortress_Snow.tga`, which no archive has (EA's
typo for `DBFortress1_Snow`); the framework's `variants()` then fails in `extract`. `variants()`
is overridden here to drop swaps to missing sheets (our body keeps its own sheet in that state)
and to keep one variant per sheet (the INI spells the snow sheet `DBFortress1_Snow` and `_snow`).

## Status (`python3 -m sagekit inventory dwarves/wall_end`)

| Part | Healthy | Construction (`_A`) / damaged (`_D1`) / snow / stonework | Really damaged, collapsing (`_D2`, `_D3`) |
|---|---|---|---|
| body (`DBWallNE`) | done, rendered, not installed | derived: our body on the variant sheets | old (EA's skinned broken bodies, recoloured sheets) |

The house-colour model `DBHCWallNE` is made by the faction step `python3 -m sagekit house dwarves`.

## Framework notes (world_space, first use)

- Worked: design in world axes, atlas mapping, UV layout / texel weights, bakes and paint (bands
  horizontal, ground dirt at the foot), cloth to the house model, and the checks' footprint,
  height and sky tests (all on the mesh transformed to world).
- `sagekit/blender/jobs.py` `job_geometry` still logs `BBOX before/after` and `Z growth` from
  `scene.bbox(obj.data)`, i.e. in mesh space (it prints "Z growth 0.0%" here; the real growth is
  +18.3 %). Log only; the checks are right.
- `sagekit/paint/canvas.py` `Canvas.ledge_distance` builds its BVH from `v.co` (mesh space) while
  `pos` / `nrm` are world: the upward ledge rays of the `Streaks` layer test world points against
  the mesh-space body, so ledge grime is missing or misplaced on a world-space building.
