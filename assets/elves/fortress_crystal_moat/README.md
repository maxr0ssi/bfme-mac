# Elves fortress crystal moat (`ElvenFortressCrystalMoat`)

EA's ring of water round the fortress (its own object, drawn at the fortress's origin), dressed as a
Lórien water-garden. Own texture `EBFortresM.tga` (DXT5). EA's water (`EBFCMOAT2`) is untouched.

## What changed (body `EBFCMOAT1`, healthy)

- **Coping.** A moulded moonstone cap over the parapet (z 4.7..5.6), its nose over the outer face.
- **Knotwork band.** Silver knots on sea-green enamel between gilt beads along the outer face
  (z 0.7..1.7), round all fifteen faces.
- **Leaf drapes.** A leaf drape (7.6 x 3.05, house colour) over the middle of every face, its gilt
  rod tucked under the coping's nose.
- **Crystals.** Two clusters of four leaning hexagonal starlight crystals per face, rising from the
  water (the tallest to z 5.9).

The object had no house-colour model: `HOUSE_DRAW` gives it one of our own, `EBHCFCMoat`, copied
from the style's `house_template` (`sagekit house`).

## Numbers

- Height 5.0 -> 5.8 (+16 %, limit 20 %). The drapes' rods stand 0.78 and the band 0.45 proud of the
  outer face: `footprint_margin = 0.8` (the moat's collision comes from the INI).
- Triangles 158 -> 5,354 (budget 6,000; the crystals are 2,160 of them). Texel density median 13.4.
- Checks: 43/43. House colour: 180 cloth faces -> `EBHCFCMoat`.
- Lifecycle: `EBFCMoat_D1`, `_D2`, `_D3` stay EA's ("no body pieces of ours"); their faces are
  recoloured by the faction sheets.

## For review

Under the 20 % limit the moat can rise only 1 unit, so from the RTS camera the crystals read as
glints and the drapes as small patches of colour. Taller crystal spires (to z ~12) would show from
the camera: a height decision for Max.

## Night lights

No night meshes in EA's model; none declared.

## Status

| Part | Healthy | Damaged / really damaged / rubble |
|---|---|---|
| moat (`EBFCMoat`) | built, checks pass, **awaiting review** | EA's (recoloured) |
| banner (`EBHCFCMoat`, ours) | our drapes | |
