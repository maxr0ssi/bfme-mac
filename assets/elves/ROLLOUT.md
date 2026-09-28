# Elven citadel-style rollout

Completion pass: 2026-09-26. The approved citadel is the reference for the remaining buildings.
The current review images live in `build/assets/elves/review/`; older `_group_*.jpg` and
`_elves_poster*.jpg` files predate this pass and must not be used for approval.

- [Review gallery](../../build/assets/elves/review/index.html): each building, close-ups and valid animation previews.
- [Full faction poster](../../build/assets/elves/review/poster.jpg).
- Group comparisons: [citadel additions](../../build/assets/elves/review/citadel-additions.jpg),
  [expansions](../../build/assets/elves/review/expansions.jpg),
  [walls](../../build/assets/elves/review/walls.jpg),
  [production](../../build/assets/elves/review/production.jpg),
  [special buildings](../../build/assets/elves/review/specials.jpg).

## Design

EA's detailed bodies, carved windows, statues, doors, foliage and water are retained. Additions
use soft ivory, mithril silver and mallorn gold, with slate roofs and teal lattice glass.
The gold leaf crowns, spire tips, lanterns and narrow trim follow the approved citadel.
Wall pieces have no banners except the gate; fortress upgrades add at most one each.
The Ent moot keeps natural stone and vegetation, without metal or flags.
The fence is a chained addition to the completed Green Pasture; its comparison starts from
that redesigned pasture, rather than showing the palette and main-body work a second time.

## Completion and evidence

The interrupted recipes were rebuilt with the final shared palette and house-colour models.
Open added surfaces were closed before lifecycle fitting. Hub collapse uses the original rest
pose; the floodgate's construction fit distinguishes internal break faces from exterior walls.
The doors apply their model-space offset only during matching, preserving the original animation.
The W3D transfer keeps required colour and UV channels, discarding only optional source colour
channels absent from the destination format. Required missing channels still reject the transfer.

Each building's README and `build/assets/elves/<building>/work/lifecycle.json` record which
states use the redesign, a derived model, or the original EA body. A passing build does not
mean every original state was replaced. No lifecycle gate was weakened or forced through.
Final check results and offline asset costs are recorded in [PERFORMANCE.md](../../docs/PERFORMANCE.md).

The following states intentionally keep EA's body:

| Building | States | Reason |
|---|---|---|
| Barracks | Heavy damage, rubble | EA's broken pieces do not match the redesigned body |
| Forge | Damage, heavy damage, rubble | EA's broken pieces do not match the redesigned body |
| Crystal moat | Damage, heavy damage, rubble | No matching body pieces for transfer |
| Mallorn tree | Heavy damage | The destination requires original vertex colours missing from the source mesh |
| Mirror of Galadriel | Damage, heavy damage, rubble | No matching body pieces for transfer |
| Statue | Construction | Probed fits still exposed new backs during construction; the unchanged gate rejected them |

The fortress wall hub shares the regular wall hub's completed construction model. This is a
shared output, not an omitted state. House-colour cloth is hidden wherever its redesigned
support is absent, so original fallback states do not acquire floating banners.

## Review and installation

The player reviewed the rollout and requested installation on 2026-09-26. The Elven building
pack and selectable builder are installed, alongside the existing Dwarven buildings and builder.
The Dwarven builder's missing player-colour mapping was repaired without changing its reviewed
model or diffuse textures. No game session was launched; runtime review remains with the player.

`python3 -m sagekit install elves --check` stages the archive and verifies its cache edits against
the current installed caches, preserving unrelated records (including duplicate records).
After review, `python3 -m sagekit install elves` applies the staged build with scoped backups.
`python3 -m sagekit install elves --revert` restores that installation only if its files still
match the receipt; later shared-cache edits make it refuse an unsafe revert.
The combined install order was Elven buildings, Elven builder, then Dwarven player-colour repair.
Undo in reverse order if needed, so each shared-cache snapshot matches before restoration.

Blender previews do not reproduce all game effects. In particular, the wall gate's unchanged
torch cards appear as dark rectangles on both sides of its comparison. Mallorn and pasture
leaves have opaque card backgrounds in some lifecycle previews on both sides; their healthy
previews preserve alpha. The enchanted anvil's
extreme collapse coordinates are present in EA's source animation and are retained. Added
lanterns on models without EA night meshes are decorative; this pass does not add new night
draw modules. Runtime appearance and performance still need the player's reviewed play session.
