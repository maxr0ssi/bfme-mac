# Men wall tower (`MenWallTowerSmall`, `ArnorWallTowerSmall`)

Model `GBWallTwrN`, mesh `GBFARTOWA` (238 triangles; not the arrow tower's mesh of that name).
Own texture `GBFortressX.tga` from `GBFortress1.tga`.

## Design (2026-09-27)

EA's tower kept whole (shaft, corner buttresses, the carved emblem on the field faces, the belfry
with its painted windows, the slate dome), crowned from [`../wall_hub/dome.py`](../wall_hub/dome.py):

- the citadel's machicolated gallery round the shaft top (band of silver stars, merlons);
- four corbelled bartizans on the diagonals over EA's buttresses;
- a parapet of merlons round the belfry's top; steel eave band and ribs on the dome, a lantern
  cupola (its collar wraps EA's dome point), a steel mast, gilt orb and spike;
- one house-colour banner from the gallery on the +x face, ending above EA's emblem (z 40.2).

Footprint EA's; height 93.62 -> 110.5 (+18.0 %).

## Open

- BOX01, EA's wall stub under the tower, stays EA's (a chained recipe could carry wall.py's
  crown through it).
- The Men style has no `house_template`: the banner's cloth stays in the body in the preview navy
  until the integration pass gives the walls a house-colour model.

## Status

- [x] healthy body designed; checks pass; renders in `build/assets/men/wall_tower/renders/`
- [ ] Max's review
