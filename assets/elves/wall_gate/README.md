# Elven wall gate (`ElvenCastleWallGate`)

Model `EBWallGateN_SKN`, redesigned mesh `EBWALLGATEN`, `Tier.STANDARD`, painted from
`EBFortress.tga` onto its own textures `EBFortresD.tga` / `EBFortresD_NRM.tga` (+ `_D`, `_snow`,
`_U` variants), DXT5 (EA's cut-out alpha kept).

EA's gate is two square towers (x +-9.3, |y| 40.16..58.68, to 47.4, a flared cap with a knotwork
pyramid to 60.16) carrying warrior statues with torches (`LUSTATUE`, `FLAMES01`), and between them
four lattice door leaves with pointed tops (`EBGATEDOOR00..03`, z <= 48.5). The leaves fold open to
the -x side, ending along x -20..0 against the towers' inner faces
(`EBWallGateN_SKL.EBWallGateN_OPN`). All of EA's other meshes are untouched.

## What changed (body, healthy)

- **Bridge:** the walls' crown across the gap between the towers (the shared profile,
  [wall_segment/README.md](../wall_segment/README.md)): its stone core is the bridge, its underside
  at 48.9, 0.4 over the leaves' points; filigree band, silver coping and 20 lancet merlons per face.
  It runs 0.5 into the towers' crown rings.
- **Arch:** a free pointed arch over the bridge's middle (half width 6, spring 60, apex 67, silver
  fronts, sea-green reveals, leaf tip 0.25, gilt leaf finial) with a
  crystal lantern hung in it.
- **Tower heads:** the crown round each flared cap (a square face line of half size 9.7), four
  lancet merlons per side, a crystal lantern on each corner; EA's statues stand inside.
- **Banners:** a long leaf banner (7.5 x 28) down each tower face that looks out of the wall (4),
  under the cap's flare; cloth to our house-colour model `EBHCWallGateN_S` (the framework's name,
  cut to 15 characters), Draw tag `ModuleTag_Draw_HCWallGate`.

Gameplay geometry kept: nothing new below z 48.9 over the passage (|y| < 40.16) or in the leaves'
travel; the towers' outer faces (|y| 58.68), where the segments meet, are left alone; the footprint
(x -10.26..10.24, y -59.65..59.68) is unchanged. Height 60.16 -> 71.39 (+18.7 %, limit 20 %),
128 -> 8,622 triangles (44 cloth faces moved to `EBHCWallGateN_S`). `checks`: 115/115 pass.

## Status (`python3 -m sagekit inventory elves/wall_gate`)

| Part | Healthy | Damaged (`_D1`), really damaged (`_D2`), collapsing (`_D3`, `_D4`) / snow / stonework |
|---|---|---|
| body (`EBWallGateN_SKN`) | done, rendered, not installed | derived: EA's body is the healthy one on one bone in all four, so ours goes in whole and EA's animations move it |

## Night lights

TODO, as the segment: no night meshes or `NightWindowName` in EA's gate (the statues' torches are
EA's fire effect meshes). The four head lanterns and the arch lantern are ready for starlight.
