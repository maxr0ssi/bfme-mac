# Elven battle tower (`ElvenBattleTower`, `elvenbattletower.ini`)

Model `EBBbattleTwr`, redesigned mesh `EBBBATTLETWR`, painted from its own sheet `EBBbattleTwr.tga` (+
`_NRM`); our texture is `EBBbattleTwH.tga` (+ `_NRM`, `_D1`, `_Snow`). New faces are mapped onto the
faction atlas. `Tier.STANDARD`.

## The original (measured, `EBBBATTLETWR` coordinates, one upright bone)

- **Foot:** a battered stone octagon round (-0.645, 1.49). Its axis faces lean in 0.17 from an
  apothem of 18.8 at the ground to 13.7 at its top edge (z 32.9), with short chamfers on the
  diagonals. The +x face holds the porch: a pointed door under a scale hood and the ramp down to x 46.
- **Shaft:** square, faces 10.8 from the centre, tall lattice windows from z 33 to 78, white
  corner piers on the diagonals.
- **Head:** z 80.8..103.3, four pointed gables on the axes with horns out to 25.6 at z 109.2 round a
  bulging fish-scale cupola (tip z 131.55). The archer bones (3..14) are in the gables' windows at
  z 88.5-93.3.
- The mesh also holds five tiny markers 55 units out on the axes: they set the footprint
  (x -57.8..46.2, y -55.7..58.7).

## What changed (body, healthy)

- **Spire:** the cupola is now the foot of a tall Elven spire. It is a concave octagonal slate
  needle (the style's `Scales` layer: continuous fish-scale slate) with swan-neck eaves and a gilt
  lip. It rises from inside the ring of gables to z 144, with a sea-green collar between gilt beads
  a third of the way up. At the top, a gilt collar, a gilt mast and a leaf finial reach z 153.4. The
  spire contains the old cupola at every height (radius 18.5 at the eaves against the cupola's 15.4).
  The gables and their horns stay in front of it; nothing is added in the head below z 103.
- **Pennant:** a long leaf pennant flies from the mast across the RTS camera's view. Its cloth goes
  to `EBHCBbattleTwr` (house colour).
- **Foot:** a moulded silver coping on the stone's top edge, and a knotwork band between gilt beads
  at z 27.4-28.8. Both run round the three plain faces and stop at the porch.
- **Lanterns:** a crystal lantern on a gilt swan-neck bracket at each end of the -y and -x faces
  of the foot.

Footprint unchanged. Height 131.25 -> 153.10 (+16.6 %, limit 20 %). Triangles 2,631 -> 4,487.
Texel density median 7.3 px/unit. `checks`: 111/111.

## Night

`night_lights`: the three lattice windows the camera sees on the shaft (+y, -x, -y, z 36-74), the
+x shaft face above the porch hood (z 48-74), and the porch door. All are cast in the Elven
starlight (`EBStarlight.tga`); see `renders/night/`. EA's `N_WINDOW` / `N_GLOW` carry them.

## Snow tower

`ElvenBattleTowerSnow` (an `ObjectReskin`, map-placed) draws `EBBbattleTwrS`. That is EA's same body
on the snow sheet, with no normal map. It is not in the model family the pipeline finds
(`EBBbattleTwr_*`), so `drawn_models` adds it. It is then derived like the damaged state: our body,
our `EBBbattleTwH_Snow.tga`. See `renders/compare_ebbbattletwrs_*.png`.

## Status

| Part | Healthy | Construction | Damaged | Really damaged / rubble | Snow | LOD M/L |
|---|---|---|---|---|---|---|
| body (`EBBbattleTwr`) | built, checks pass, **awaiting review** | built (`EBBattleT_A`, lifecycle) | derived (`EBBbtlTwr_D1`) | built (`EBBbtlTwr_D2`, `_D3`, lifecycle) | derived (`EBBbattleTwrS`) + `_Snow` sheet | old |
| banner (`EBHCBbattleTwr`) | the pennant's cloth added (shown after `sagekit house elves`) | | | | | |

## Notes

- EA's porch lanterns (`EBBBATTLETWRLE`, untouched) are painted by day from Gondor's
  `gbnightwindows`. The night-lights check allows no shipped mesh to draw another faction's night
  sheet. The Elven style now declares its own recoloured copy, `shared_sheets =
  {"GBNightWindows.tga": "EBLanternPanes.tga"}`, at 512 (the 4x upscale of EA's 128 sheet).
- The lattice glass is recoloured sea-green (EA's pale blue) by the palette's enamel.
