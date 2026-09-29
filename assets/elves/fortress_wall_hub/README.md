# Elven fortress wall hub (`ElvenCastleWallHubExpansion`)

Model `EBEFWHub`, mesh `EBWALLRMPRTN01`, own texture `EBFortresX.tga` (from `EBFortress.tga`, EA's
cut-out alpha kept). `Tier.STANDARD`. The design is the [wall hub](../wall_hub/README.md)'s,
including its height bound for EA's separate dome.

EA's body, lattice dome and short connecting wall run stay whole.

## What changed

- **Rim**: a filigree band and mithril coping, no merlons; crystal lanterns.
- **Dome**: gold ribs and a leaf crown.
- **Banners**: none; no window frames.

## Status

Installed with the Elven pack. 374 -> 3,658 triangles, height 53.05 -> 74.10 (+39.7 %,
`max_z_growth = 0.40`), footprint unchanged, 88/88 checks. Damaged derives the new body; really
damaged and collapse are rebuilt along EA's pieces, collapse from EA's rest pose. Construction is
`EBWallRmprtN_A`, which [`wall_hub`](../wall_hub/README.md) builds and ships.
