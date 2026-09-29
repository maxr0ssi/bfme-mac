# Elven wall segment (`ElvenCastleWallSegment`)

Model `EBWallN`, mesh `EBWALLN`, own texture `EBFortresB.tga` (from `EBFortress.tga`, EA's cut-out
alpha kept). `Tier.STANDARD`. The crown profile is [`wall.py`](wall.py), shared by every Elven wall piece.

## What changed

- **Crown**, both faces: a filigree band between gilt beads, a mithril coping and a crest of
  gold-edged leaf merlons, spaced so a stretched or neighbouring segment continues the rhythm.
- EA's lancet windows, pointed hoods, leaf emblems and V cornice are kept whole.
- **Banners**: none (segments repeat along a wall).

## Kept clear

- The ends (y ±19): only the crown reaches them; everything stays inside x ±4.9.

## Status

Installed with the Elven pack. 326 -> 1,952 triangles, height 51.2 -> 58.2 (+13.7 %), 84/84 checks.
Construction, damaged and the placement cursor derive the new body; really damaged and collapse are
rebuilt along EA's pieces. Shared `GBWall_Rubble` stays EA's.
