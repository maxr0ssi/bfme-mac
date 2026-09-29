# Men citadel (`MenFortressCitadel`)

Model `GBFortress`, mesh `GBFORTRESS`, own texture `GBFortressH.tga` (from `GBFortress1.tga`).
`Tier.HERO`. Ships as `GBFortress2`: Arnor and the neutral fortress stay on EA's model.
EA's body kept whole; new silhouette from `MenShapes` (`assets/men/shapes.py`) and `assets/men/paint.py`.

## What changed

- **Tower crowns** (`crown.py`): a machicolated gallery round each shaft top (two-step corbels,
  parapet, square merlons with capstones), its front a black band of silver seven-pointed stars;
  four corbelled bartizans with slit windows and slate spirelets; pilasters up the chamfers.
- **Domes**: steel eave band, twelve steel ribs, a lantern cupola, a steel mast, gilt orb and
  spike to z 129.
- **Walls**: crenellated parapets on the side and back walls, a string course, pinnacles over
  EA's buttresses.
- **Gatehouse** (`gate.py`): pilasters, eleven voussoirs and a keystone, portcullis teeth, a black
  frieze with the seven gilt stars, a slate-roofed pediment with the White Tree, a winged-helm
  crest and corner pinnacles.
- **Paint** (`style.py`): bright limestone, charcoal slate, bright steel, sable enamel, muted old gold.
- **Banners**: four on the front towers, under the flame hardware; cloth in `GBHCFortress2` (an own
  copy: Arnor draws `GBHCFortress` too). Steel-framed White Tree shields on the back towers.

## Kept clear

- The doors' sweep: x 50.5..67, |y| < 15.45, z < 41.
- The oil outlets, the flame hardware and the banner upgrade's pennants (z 105..112 at the poles).
- The front towers' galleries stop at x 44.3 on the face toward the healing house.

## Status

Installed with the Men pack. 1,458 -> 14,853 triangles (budget 15,000), height 116.65 -> 129.0
(+10.6 %), footprint unchanged, 109/109 checks. Construction, really damaged and rubble are
rebuilt along EA's pieces. No night meshes (EA has none).
Add-ons: [`fortress_ivory_tower`](../fortress_ivory_tower/README.md),
[`fortress_house_of_healing`](../fortress_house_of_healing/README.md),
[`fortress_oil`](../fortress_oil/README.md), [`fortress_oil_guy`](../fortress_oil_guy/README.md).

## Known limits

- Renders invisible in game (own-copy bug, being fixed).
- The gate pediment stands in front of the healing house's lower arcade when that upgrade is built.
