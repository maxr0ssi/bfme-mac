# Elven troops and upgrades

Troop and equipment-upgrade art for 18 units: Lórien warriors and archers, Mithlond sentries (two
looks), Mirkwood archers, Rivendell lancers, Lindon horse archers, Noldor warriors, five banner
carriers, four Ents and the fortress Eagle. Heroes later; the builder is [`porter`](../porter/README.md).

```sh
python3 -B -m assets.elves.troops.build
python3 -B -m assets.elves.troops.audit --motion
python3 -B -m assets.elves.troops.preview
python3 -B -m assets.elves.troops.audit --previews
```

The gallery is `build/assets/elves/troops/redesign/review.html`: paired EA/ours stills for every
equipment combination, and representative loadouts in EA's own clips. `preview` filters with
`--unit`, `--variant` and `--pose`; `--force` redraws after a change.

## What changed

- **Design**: the Elven buildings' neutral cloth and fitted metal edging.
- **Kept**: EA's vertices, faces, UVs, normals, skin weights, rigid bindings and skeletons. Lower-detail
  models keep their geometry; meshes with secondary skin arrays change texture only. Face and hair
  regions, texture sizes, alpha and mip counts are checked; player-colour masks are copied exactly.
- **Names**: every model and painted sheet gets a private name and only the troops' draw directives
  change; shared hero, builder and source sheets, skeletons and animations are not replaced. The
  recruited fortress Eagle gets its own draw block, so the hero Eagle is untouched.
- **Natural looks**: Ent bark, Eagle feathers and horse hides stay as EA made them; the Mirkwood
  leaf cloak keeps its green upper part.
- The staging and preview pipeline is the [Dwarven troops](../../dwarves/troops/README.md)',
  configured for the Elves.

## Status

Built and staged, not installed: 53 models, 17 textures, 9 house masks. How a troop pack gets
installed: [Troop review](../../README.md#troop-review).

## Known limits

- EA's Mirkwood shield has a one-level mip chain; kept as EA made it.
- Missing or incompatible source animations are listed in `motion-checks.json`.
- Not simulated offline: player-colour blending, particles, projectile flight, in-game lighting.
