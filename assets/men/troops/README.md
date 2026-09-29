# Men of the West troops and upgrades

Gondor infantry, Rohan Spearmen, Rangers, cavalry, Dol Amroth, Trebuchets, banners and the
collector-edition appearances. Built and staged; not installed. Heroes later.

```sh
python3 -B -m assets.men.troops.build
python3 -B -m assets.men.troops.audit --motion
python3 -B -m assets.men.troops.preview
python3 -B -m assets.men.troops.audit --previews
```

The gallery is `build/assets/men/troops/redesign/review.html`: paired source/new stills for every
equipment combination, and representative loadouts in their original animations. `--stills`,
`--motion`, `--unit`, `--variant` and `--pose` narrow the preview; `--force` re-renders after an
art change. Staging, the skin audit and the preview pipeline are the Dwarves' (`assets/dwarves/troops`).

## What changed

- **Palette**: steel, the original White Tree details, restrained warm metal accents. Rangers keep
  their green and leather; the Rohirrim keep their own look and natural horse skins.
- **Detail**: small fitted edges on supported rigid pieces. Helmets, faces, hair, bodies and
  equipment stay as EA made them.
- **Kept**: meshes with secondary skin channels (byte-exact), lower-detail geometry, texture
  alpha, mip counts and player-colour masks. Face and hair blocks are copied from source at every
  mip; the CE sheet stays DXT1.
- **Banners**: the Gondor and Ranger banner sheets keep EA's shared `HC_GUBanner` mapping.

## Scope

- The catalog follows the installed recruitment and animation routes. Rangers get fire arrows but
  no bought armour; Dol Amroth has no bought equipment skin. Both Rohirrim weapon modes and all
  random rider and horse textures are kept.
- Private model and texture names isolate the work; only troop Draw modules change. Campaign Royal
  Guard, the Lone Tower archer and the Morgul Trebuchet keep their inherited Draw and
  SubObjectsUpgrade modules. Heroes, builders, structures, recruitment and gameplay are unchanged.

## Known limits

- Missing source upgrade subobjects and animation references are listed in the audit.
- Not simulated offline: particles, projectiles, player-colour blending, game lighting.
- The forged-blade glow speckles in both columns of the previews; EA's effect materials are unchanged.
