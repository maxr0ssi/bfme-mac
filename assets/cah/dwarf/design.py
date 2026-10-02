"""The cah pack's Dwarf: more choices in the Create-a-Hero screen's existing rows (Taskmaster and
Sage), the first class built with the kit (assets/cah/kit, docs/CAH.md).

Each part is a new hidden sub-object in our copies of EA's four dwarf models (in game _U and
creation-screen _C, Taskmaster and Sage), shown by its upgrade's SubObjectsUpgrade and cleared by
the row's RemoveUpgradeUpgrade; every entry is APPENDED to its row (saved heroes index the rows).

    python3 -m assets.cah.dwarf.build           # EA sources, both sheets, the models, the INI, checks
    python3 -m sagekit.units.cah --stage | --install | --revert [--dry-run]
"""
from . import fun, serious

NAME, CLASS_FILE = "dwarf", "dwarf"
SUBCLASSES = [{"index": 0, "name": "Taskmaster", "models": ["CHDW_TM_U_SKN", "CHDW_TM_C_SKN"]},
              {"index": 1, "name": "Sage", "models": ["CHDW_SG_U_SKN", "CHDW_SG_C_SKN"]}]
# EA's models -> ours (a copy under its own name; EA's files and asset.dat records stay EA's)
MODELS = {"CHDW_TM_U_SKN": "SKDW_TM_U_SKN", "CHDW_TM_C_SKN": "SKDW_TM_C_SKN",
          "CHDW_SG_U_SKN": "SKDW_SG_U_SKN", "CHDW_SG_C_SKN": "SKDW_SG_C_SKN"}
SKELETONS = {"chdw_tm_u_skn": "chdw_dw_u_skl", "chdw_tm_c_skn": "chdw_dw_c_skl",
             "chdw_sg_u_skn": "chdw_dw_u_skl", "chdw_sg_c_skn": "chdw_dw_c_skl"}
KIND = {"chdw_tm_u_skn": "u", "chdw_tm_c_skn": "c", "chdw_sg_u_skn": "u", "chdw_sg_c_skn": "c"}
DESIGN = "chdw_tm_u_skn"
EXPECTED = {
    "chdw_tm_u_skn": "4a81cf21d116d4cf1a9aedc41fe0b7ee73b96a0253750f704f7e9656c2261776",
    "chdw_tm_c_skn": "cb248c0dc1a6b5a9740d13eb08efd36d2924d9766b0594c551862494de33ae29",
    "chdw_sg_u_skn": "e4bcba9dd62f85ddc329fe70bea8d51dc3eb7c6e175085b724e8be040f498ac4",
    "chdw_sg_c_skn": "e63c5cc7dd0fb4e4f16255f445c21168d20de434ed9f18d21aac4d0e5b4eae84",
    "chdw_dw_u_skl": "ff3aab9636969ee52a95a83a4157493906d5a18b5b008d6b8eb8923b9d04fcd6",
    "chdw_dw_c_skl": "a60a6f3c7506d536755a8a9595678324e5811af3f9d5d76c9e2e6793448b121f",
    "chdw_dw_u_atka": "5fab563555f2e01de4add7f9d39f73c8e0c2c1f9dbd752544941c3d2392cb3e5",
    "chdw_dw_c_wpna": "7810331bf266ec069563668a6561c8d6b41a1bd2ecee5b3d21aef63d2b43b2db",
    "chdw_dw_c_atnb": "61ce11ce54e8e84d7ec34adcfd05b212c2f0f943f675e730c22e9a26d0ba01bf",
    "chdw_dw_u_idla": "b4b916988ab397020737ea793e7924ae10ebfa7d4f25baae89ea3da45f72abf1",
}
CHECK_ANIM = {"chdw_dw_u_skl": "chdw_dw_u_atka", "chdw_dw_c_skl": "chdw_dw_c_wpna"}
FIT_REFS = ("HLMT_04", "HLMT_05", "SLDR_04", "SLDR_05", "BOOT_04", "HLMT_06")
WEAPON_REF, DESIGN_HAND = "AXE_02", "B_HAND_R"
HAND = {"chdw_dw_u_skl": "B_HAND_R", "chdw_dw_c_skl": "B_HANDR"}     # the bone EA's AXE_02 rides
TEMPLATE, TEMPLATE_TEX = "HLMT_01", "CHDW_SG_Gear_03.tga"          # the EA part whose material ours copy
SHEETS = {"serious": "SKCAH_DWGEAR.tga", "fun": "SKCAH_DWFUN.tga"}
MASKS = {"SKCAH_DWGEAR.tga": "HC_SKCAH_DWGEAR.tga", "SKCAH_DWFUN.tga": "HC_SKCAH_DWFUN.tga"}
SEAT = {"CreateAHero_Helmet": serious.helm_fit}                    # helmets drawn on a head guide
BONES = {"CreateAHero_Helmet": {"B_HEAD"}, "CreateAHero_Weapon": {"B_HAND_R", "B_HANDR"},
         "CreateAHero_Shield": {"BAT_FARML"}, "CreateAHero_ShoulderPlates": {"BAT_UARML", "BAT_UARMR", "BAT_SPINE2"}}
