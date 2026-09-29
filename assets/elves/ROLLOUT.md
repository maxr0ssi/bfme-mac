# Elven rollout

**Status: installed.** 23 recipes and the selectable builder ([porter](porter/README.md)),
277.3 of 512 MB. The citadel ([fortress](fortress/README.md)) is the reference for the rest.
The loop is in [docs/FACTIONS-PLAN.md](../../docs/FACTIONS-PLAN.md).

Review images (in `build/`, not in git; each player builds their own):
`build/assets/elves/review/index.html` (each building, close-ups, animation previews),
`poster.jpg`, and the group comparisons `citadel-additions.jpg`, `expansions.jpg`, `walls.jpg`,
`production.jpg`, `specials.jpg` in the same folder.

## Design

EA's detailed bodies, carved windows, statues, doors, foliage and water are kept. Additions use
soft ivory, mithril silver and mallorn gold, with slate roofs and EA's teal lattice glass. The gold
leaf crowns, spire tips, lanterns and narrow trim follow the citadel. Wall pieces have no banners
except the gate; fortress upgrades add at most one each. The Ent moot keeps natural stone and
vegetation, without metal or flags. The fence is chained on the redesigned Green Pasture.

## Shared by every Elven building

Said once here, not in each README:

- The palette is [`style.py`](style.py)'s. No face of EA's healthy body is removed.
- Build output is in `build/assets/elves/<building>/`: `work/lifecycle.json` says which models are
  rebuilt, derived or left to EA; `work/logs/checks.log` has the checks;
  `renders/compare_*.png` and `renders/lifecycle/*.png` are the before/after images.
- Night lights: only the barracks, battle tower, forge, green pasture, fence and mallorn have EA
  night meshes, and ours replace them. Elsewhere EA has no `NightWindowName`, and the new crystals
  and lanterns are day-lit.
- House-colour cloth is hidden wherever its support is absent, so states left to EA get no
  floating banners.

## States that keep EA's body

| Building | States | Reason |
|---|---|---|
| Barracks | Really damaged, rubble | No body pieces of ours to transfer |
| Forge | Damaged, really damaged, rubble | No body pieces of ours to transfer |
| Crystal moat | Damaged, really damaged, rubble | No body pieces of ours to transfer |
| Mallorn tree | Really damaged | EA's piece carries per-vertex data ours lacks |
| Mirror of Galadriel | Damaged, really damaged, rubble | No body pieces of ours to transfer |
| Statue | Construction | Our holder shows open backs while it rises |

The fortress wall hub uses the wall hub's construction model (`EBWallRmprtN_A`, shipped by
`wall_hub`).

## Install

`python3 -m sagekit install elves --check` stages the archive and checks its cache edits against
the installed caches. Without `--check` it installs with scoped backups; `--revert` restores them,
and refuses if a later install changed a shared file. The Elven buildings, the Elven builder and
the Dwarven builder's player-colour fix went in in that order: revert in reverse order.

## Known limits

- The barracks and the mallorn ship own copies of their models; these render invisible in game
  (a known bug, being fixed).
- Blender previews differ from the game: the wall gate's torch cards show as dark rectangles, and
  mallorn and pasture leaves show opaque card backgrounds in some lifecycle previews (EA's and ours).
- EA's enchanted anvil collapse animation throws pieces far off-scene; kept as EA made it.
