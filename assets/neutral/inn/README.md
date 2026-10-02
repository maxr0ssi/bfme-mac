# Neutral inn (`Inn`, `InnSecond`)

The pilot of the neutral pseudo-faction (`assets/neutral/`) and of the capture dress
([sagekit/capture.py](../../../sagekit/capture.py)).

- Source model `NBInn_SKN`, target mesh `NBINN` (1,880 triangles), sheet `NBInn.tga` -> own `NBInH.tga`
  (STANDARD tier). EA's body is kept whole (no `clear`); the townsfolk, their skeleton and animation
  and the well's water stay EA's.
- EA's generic rubble pile `GBGenRubble` (after the collapse; six factions' camp keeps draw it) is a
  lifecycle `skip`: none of our body is in it.

## Design

A wayside inn told at the RTS camera, on EA's own sheet and colours (graded, not recoloured):

- a great fieldstone chimney through the hall's roof, smoking (`fire_points`: `smoke`);
- a sign gallows at the yard's mouth carrying EA's own painted wolf's-head board, 12 by 9, with a lamp;
- a faded madder awning on brackets over the gate;
- a shingled stable lean-to with stalls and a hay rack against the stable wing's podium;
- an open hearth in the yard with a spit and a kettle, burning (`hearth`), and barrels by the hall.

The yard's middle (x -2..14) stays clear: units leave the gate at (5.9, 20.1) for the rally point (-0.1, -80).

## Capture dress

Nothing of it shows while the inn is neutral. When a player captures it, its faction's dress appears
(`CAP_<P>` in the body, `HC_CAP_<P>` in the house-colour model `NBHCInn_SKN`, tinted in the
capturer's colour), every other faction's is hidden:

| Faction | Banner on the hall's gable | Crest over the gate | Finial on the sign post |
|---|---|---|---|
| Dwarves | rune-banded banner, bronze rod | stepped rune lintel, gold hex bosses | gold step pyramid |
| Elves | leaf banner and pennant | gilt leaf crest round a crystal | crystal lantern |
| Men (and Arnor) | White Tree banner | White Tree shield between two stars | steel orb and spike |
| Isengard | iron-framed banner, the White Hand | Uruk shield on crossed iron braces | iron spike |
| Mordor | iron-framed banner | the Eye in its slot, iron spikes | barbed stake |
| Goblins | ragged banner, war-paint eye | horned beast skull, crossed bones | skull on a spike |
| Angmar | iron-framed banner, ice on the brackets | frozen iron crown of tines and ice | ice shards |

Review: `python3 -m sagekit capture neutral/inn` -> `build/assets/neutral/_review/inn_v1.jpg`.

## Status

- [x] healthy body designed; damaged (`NBInn_D1`, derived) carries body and dress
- [x] construction, really damaged, collapse, rubble rebuilt along EA's pieces (no dress there)
- [x] checks pass, renders made
- [ ] reviewed by Max; in-game check: the dress appears on capture, follows a recapture, LAN
