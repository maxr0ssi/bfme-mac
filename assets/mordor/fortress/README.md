# Mordor citadel (`MordorFortressCitadel`, `MordorFortress`)

Model `MBFortress`, mesh `MBFORTRESS`, own texture `MBFortresH.tga` (from `MBFortress.tga`).
`Tier.HERO`. Palette F2 "Fire, shadow and steel" (Max's pick). New pieces come from the Mordor
kit ([`shapes.py`](../shapes.py), [`shapes_horn.py`](../shapes_horn.py),
[`shapes_lava.py`](../shapes_lava.py), [`shapes_story.py`](../shapes_story.py)). EA's body is
kept whole. EA's facts are in [`building.py`](building.py).

## Pass 7: a claw round the witch-fire

Max on pass 6 in game: "i like the idea but i don't like the execution, we should drastically
reduce the green -- green fire would be kinda cool. but what we should do is that the tower but
invert it i.e. put the spikes and flames inside, rather than outside and then much smaller".

- **Crowns** ([`crown.py`](crown.py)): the big outer horn-blades and their collars are gone, on
  all four towers and over the gate. Inside each crown, eight jagged spikes rise from the crown's
  walk (z 121, r 7.5) and lean in round the fire, like a claw closing on it from within. Four are
  tall, with a steel outer edge, teeth hooking up, a hook down and a lava seam; four short ones
  stand between them. The corner crowns' tips reach z 147 (7 over EA's crown). The back tower's are
  a little heavier and reach z 150.
- **Green, drastically less**: F2's windows are unlit now, a dim ember deep in them
  (`EMBER_WINDOW`, [`../style.py`](../style.py)): EA's crown windows, the keep's slots and our
  flute lancets. The Morgul green stays on one lancet pair per tower, the pair facing the camera,
  the same on all four (tag `witch`, painted by the style's TagRamp). Max asked "why only green on
  one?" when only the back tower had it.
- **Green fire**: every crown burns `witchfire`, our `SagekitWitchFire` (EA's furnaceFire, its
  Color keyframes in Morgul green) and `SagekitWitchSmoke` (EA's SmokeChimney, twice as broad: a
  modest dark plume). They sit just over the crown's parapet (z 134.5). The back crown adds a
  second green flame (`witchflame`, z 138). EA has no green fire that burns in place, so both
  systems are ours, made at build time from EA's file and added to it
  ([`sagekit/fire_systems.py`](../../../sagekit/fire_systems.py)). The pass 6 fireballs
  (FireBuildingLarge over the tips) are gone. The lava, the forge and the fire baskets stay
  orange (EA's systems). The flue keeps a small orange `chimney` fire and EA's heavy dark plume
  on its own (`plume`).
- **EA's pyres and flame cards** (MBFDPYRES, MBFDPF, MBFDPFG): the game hides all three until the
  Doom Pyres upgrade (EA's SubObjectsUpgrade), so before it the crowns show only our spikes and
  the green fire. After the upgrade, EA's orange flame cards burn over the green fire as the
  upgrade's sign. We keep them: hiding them would take the upgrade's look away, and
  recolouring them needs a texture of our own. The renders leave all three out (`bake_hidden`) to
  show the crowns as they stand before the upgrade.

4,882 -> 14,914 triangles (budget 15,000). Height 140.2 -> 150.0 (+7.0 %; pass 6 +24.1 %,
`max_z_growth` 0.08). Footprint unchanged. 9/9 preview checks, 121/121 build checks. 19 fire
points, 29 particle systems in each state that shows our body (default, DAMAGED, SNOW).

Review sheets: `build/assets/mordor/_review/citadel_v1.jpg` .. `citadel_v7.jpg`. v1..v3 had one
crown on the back tower, v4 and v5 covered every crown (they read as barrels), v6 had the outer
horn-blades (installed, seen in game) and v7 has the inner claws, in colour.

## Kept clear

- The Gorgoroth spire (|x| < 19.15, |y| < 23.3, the courtyard's middle, to z 174.7).
- The magma cauldrons: the -X walk (y < 22 there), the base up the -X inner face (|y| < 8.9),
  and the spouts on the outer faces (z 25..37). The -X chain stays above z 112.
- The fire arrows over the gatehouse (x 32.6..51.6), both doors, the ramp and EA's box
  (y +-57.26, x from -56.51).
- EA's crowns (r 13, spike heads to z 139.6) and the flame cards: two crossed planes on each
  tower's axes (+-14.2, z 139.8..168) and a glow plane (z 132.8..163.2). The spikes stand at
  22.5 + 45k degrees, between the planes, and never cross one. They do rise through EA's pyre
  sticks (r < 10.5, shown only after the Doom Pyres upgrade), out of the pyre as asked.

## Open

- How the green witch-fire and its smoke read in game (size, brightness by day, the particle
  cost of 29 systems) is checked in play. The fire is EA's furnaceFire in size; the colour is
  one line in `sagekit/fire_systems.py`.
- `rts` and `close` are EA's views with the target raised (to z 80 and 96).
- No new player-colour cloth. EA's banner (MBHCFortress) stays.

## Status

- [x] healthy body designed (pass 7)
- [x] built in F2 (121/121 checks), reviewed on `citadel_v7.jpg`
- [ ] Max's review, then installed
