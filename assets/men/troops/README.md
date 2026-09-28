# Men of the West troops and upgrades

Staged review art for Gondor infantry, Rohan Spearmen, Rangers, cavalry, Dol Amroth,
Trebuchets, banners and collector-edition appearances. Heroes remain deferred.
Nothing here installs assets or launches the game.

```sh
python3 -B -m assets.men.troops.build
python3 -B -m assets.men.troops.audit --motion
python3 -B -m assets.men.troops.preview
python3 -B -m assets.men.troops.audit --previews
```

The gallery is `build/assets/men/troops/redesign/review.html`. Every equipment combination
has paired source/proposed stills; representative loadouts show original authored animations.
Use `--stills`, `--motion`, `--unit`, `--variant` and `--pose` to narrow preview work;
`--force` refreshes existing renders after an art change.

The palette emphasizes steel, original white-tree details and restrained warm metal accents.
Rangers retain green and leather; Rohirrim retain their own character and natural horse skins.
Original helmets, faces, hair, bodies and equipment remain intact. Small fitted edges enhance
supported rigid pieces. Meshes with secondary skin channels stay byte-exact; the shared troop
poser evaluates both bone coordinates and original weights. Lower-detail geometry is retained.
Texture alpha, original mip counts and player-colour masks are preserved. The Gondor/Ranger
banner sheets keep their existing shared HC_GUBanner mapping, including its original cache
lookup; its unusual JPEG/PNG source resources are recorded without conversion. Protected face/hair
compressed RGB blocks are copied from source at every mip; the CE sheet retains native DXT1.

The catalog follows installed recruitment and animation routes. Rangers have fire arrows but
no purchased armor; Dol Amroth has no purchased equipment skin. Both Rohirrim weapon modes
and all authored random rider/horse textures are retained. Missing source upgrade subobjects
and incompatible or absent animation references are reported rather than invented.

Private model/texture names isolate the work. Only troop visual directives change. Campaign
Royal Guard, the Lone Tower archer and the enemy Morgul Trebuchet receive their original
inherited Draw and SubObjectsUpgrade modules, preserving their visuals. Other descendants
retain their original overrides, or inherit troop visuals where appropriate for summoned troops.
Heroes, builders, structures, recruitment, gameplay and source animation files remain unchanged.

The shared Dwarven staging, skin audit and preview pipeline is reused. The motion check decodes
every frame of available matching clips; GIFs sample whole clips at their nominal duration.
Particles, projectiles, player-colour blending and game lighting are not simulated. Forged-blade
glow shows offline speckling in both comparison columns; source effect materials are unchanged.
These are offline review results, not runtime approval or performance measurements.

No installer is provided. A reviewed installation must freshly compose current asset caches
and the house-colour table, check source hashes and provide scoped backups and `--revert`.
Do not copy staged caches over a later installation.
