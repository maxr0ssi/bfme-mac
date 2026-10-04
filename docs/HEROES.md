# Heroes: the heroes pack

More heroes, and heroes that change as they level. Everything is INI data recombined from EA's own
modules, plus models drawn with the Create-a-Hero kit on EA's rigs. One revertable pack:
`!!!!!!!!!!!sagekit-heroes.big`, and its string table in `lang\`.

```sh
python3 -m assets.heroes.audit [--markdown]       # EA's hidden heroes: what is complete in 2.02
python3 -m assets.heroes.build [--skip-art]       # models, portraits, INI, strings, lint (nothing installed)
python3 -m assets.heroes.render [captain aragorn unlocked roster]   # review sheets
python3 -m sagekit.units.heroes --stage           # both archives into build/assets/heroes/pack/_install/
python3 -m sagekit.units.heroes --install [--dry-run]
python3 -m sagekit.units.heroes --revert  [--dry-run]
```

Review sheets: `build/assets/_review_finish/heroes/` (`captain_of_erebor.jpg`, `aragorn_level8.jpg`,
`heroes_unlocked.jpg`, `roster_and_buttons.jpg`).

## What the pack does

| Hero | Faction | What |
|---|---|---|
| Gamling | Men | EA's `RohanGamling`, finished, on EA's unused detailed model (below). EA left him `Side = Obsolete` with no portrait (commented out), Boromir's voice and button, a placeholder weapon (HwaldarAxe: "line limit in weapon.ini") and no powers. Now: Boromir's sword and tier (1400, 2400 health), the Create-a-Hero captain's voice, our portrait and icons, stances and capture, and Boromir's power modules, which his Draw already animates: Leadership (1), Horn of Helm Hammerhand (3, Boromir's Horn of Gondor), Captain of the Guard (6, Boromir's Captain of Gondor without Boromir's voice line). |
| Damrod | Men | EA's `GondorDamrod` (obsolete.ini) is complete: model, portrait, icon, strings, voice, four powers, ten levels. Rostered as is. |
| Earnur | Men | EA's `GondorEarnur` is complete but for levels (2.02 took him out of Aragorn's) and his recruit text (Boromir's). Now: Aragorn's ten levels copied for him, his own recruit text. |
| Captain of Erebor | Dwarves | New: King Dain's object rewritten (`assets/heroes/captain/hero.py`), on Dain's rig and animations; Gloin's tier (1500, 2700 health, Gloin's axe and levels); the Create-a-Hero dwarf's voice; powers from EA's modules: Leadership (1, Dain's aura), Charge (3, the CaH dwarf's), Toughness (5, the CaH dwarf's), Train Allies (7, the CaH level grant), Summon Royal Guard (10, Dain's, on a power of our own without Dain's voice line). Model: Dain with a blue-steel Erebor helm (rounded faceted skull, ridge crest, gold-runed band in the player's colour, brow guard, nasal, pointed cheek guards, nape guard; `captain/kit.py`, seated on Dain's larger head), matching pauldrons, the CaH Shield of Erebor and war axe. |
| Aragorn | Men | At level 8 (EA's `Upgrade_ObjectLevel8`, which already puts him in his Return-of-the-King costume) the King's armour appears: a `SubObjectsUpgrade` shows `SKAR_KINGSARM` and `SKAR_KINGTRIM` on our copy of his model: EA's own shoulder, chest and forearm triangles lifted off his body along EA's normals, drawn with EA's sheet burnished (his detail kept; the tabard's White Tree becomes a lacquered breastplate), rimmed in fine gold (`gear.surface_plate`, `gear.rim`). |

Men now recruit 10 named heroes (EA's limit is 11 per faction, the hero bar 16), Dwarves 5. The AI
recruits the new heroes after its own, late in a game.

## EA's hidden heroes (2.02)

From `python3 -m assets.heroes.audit`: Gamling, Damrod and Earnur are used (above). Not used:

| Hero | Why not |
|---|---|
| Isildur (`GondorIsildur`) | no portrait, no hero icon mapped, no recruit or revive text, one experience level |
| Tom Bombadil (`TomBombadil`) | the spell-book summon: no recruit or revive text, one level, Side Neutral |
| Orc chieftains (`OrcChief01..05`) | Lurtz's command set, voice, strings and buttons; his powers not carried; no levels; 01 misses 65 animations, 03-05 have no model |
| DwarftHero | a premade Create-a-Hero dwarf for custom maps: no strings, no powers, no levels, portrait texture missing |

Gamling wears EA's unused higher-detail model, `RUGamlingCH_SKN` (929 vertices, `RUGamling_new.tga`
with EA's house-colour mask, on the skeleton his Draw animates), which has no sword or shield: the
pack adds EA's own, the triangles of the old `RUGamling_SKN` on `B_SWORDBONE` and `B_SHIELD`, as one
sub-object on the same bones (`assets/heroes/gamling_model.py`, `SKGamling_SKN`).

## How it works

| Piece | Where |
|---|---|
| EA's data, read from the player's install | `assets/heroes/ea.py` |
| roster, revive slots, hero submenus, AI | `assets/heroes/roster.py` |
| powers: EA's modules copied by tag, our level gates, button copies | `assets/heroes/powers.py` |
| experience levels | `assets/heroes/levels.py` |
| the heroes | `captain/hero.py`, `gamling.py`, `compose.py` (Earnur, Aragorn) |
| composition and lint | `compose.py`, `lint.py` |
| strings | `strings.py` |
| models | `gear.py`, `captain/design.py`, `aragorn/design.py` |
| portraits and icons | `portraits.py`, `imaging.py` (numpy, on Blender's Python) |
| stage, install, revert | `sagekit/units/heroes.py`; `assets/heroes/pack/design.py` (archive, house-colour lines) |

- **Revive slots.** A building that revives heroes lists one `Command_GenericReviveSlotN` per named
  hero, and its hero submenu (`PUSH_VISIBLE_COMMAND_RANGE`) counts them. A roster that grows gets a
  slot in every such set (fortress, monument fortress and its rebuilt state, Helm's Deep, custom
  keep), later slots move up, a submenu two sets share moves once. A set holds at most 33 slots (the
  engine's CommandSet field table names "1".."33", exe 0xc4f5e8).
- **Powers.** A copied module keeps EA's fields; the pack adds an `UnpauseSpecialPowerUpgrade` on
  `Upgrade_ObjectLevelN` and makes sure the hero's levels grant it. Buttons are copies of EA's under
  our names with our tooltips (EA's mention Dain, Boromir and other levels).
- **Models.** Gear is drawn with the Create-a-Hero kit (`assets/cah/kit/geom.py`). The CaH dwarf's
  rig is Dain's (head, spine and shoulder bones stand where Dain's do; `gear.Rig` stores each piece
  in the design rig's bone space and binds it to Dain's bone of the same name), the CaH Men captain's
  rig is Aragorn's, bone for bone. Dain's shield and axe are fitted to Dain's own (centre, face,
  size; head, haft, reach). Every EA mesh the hero keeps is byte for byte EA's; each piece rides one
  bone (checked through an EA animation). Budgets: the Captain 4173 vertices (Dain 2552), Aragorn
  1613 + 1364 at level 8.
- **Player colour.** Dain's red coat is repainted Erebor blue through the Dwarven cloth ramp and
  takes the player's colour, as do the Erebor kit's enamel and Aragorn's White Tree roundels (unit
  house masks; the lines go into the shared `!!!!!!!!!!!!!sagekit-units.big`).
- **Portraits and icons** are EA's kind: renders of the game model graded against the EA hero
  beside them (the Captain against Dain, Gamling against Boromir), on pages of our own
  (`SKHeroUI_*.tga`, `SKHI*.tga`); their MappedImages are appended to EA's `heroui.ini` and
  `heroselecticons.ini`.
- **Strings.** The game reads `data\lotr.str` from `lang\English*.big` before the root archives
  (exe 0xa14419), and the first archive to file a member wins (0xa18384). So the pack ships 2.02's
  English table plus 18 labels of ours (and two EA labels corrected: Gamling's revive text read
  "Revive Gaming", his hotkey label was missing) as `lang\English!!!!!!!!!!!sagekit-heroes.big`.
- **Upgrades.** None added (EA 1027 + cah 43 = 1070 of 1152). The lint fails on any Upgrade block
  beyond EA's; `python3 -m sagekit validate` counts the staged pack.

## INI files the pack changes

`playertemplate.ini`, `commandset.ini`, `commandbutton.ini`, `default\skirmishaidata.ini`,
`experiencelevels.ini`, `specialpower.ini`, `object\goodfaction\units\rohan\gamling.ini`,
`object\goodfaction\units\men\earnur.ini`, `object\goodfaction\units\men\aragorn.ini`,
`mappedimages\aptimages\heroui.ini`, `mappedimages\aptimages\heroselecticons.ini`, and a new
`object\goodfaction\units\dwarven\sagekitereborcaptain.ini`. The pack refuses to stage while
another archive of ours serves any of them. Everyone in a LAN game needs the same pack.

## Lint (`assets/heroes/lint.py`, in every build)

Rosters, slots and submenus (no new gaps or overlaps against EA's own); every hero's command set,
buttons, powers (defined and carried), labels (in our table), images (mapped), voices (defined),
models (EA's or ours), unique module tags; every level gate granted by the hero's levels; no new
Upgrade. Four broken copies must fail it: a roster grown without a slot, a missing label, a level
never granted, a missing command set.

## Not checked without the game

The radial hero menu now holds 13 buttons on the Men's fortress (EA's 10); whether the palantir lays
them all out; the string archive's load order (if it lost, the new names would show as MISSING);
the copied powers' animations on their new rigs (Train Allies asks for an unpacking animation Dain's
Draw lacks and plays his idle).
