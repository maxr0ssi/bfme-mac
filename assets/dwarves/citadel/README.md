# Dwarven summoned citadel (`DwarvenSummonedCitadelKeep`)

Model `DBCitadel`, redesigned mesh `TOWER` (the three tower heads, the tower plinth and the gate),
`Tier.STANDARD`, painted from the faction atlas `DBFortress1` onto its own textures
`DBFortressK.tga` / `DBFortressK_NRM.tga` (+ `DBFortressK_Snow.tga`). The rock (`STONEA`), the
three statues and the door are EA's, byte for byte.

The citadel is a rock spire with tower heads breaking out of it; it takes the redesigned
fortress's language so the two read as one family.

## What changed (body, healthy)

- **Keep (the tall octagonal tower):** a crown ring on the rim over the rune band (bronze corbel,
  triangle frieze, battered parapet), stepped-pyramid blocks on the four flat sides and stepped
  gables on the four long chamfers. The bronze disc inside is kept. The +Y face is the bounding
  box, so the ring's path is pulled 1.3 in there.
- **Shield tower (the turned square with the double-window shields):** the fortress's own tower
  head and crown (corbel + hexagon frieze, stepped crown ring), lowered onto the shields just clear
  of the windows, with its corners cut on the corner posts; stepped pyramids on the cut corners,
  stepped gables over the shields, and a gilded stepped pinnacle on the stone cap (over its vent).
- **Round tower (hexagon of bronze shields):** the keep's crown ring and a stepped gable on each
  side (its -X corner is the bounding box: the path is pulled 1.5 in there).
- **Gate:** a deep stepped pointed portal round EA's opening (triangle frieze on the ring fronts,
  bronze reveals), run back into the rock so no side shows a hollow; over it a rune lintel, a
  bronze cornice, a triangle-frieze tier, a hexagon tier and a stepped gable. EA's bollards stand
  in front of it.
- **Banners:** two banner poles (height 40, banners 6 x 17) either side of the gate, at the front
  edge of the bounding box. The citadel had no house-colour model: the framework gives it one
  (`DBHCCitadel`, from the style's template), so the cloth takes the player's colour once
  `sagekit house dwarves` has run.
- **Flame upgrade:** `DBFFlam` (dwarves/fortress_braziers) stands its braziers on open ground at
  x 80.8..90.4, beside the right statue; nothing here comes near them (checked in a render with the
  rebuilt braziers at the same origin).

Footprint unchanged (x -50.47..52.92, y -40.71..52.5), height 110.3 -> 122.5 (+11.1 %, limit
20 %), `TOWER` 838 -> 2,958 triangles. `checks`: 73/73 pass.

## Status (`python3 -m sagekit inventory dwarves/citadel`)

| Part | Healthy | Construction (`_A`) | Damaged (`_D1`) | Really damaged / rubble (`_D2`, `_D3`) | Snow |
|---|---|---|---|---|---|
| body (`DBCitadel`) | built, rendered, not installed | derived: carries the new body | EA's (see below) | EA's | own `_Snow` sheet |
| flames (`DBFFlam*`, improvement 1) | dwarves/fortress_braziers | | | | |

## Work-arounds in the recipe (framework)

- EA's citadel files name the sheet in lower case (`dbfortress1.tga`); the derived-model check
  (`checks_suite.py`, `own.get(t, ...)`) looks it up case-sensitively. `texture_names()` returns a
  dict whose `get` ignores case.
- `DBCitadel_D1`'s `TOWER` uses legacy vertex materials (chunks 0x2a/0x29/0x30, no 0x50 shader
  materials). The derive step keeps our export's shader materials unrenamed, so the damaged model
  would draw our layout with EA's `dbfortress1.tga`. `derived_models()` leaves D1 to EA.
