# Isengard citadel (`IsengardFortressCitadel`, `IsengardFortress`)

Model `IBFortress`, mesh `IBFORTRESS`, own texture `IBFortresH.tga` (from `IBFortress.tga`).
`Tier.HERO`. Palette A "Orthanc black and silver" ([`style.py`](../style.py)); new pieces come from
the Isengard kit ([`shapes.py`](../shapes.py), [`shapes_works.py`](../shapes_works.py),
[`shapes_yard.py`](../shapes_yard.py)). EA's body is kept whole.

## Pass 6

Pass 4 was a block, pass 5 a bundle of thin sticks that lost the silhouette. Pass 6 keeps pass
5's language with fewer, wider blades:

- **Foundry** (`foundry.py`): three lozenge blades round EA's back tower (whole and in sight,
  the orcfire cauldron on it). B0, the dominant one, along the +Y wall, broad face to the
  courtyard and the camera, to z 120, right of EA's tower in the RTS view (placed behind the
  tower point first, it hid all but its needle); B1 on the -X wall's foot to z 84, left of it; B3
  clasping the tower's courtyard corner from a corbel at z 24 (over the excavations upgrade) to
  z 84, with the White Hand in a pointed-arch slot and the crane boom. Each: a flared, spurred
  foot, two set-back steps, three layered fins on every face (a tall deep one between two short
  shallow ones), silver edges, ember slits, a needle tip. The great chimney out of EA's tower's
  point (z 108).
- **Chimneys**: lozenge stacks, wider at the foot, a set-back step, tapering to the blade crowns.

No upgrade's vertex lies inside the new solids and nothing enters the orcfire fire cards' box.
3,876 -> 14,107 triangles (budget 15,000), height 91.4 -> 120 (+31.3 %), footprint unchanged,
9/9 preview checks. Review sheet: `build/assets/isengard/_review/citadel.jpg` (passes 4-6 side by
side at the RTS view on top; earlier sheets `citadel_v1.jpg` .. `citadel_v5.jpg`).

### Pass 6b: fire and small details (colour build)

Max on pass 6's colour build: "needs more little details, I like flames and embers". Palette A
reads as Isengard.

- **Fire**: flame tongues (the "flame" tag, painted near-white orange so they read by day) out of
  every chimney's widened throat, from braziers on every walk, the forges' hearths, the fire
  grates and the crucibles; the chimneys' collars an ember band; brighter embers everywhere; a
  furnace mouth in B0's foot at the +Y walk, a runnel to the walk's edge and molten metal pouring
  down the wall's inner face into a glowing pool; molten runnels on both walks from the side
  stacks to the forge and the gantry's grate (`shapes_fire.py`).
- **Real flicker** (EA's fire cards and particle systems on bones) needs bones of our own and
  `ParticleSysBone` lines the pipeline does not write yet: a framework item, not done.
- **The White Hand**: large in a pointed-arch slot on B0's broad face (z 72..98, above the crane),
  on a shield over the gate, on B3's slot and the shields in the rack.
- **Details**: a slag cart, stacked ingots with a glowing top row, anvils with white-hot work, a
  bellows at the forge, a pike rack, ember lanterns on posts along the walks.
- The -Y chimney no longer reads as a white ladder: its edge fins are black, silver only on the rim.
- Traded for them: the frame saw, one shield rack, the winch, the blade rails, a log row, a
  lip spike per face, two water-wheel paddles.

3,876 -> 14,746 triangles (budget 15,000), height +31.3 %, 9/9 preview checks, no upgrade's vertex
inside the new solids. Colour renders: `build/assets/isengard/fortress/renders/compare_*.png`.

After that build: the side chimneys still read silver-white (new "iron" faces sample a bright
plate the recolour turns silver: fixed with an "iron" TagRamp, dark iron) and the flames were
thin (tongues made fatter). Both need the next colour build to show.

### Pass 7: a matching pair, embers, fire points (colour build)

Max on build 2: "whatever you put on either side of that triangle, so have 2".

- **The pair** (`foundry.py`): two matching blades, BL and BR, flank EA's back tower (the triangle
  in the middle of the RTS view), mirrored about the tower's axis in that view, to z 120, a
  White Hand in a pointed-arch slot on each one's outer face; the great chimney on the axis
  between them, the side chimneys a pair beyond. Pass 6's single wide blade mirrored would have
  stood inside the burning forges, so the pair is narrower and both sit clear.
- **Embers**: wider ember slits on the blades; ember throats, collars, runnels, the molten fall
  (now ember, not flame) and glowing work.
- **Painted flame cones are off** (`FireKit.PAINTED_FLAMES`: they read as pale plastic). Every
  fire records its point instead: `Fortress.fire_points`, 20 (x, y, z, kind) points (chimney,
  furnace, hearth, crucible, brazier, grate) for the real-fire job (particle systems on bones).

### Tweak options (shape previews, 2026-09-30)

After pass 4 took the needle stacks off the other buildings, the citadel's three (the great chimney
up the foundry point between the pair, the two side stacks) are its weakest pieces. `tweaks.py`
holds three options, `ISENGARD_CITADEL=A|B|C python3 -m sagekit preview isengard/fortress`
(unset: the installed design, unchanged). A: all three out, smelting hearths where the side stacks
stood, a crucible on the -Y walk (14,149 triangles). B: A with one heavy smelter stack on the +Y
walk (14,701). C: A with Orthanc's horns, the wall hubs' crown A, on the three corner towers in
place of their spikes (14,713). 20 fire points each. Sheet: `_review/citadel_tweaks_v1.jpg`.
Max on v1: "get rid of the stupid tower", the tall pair. D: C without the pair and its Hands
(12,203, 20 fire); D2: D with the hubs' horned crown and a fire-pot on EA's tower point, peak z 109
(13,285, 21 fire). Sheet: `_review/citadel_tweaks_v2.jpg`.

## Kept clear

- The courtyard: the upgrades stand there (the wizard's tower `IBFWTower` at the centre to
  z 175.7, the excavations, the burning forges over the -X wall, orcfire munitions on the walls).
- The orcfire munitions upgrade: a cauldron on each tower top ((+-37.4, +-37.7), z 80.2..93.7,
  fire to z 110). Pass 1's stack on the -X -Y tower stood in it; pass 2 moved it.
- The gate opening (x > 73, |y| < 11, z < 43).

## Status

- [x] palette chosen (A, with silver)
- [x] healthy body designed (pass 6, shape preview)
- [x] built (pass 6b, colour renders)
- [ ] reviewed, installed
