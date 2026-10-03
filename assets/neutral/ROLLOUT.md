# Neutral: the capturable buildings and lairs

`neutral` is a pseudo-faction (sagekit/taxonomy.py `OWNERS`): EA's buildings nobody owns at the
start, which a player takes with the capture flag beside them, and the creep lairs. They are in
nearly every match: the capture flag on 232 multiplayer maps, the signal fire on 155, the Inn on
128, the Outpost on 86, the creep lairs on 240 of 259.

- Style: `style.py`, "Wilderland": EA's own colours graded for contrast (`paint.py` Grade), the Inn's
  sheet `NBInn` as the master for new faces (`atlas.py`), the kit in `shapes.py`, the lairs' story
  pieces in `lairs.py` (the Goblin kit's bones and skulls, retagged).
- Ownership: `sagekit owners neutral` counts `data\ini\object\neutral` as neutral's; the seven
  factions never see neutral as another owner (their builds are unchanged), and a neutral recipe may
  not change a faction's art (GBGenRubble, the generic rubble pile, is a lifecycle `skip`).
- Archive: `sagekit install neutral` builds `!!!!!!!!!!!sagekit-neutral.big`; the release packs it
  with `scripts/make-release.sh --buildings neutral` (not in the default list until checked in game).
- Capture dress (sagekit/capture.py): a recipe that is `Capturable` gives `body(kit)` and
  `dress(kit)`; `dress.py` builds every faction's banners and ridge crowns at the spots the recipe
  names, from that faction's own kit, in its ramps. No fire in a dress: a fire Draw can only follow a
  model condition, and an upgrade sets one for good, so the fire would outlive its holder.
- Review: `python3 -m sagekit capture neutral/<name>` -> `build/assets/neutral/_review/<name>_v1.jpg`
  (all seven holders at the RTS camera and close; a lair: EA's against ours).

## State

| Recipe | EA model | Ours | Dress |
|---|---|---|---|
| inn | NBInn_SKN | three-flue chimney, sign gallows, awning, stable lean-to, yard hearth (fire) | banners on the hall and gatehouse, crowns on two ridges, Goblin porch fence |
| signal_fire | NBSigFire | firewood stacks at the foot, a roofed warden's lookout | banners on the lookout, crowns round the column's foot |
| outpost | NBOutpost_SKN | two market stalls under madder canopies, barrels | banners on the east gable and the watchtower, crowns on two ridges, porch fence |
| ship_wright | NBShipWrt_SKN | a ship in frame on the slipway | banners on the crane tower and the shed's side, crown on the ridge |
| ruined_tower | RuinTwr | the broken top left open; a squatters' camp on the old floor (fire ring and cookpot, barrels, a fallen roof beam, a lantern pole) | none: it changes hands by garrison and goes back when emptied, and an upgrade cannot be undone; EA's house-colour banner shows who is inside |
| cave_troll_lair | NBTrollLair | the troll's larder, a spiked club, a skull on a stake | (a lair) |
| warg_lair | NBWargLair | a gnawed kill on the mound, another at the foot, warg skulls on stakes | |
| moriar_goblin_lair | NBGoblinLair | a war totem crowning the rock, skulls on spikes, a skull heap | |
| spider_lair | NBSpiderL_SKN | two great webs, cocoons, egg sacs | |
| barrow_wight_lair | NBWightLair | an avenue of standing stones to the door, the grave goods spilled | |
| fire_drake_lair | NBDrakeLair | the hoard: gold, a chest, a sword, a shield, bones; its own sheet in every state (EA's healthy WBStone and Goblin-recoloured WBStone_D1 clashed) | |

EA's own capture hooks, read: the Inn and the shipwright swap command sets per faction upgrade; the
shipwright shows GoodPart_A/B or EvilPart_A/B (no model has those meshes: nothing shows); the capture
flag shows its holder by Lua (scripts.lua OnCaptureFlagGenericEvent hides every FLAG_<FACTION>
sub-object and shows the capturer's), each flag painted with that faction's emblem on
All_Faction_Banners (only the flag draws it). The flag already reads per holder; restyling its
emblems in our palettes is a texture repaint for later, not a model change.

Not covered: the signal fire and outpost carry no ProductionUpdate (EA's Inn and shipwright do); the
faction upgrades are player upgrades, which should reach them on capture all the same: checked in game.
