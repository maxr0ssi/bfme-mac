# Dwarven troops and upgrades

Scope confirmed with Max, 2026-09-26: troops and equipment upgrades first; heroes later.
The full troop redesign is built and staged for review. The already installed building and
builder packs are unchanged; no troop package has been installed and no game was launched.

## Redesign and motion review

```sh
python3 -B -m assets.dwarves.troops.build
python3 -B -m assets.dwarves.troops.audit
python3 -B -m assets.dwarves.troops.motion_check
python3 -B -m assets.dwarves.troops.preview
```

The new gallery is `build/assets/dwarves/troops/redesign/review.html`. Select a troop, equipment
combination and motion. Paired pictures use the same authored clip, lighting and camera.
`--unit`, `--variant` and `--pose` narrow previews; existing renders resume unless `--force` is
given. All legal equipment combinations have stills; base and representative upgraded loadouts
have every catalogued pose animated. `--all-variants` additionally animates redundant equipment
combinations. Motion GIFs sample each full clip; the separate audit decodes every frame of all
available source clips matching these rigs.

The design uses warm neutral wool, bronze/gold details, dark iron and timber. Fixed blue cloth
and enamel were rejected in review; original team-colour masks remain unchanged.
Fitted forged edging, clasps, angular joinery and axle caps sit on existing model surfaces.
Original body geometry, UVs, skin weights, texture dimensions and animation files are retained.
Meshes carrying secondary skin channels stay whole; fitted additions only touch supported meshes.
Mount fur, horns and barding retain the original source sheet.
Lower-detail models retain their original geometry and receive the same private palette.
Faces/hair are protected in the painting pass; original DXT3/DXT5 alpha blocks and mip counts
are preserved, including the non-power-of-two Zealot sheet and translucent banner edges.

Every redesigned model and painted texture has its own name. Visual model/texture directives
are changed only in the targeted Dwarven INIs. Private house-colour mappings retain the original
masks. No original shared sheet/model, gameplay directive, animation or skeleton is shipped.
The staged archive/caches under `redesign/staged/` are review artifacts, not an installer. A
reviewed installation must freshly compose the current caches/house-colour table and retain a
scoped `--revert`; never copy staged cache files over a later installation blindly.

## Validation limits

Geometry, source hashes, private asset ownership, visual-only INI edits, untouched live files,
texture masks/mips and animation transforms are checked. Existing absent/empty animation
references and incompatible passenger death routes are recorded in `motion-checks.json`, not
invented or silently repaired. These inherited defects are not introduced by the redesign.
The previews show the original fire/forged weapon meshes but do not simulate particle systems,
launched projectiles or player-colour blending. Catapult flaming ammunition remains the original
weapon/FX; there is no invented fire skin. Runtime appearance and performance await player review.

## Original source survey

`python3 -B -m assets.dwarves.troops.review --render` extracts active installed models,
textures, skeletons and idle animations, records source hashes and archive owners, and renders
the review gallery in `build/assets/dwarves/troops/review.html` and `roster.jpg`.
It checks animation hierarchy and finite transforms across every decoded idle frame.
Creation-script hides are reflected in the base portraits; the Zealot source variants are
shown separately. Game effects, lighting and player-colour blending are not simulated.

## Complete visual scope

| Troop | Equipment and variants to carry through the redesign |
|---|---|
| Guardian | Base axe/shield, forged blades, alternative siege hammer, Mithril Mail with either weapon path |
| Phalanx | Base pike/shield, forged blades, Mithril Mail, formation poses |
| Axe Thrower | Base, forged blades, Mithril Mail, thrown axe |
| Men of Dale | Base, Mithril Mail, fire arrows, nocked arrow and projectile |
| Zealot | Both halberd/hammer source appearances and ability weapons; no purchased armour upgrade |
| Battlewagon | Base, hearth, banner with Phalanx passengers, Axe Thrower passengers, Men of Dale passengers; armour for each upgraded role |
| Demolisher | Base, Mithril Mail, deployed and moving forms, destruction |
| Catapult | Base, flaming ammunition, firing/build/death states |

Include Guardian, Phalanx, Axe Thrower and Men of Dale banner models. Preserve faction player
colours and troop-specific recognition. Heroes, construction workers and the neutral Inn's
Hobbit recruits are outside this troop-art pass. Child/summoned uses of shared troop models
must be reviewed for unintended changes. Do not recolour shared assets for unrelated factions.

## Findings that affect the work

- Guardian forged blades and siege hammers are mutually exclusive; armour combines with either.
- Battlewagon armour becomes purchasable after selecting a role; it is not absent simply because
  its purchase button is commented out in the initial commandset.
- The active HD Men of Dale model lacks the INI's requested `ARMOR` subobject. Its armour texture
  exists. Review the actual model and texture path rather than assuming an overlay exists.
- Catapult Flaming Shot changes the weapon/projectile, not its body texture.
- The Zealot's two complete source models use `ExtraMesh:Yes`; exact runtime selection remains
  unverified. Its random-texture list names a sheet absent from the active HD models.
- The building draw parser stops early on some troop `LodOptions` blocks. This roster was checked
  directly against active recruitment, object, upgrade and creation-script definitions.

Detailed audit: `build/assets/dwarves/troops/upgrade-audit.md`.

Base and upgraded looks are reviewed together. No troop art is installed by any tool here.
