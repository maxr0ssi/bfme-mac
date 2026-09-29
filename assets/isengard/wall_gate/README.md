# Isengard wall gate (`IsengardCastleWallGate`)

Model `IBWallGateN_SKN`, mesh `IBGATE` (the pylons; identity bone), own texture `IBFortresE.tga`.
Palette A. EA's pylons are kept whole and the door leaves `IBGATEDOOR01`/`02` stay EA's.

## Pass 1 (shape preview)

- **Two tridents**: a blade tower out of each pylon's top between the fork plate's horns
  (lozenge along the pylon, flared foot, set-back steps, three layered fins a face, silver edges,
  ember slits, a collar) to a needle at z 90; silver along the horns' outer edges.
- **Fire**: four fire baskets on iron brackets out of the pylons' field faces beside the gateway
  (z 50.5), the gate's real fire (`fire_points`, four 'brazier').
- Pointed ember slits low on each pylon end, iron spikes along its top edge.
- **Banners**: one a face, on iron frames with the White Hand, the cloth in the player's colour
  (the +y pylon's +x end, the -y pylon's -x end): the wall run's banners hang here.
- **Pass 3**: the White Hand in a pointed-arch slot (silver frame, black panel) on each pylon end
  without a banner (z 22..42, leaning back with the end), so each face shows a banner and a
  Hand; the blade towers' collars lifted to 0.62 of their height, clear of the fins (they read
  as white crosses), the slits under them.

200 -> 2,814 triangles (the leaves' 1,424 unchanged), height 76.9 -> 90.0 (+17.1 %), footprint
unchanged, 9/9 preview checks. Real fire shows only in game (the preview has no particles).

## Kept clear

- The door leaves fall outward about their feet to lie flat at |x| <= 45.1 when open
  (`IBWallGateN_OPN`): nothing new enters |y| < 48.3 at any height.
- The segments meet the pylons' outer faces (|y| 59.19); the banner frames stop at |y| 59.1.

## Status

- [x] healthy body designed (pass 3, shape preview; sheet `_review/walls_v3.jpg`)
- [ ] reviewed, built in colour, installed
