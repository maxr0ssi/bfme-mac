# Elven troops and upgrades

Private troop art is staged for review only. Heroes and builders remain outside this pass.
No command here installs assets or launches the game.

```sh
python3 -B -m assets.elves.troops.build
python3 -B -m assets.elves.troops.audit --motion
python3 -B -m assets.elves.troops.preview
python3 -B -m assets.elves.troops.audit --previews
```

The gallery is `build/assets/elves/troops/redesign/review.html`. Every equipment combination
has paired original/proposed stills; representative loadouts use the original authored clips.
Filter with `--unit`, `--variant` and `--pose`. Existing previews resume; `--force` refreshes
art after a change. GIFs sample the whole clip at its nominal duration. The motion audit
separately decodes every frame of matching available source animations. The offline poser evaluates
both primary and secondary bone coordinates and their original weights. Meshes using secondary skin
arrays receive texture changes only; their original body geometry remains byte-exact.

The design uses the Elven buildings' neutral cloth and fitted metal edging.
Original body vertices, faces, UVs, normals, skin weights, rigid bindings and skeletons are
retained. Lower-detail models keep their source geometry. Face/hair regions, texture dimensions,
source alpha and mip counts are checked; player-colour masks are copied exactly.

The shared Dwarven staging and preview pipeline is reused through explicit faction configuration.
All models and painted sheets receive private names; only targeted troop visual directives are
changed. Shared hero, builder, source sheets, skeletons and animations are not replaced. The
recruited fortress Eagle receives its own inherited draw block, leaving the parent hero intact.
Source animation omissions or incompatibilities are recorded, not silently repaired.
The source Mirkwood shield has an incomplete single-level mip chain; that original count remains
unchanged and the audit records it. Ent bark, Eagle feathers and horse hides keep their natural
source appearance. The Mirkwood leaf cloak retains its green upper region.

The staged archive and cache files are review artifacts. A later reviewed installation must
freshly compose current caches and the house-colour table and provide a scoped `--revert`.
Do not copy staged caches blindly over a later installation. The live-file snapshot and source
hashes are verified by the audit. Player-colour blending, particle effects, projectile flight,
and in-game lighting are not simulated; runtime approval remains with the player.
