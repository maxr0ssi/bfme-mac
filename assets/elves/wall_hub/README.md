# Elven wall hub (`ElvenCastleWallHub`)

Model `EBWallRmprtN`, mesh `EBWALLRMPRTN`, own texture `EBFortresC.tga` (from `EBFortress.tga`,
cut-out alpha kept). `Tier.STANDARD`. The [fortress wall hub](../fortress_wall_hub/README.md) reuses
`crown`, `dome` and `lanterns`. EA's round tower, lancet windows, ivy and separate lattice dome
stay whole.

## What changed

- **Rim**: the walls' filigree band and mithril coping, no merlons; crystal lanterns on silver posts.
- **Dome**: gold ribs up EA's dome to a gilt collar, a leaf coronet and a finial.
- **Banners**: none; no added window frames.

## Kept clear

- The footprint (x ±24.09, y ±22.83).

## Status

Installed with the Elven pack. 374 -> 3,658 triangles, height 53.05 -> 74.10 (+39.7 %), 86/86
checks. `max_z_growth = 0.40`: the target ends at 53.05, EA's separate dome at 67.6, and the crown
grows from the dome. The game draws `EBWallRmprtN_A` healthy too; it and damaged derive the new
body from the static source (not construction's underground first pose). Really damaged and
collapse are rebuilt along EA's pieces, collapse from EA's rest pose.
