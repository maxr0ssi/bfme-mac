# Dwarven troops and upgrades

Troops and equipment upgrades; heroes later. Built and staged; not installed.

## Commands

```sh
python3 -B -m assets.dwarves.troops.build
python3 -B -m assets.dwarves.troops.audit
python3 -B -m assets.dwarves.troops.motion_check
python3 -B -m assets.dwarves.troops.preview
python3 -B -m assets.dwarves.troops.review --render
```

The gallery is `build/assets/dwarves/troops/redesign/review.html`: pick a troop, an equipment
combination and a motion; each pair uses the same clip, lighting and camera. `--unit`, `--variant`
and `--pose` narrow the previews, `--force` redoes existing renders, `--all-variants` also animates
the redundant equipment combinations. `review --render` renders EA's originals
(`build/assets/dwarves/troops/review.html`, `roster.jpg`).

## Design

Warm neutral wool, bronze and gold details, dark iron and timber; EA's team-colour masks are kept.
Forged edging, clasps, angular joinery and axle caps sit on the existing surfaces. EA's body
geometry, UVs, skin weights, texture sizes and animations are kept. Meshes with secondary skin
channels stay whole; mount fur, horns and barding keep EA's sheet; lower-detail models keep their
geometry and take the same palette. Faces and hair are protected when painting, and DXT alpha
blocks and mip counts are preserved. Every changed model and texture has its own name; only the
Dwarven INIs' visual directives change.

## Scope

| Troop | Equipment and variants |
|---|---|
| Guardian | Base axe/shield, forged blades, alternative siege hammer, Mithril Mail with either weapon |
| Phalanx | Base pike/shield, forged blades, Mithril Mail, formation poses |
| Axe Thrower | Base, forged blades, Mithril Mail, thrown axe |
| Men of Dale | Base, Mithril Mail, fire arrows, nocked arrow and projectile |
| Zealot | Both halberd/hammer source models and ability weapons |
| Battlewagon | Base, hearth, banner with each passenger role; armour for each upgraded role |
| Demolisher | Base, Mithril Mail, deployed and moving forms, destruction |
| Catapult | Base, flaming ammunition, firing/build/death states |

The Guardian, Phalanx, Axe Thrower and Men of Dale banner models are included. Heroes,
construction workers and the Inn's Hobbits are not.

## Known limits

- EA's missing or broken animation references are listed in `motion-checks.json`.
- The previews do not simulate particles, projectiles or player-colour blending.
- EA's HD Men of Dale model lacks the `ARMOR` subobject its INI asks for; the texture exists.
- The Zealot's two source models use `ExtraMesh:Yes`; which one the game picks is unverified.
- The building draw parser stops early on some troop `LodOptions` blocks; the roster was checked
  against the INIs directly. Full audit: `build/assets/dwarves/troops/upgrade-audit.md`.
