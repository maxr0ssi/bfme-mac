# Mordor Haradrim palace (`MordorHaradrimPalace`)

Model `MBHrdPlc_SKN`, mesh `MBHRDPLC`, own texture `MBHrdPlH.tga` (from `MBHrdPlc.tga`); new faces
map to the faction's master sheet. EA's great cross-shaped tent is kept whole. EA's facts are in
[`building.py`](building.py), the design in [`palace.py`](palace.py), the group's pieces in
[`../shapes_harad.py`](../shapes_harad.py).

## Pass 2: a crown of tusks and grounded claws

Max approved the Harad twist ("cool like it go for it"). The palace keeps Mordor's F2 base of black
basalt, orange fire and steel on the points. It adds ivory tusks (`bone`), brass (`brass`), war-paint
red (`warpaint`) and sun-and-serpent banners in the player's colour. Pass 1's four claws on thin
piers read as lanterns at rts; pass 2 grounds them and gives the tent a crown.

- **Crown** (the family motif, the new silhouette): a stepped basalt plinth sits round the tent's
  peak with a great fire bowl on it. It burns orange (`furnace`) under EA's heavy dark plume
  (`plume`). Eight big ivory tusks rise from the roof round it (r 19), with brass bands and steel
  points, bowing in over the fire (tips z 64).
- **Claws**: one on the ground either side of the -Y door. Each is a stepped basalt plinth with a
  fire bowl (`furnace`, `smoke`) and six ivory tusks bowing out and turning in over it. The +Y door
  has no room inside the footprint.
- **Suns**: the Harad sun in brass on war-paint red plates under both X gable ends (11 across) and
  over the -Y door (10 across).
- **Banners**: two banners in the player's colour, 8 by 16, hang from the X arm's -Y eave. Each
  carries the sun and serpent in brass.
- **Bonfire**: EA's bonfire gets real fire (`hearth`). Its flame card `FIRE` stays in game and is
  left out of our bakes.

1,106 -> 5,797 triangles. Height 51.0 -> 72.5 (+42.1 %, `max_z_growth` 0.45; EA's own level 3
tower reaches z 79). Footprint unchanged. 9/9 preview checks. 7 fire points. Review sheet:
`build/assets/mordor/_review/harad_v2.jpg` (v1: pass 1).

## Levels

The game hides `V1` (the tusk ring, level 2), `V2A` (the tower on the peak, level 3), the banner and
the lancer until the upgrades (EA's `SubObjectsUpgrade`s). `bake_hidden` leaves them out of the
bakes and the renders, so the review shows the palace as built. The sheet also has an rts row with
them shown.

## Kept clear

- `V1`: arcs rooted in the inner corners, over the X ends (x +-30..36) and off the Y ends.
- `V2A`: its floor at z 53..54 over x -15..9, |y| < 12, walls to z 67, posts at (-18, +-16) and
  (10, +-16). The crown's tusks stand between the posts and at least 1.5 from the walls, so at
  level 3 they close round EA's tower.
- EA's bonfire, the house banner's pole (17.2, -19.7), `BANNER_HARAD01`, the lancer, the arrow bones.

## Open

- At level 3, `V2A`'s floor sits just over the crown's fire bowl (rim z 52.6). The fire burns up
  into EA's howdah tower. How that reads is checked in game.

## Status

- [x] healthy body designed (shape preview, pass 2)
- [ ] Max's review of `harad_v2.jpg`, then build, colour, install