WEAPON_NOTE = "EA's dwarf axes"
WEAPON_LINES = ["\tWeapon\t\t\t  =\tPRIMARY\tCreateAHeroBasicMeleeWeapon", "\tWeapon\t\t\t  = TERTIARY CreateAHeroAxeThrow",
                "\tAutoChooseSources =\tPRIMARY\tFROM_PLAYER\tFROM_SCRIPT\tFROM_AI", "\tAutoChooseSources = TERTIARY NONE"]
WEAPON_SETS = range(43, 46)                                        # WEAPONSET_CREATE_A_HERO_WS_43..45
# vertex budgets per sub-object, in game (_U) and on the creation screen (_C): EA's dwarf helmets
# reach 401 / 921, shoulders 290 / 576, axes 468-532; cloaks and shields have no EA dwarf equivalent
BUDGET = {"CreateAHero_Helmet": (650, 950), "CreateAHero_ShoulderPlates": (700, 1100),
          "CreateAHero_Shield": (600, 900), "CreateAHero_Weapon": (540, 700)}
# a cloak is a large sheet; the spangenhelm's eight gilded strips stay visible from the RTS camera
OWN_BUDGET = {"SKH_SLDR_MN": (900, 1350), "SKH_FUN_PINKCAPE": (900, 1350), "SKH_FUN_RAINBOW": (900, 1350),
              "SKH_HLMT_KD": (700, 950)}


def _parts():
    """[(sub-object, group, design, name, description, sheet, remap, upgrade)] in APPEND order."""
    out = [(k, g, d, n, t, "serious", None) for k, (g, d, n, t) in serious.SERIOUS.items()]
    out += [(k, g, d, n, t, sheet, remap) for k, (g, d, n, t, sheet, remap) in fun.FUN.items()]
    count = {"CreateAHero_Helmet": 7, "CreateAHero_ShoulderPlates": 7, "CreateAHero_Shield": 1, "CreateAHero_Weapon": 43}
    pattern = {"CreateAHero_Helmet": "Upgrade_SKH_DWARF_CHH%02d", "CreateAHero_ShoulderPlates": "Upgrade_SKH_DWARF_CHSP%02d",
               "CreateAHero_Shield": "Upgrade_SKH_DWARF_CHS%02d", "CreateAHero_Weapon": "Upgrade_SKH_CHW%02d"}
    named = []
    for k, g, d, n, t, sheet, remap in out:
        named.append((k, g, d, n, t, sheet, remap, pattern[g] % count[g]))
        count[g] += 1
    return named


PARTS = _parts()


def budget(name, group, kind):
    return OWN_BUDGET.get(name, BUDGET[group])[0 if kind in ("u", "m") else 1]   # mounted: the in-game cap


# the overview (python3 -m assets.cah.kit.render dwarf)
RENDER = {"body": {"chdw_tm_u_skn": "CH_DWARF_04", "chdw_tm_c_skn": "CHDW_TM", "chdw_sg_u_skn": "CH_DWARF_03",
                   "chdw_sg_c_skn": "OBJCHDW_SG"},
          "head_model": "chdw_tm_c_skn", "game_model": "chdw_tm_u_skn",
          "ea_heads": ["HLMT_01", "HLMT_03", "HLMT_05", "HLMT_06"],
          "kits": [("EA KIT", ["HLMT_06", "SLDR_06", "GNLT_04", "BOOT_04", "AXE_03"], True),
                   ("EREBOR", ["SKH_HLMT_ER", "SKH_SLDR_ER", "SKH_SHLD_ER", "SKH_AXE_ER", "GNLT_04", "BOOT_04"], False),
                   ("PINK", ["SKH_FUN_DUCK", "SKH_FUN_PINKCAPE", "SKH_FUN_PINKSH", "SKH_FUN_PAN", "GNLT_04", "BOOT_04"], False),
                   ("RAINBOW", ["SKH_FUN_JESTER", "SKH_FUN_RAINBOW", "SKH_FUN_SMILEY", "SKH_FUN_FISH", "GNLT_02", "BOOT_03"], False)],
          "colours": [(70, 52, 38), (38, 66, 150), (196, 156, 72)],
          "anims": {"chdw_dw_u_skl": "chdw_dw_u_idla", "chdw_dw_c_skl": "chdw_dw_c_atnb"}}
