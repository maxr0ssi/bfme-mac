"""The cah pack's Female Elven Archer (archer subclass 1): the Archers' Elven, Ranger and fun
choices appended to the Create-a-Hero rows of CHAR_FE_U_SKN (in game) and CHAR_FE_C_SKN (creation
screen). Her models share no skeleton or part with the Elven Archer's, so she is her own folder
(docs/CAH.md); the parts are the Elven Archer's designs (assets/cah/archer_el/parts.py), mapped
onto her by region (archer_el/place.py, measured from EA's parts on both archers).

    python3 -m assets.cah.archer_fe.build [--skip-paint]
    python3 -m sagekit.units.cah --stage | --install | --revert [--dry-run]
"""
import sys

from ..archer_el import parts

NAME, CLASS_FILE, STEM, FLAGS = "archer_fe", "archer", "ARFE", (55, 56, 57)
SUBCLASSES = [{"index": 1, "name": "Female Elven Archer", "models": ["CHAR_FE_U_SKN", "CHAR_FE_C_SKN"]}]
MODELS = {"CHAR_FE_U_SKN": "SKAR_FE_U_SKN", "CHAR_FE_C_SKN": "SKAR_FE_C_SKN"}
SKELETONS = {"char_fe_u_skn": "char_fe_u_skl", "char_fe_c_skn": "char_fe_c_skl"}
KIND = {"char_fe_u_skn": "u", "char_fe_c_skn": "c"}
DESIGN = "char_fe_c_skn"
OWN_SPACE = ("char_fe_u_skn",)                 # archer_el/place.py maps each part into each model by region
EXPECTED = {
    "char_fe_u_skn": "7a9a522a6319e85921ba5d943ae792ebb78da4347e5d96d5be50e9cec0d4e744",
    "char_fe_c_skn": "3fdb5e5009a8d6640c0a194d74c86639d32d1f47fb9ad7a2a81ec4ebd1f12b96",
    "char_fe_u_skl": "03fa699fba6a62d3354717bbfeb61cb1a6181c154d949aa0f40a618222244114",
    "char_fe_c_skl": "ef84c726d96654a778fe504267b3c43b11cb9b31827d294b5c928dcae497f920",
    "char_fe_u_atka": "b922e716c97163612049c05a1b0d5356ba1188e35fda22edf0de45a4bc95bb8b",
    "char_fe_u_idla": "674388055688b4f096fe6c8621676c73436bb1df0fc7660a13d04d9d06fcbd0f",
    "char_fe_c_wpna": "2963c655e5c12c903ff52e69aa8d062a05cac9b624588cc9813dbeb2b6c3e09e",
    "char_fe_c_atnb": "75c383bf0d7a7652a833468ebd7ad68d462cd09917eab1a1c682421f020ef67b",
    # the design space: the Elven Archer's creation-screen model, for the maps onto her
    "char_el_c_skn": "04b15bf84f11dfe1c50308cb882eabbf4ef48ddf3a261eda8524e1ad610b3cdb",
    "char_ar_c_skl": "3d80d43d5f0904231a0a5171707e71c11d541ec0b5b16cd1b6ae42b46631d3e8",
}
CHECK_ANIM = {"char_fe_u_skl": "char_fe_u_atka", "char_fe_c_skl": "char_fe_c_wpna"}
DESIGN_HAND = "BOWBONE"                        # the design's bow bone; place.py sets each model's bones
HAND = {"char_fe_c_skl": "B_HANDL", "char_fe_u_skl": "B_HAND_L"}
TEMPLATE, TEMPLATE_TEX = "HLMT_05", "CHAR_FE_OF3D_HLMT_03.tga"     # EA's hood: ours copy its material
SHEETS = {"serious": "SKCAH_ARFEGEAR.tga", "fun": "SKCAH_ARFEFUN.tga"}
MASKS = {"SKCAH_ARFEGEAR.tga": "HC_SKCAH_ARFEGEAR.tga", "SKCAH_ARFEFUN.tga": "HC_SKCAH_ARFEFUN.tga"}
WEAPON_LIKE, WEAPON_NOTE = "WEAPONSET_CREATE_A_HERO_WS_37", "EA's elven bows (ranged and melee)"
BONES, budget = parts.BONES, parts.budget
PARTS = parts.named(sys.modules[__name__])
ALSO_SHOW = {}          # EA's bows also show WestronSword, which neither archer model carries

# the overview (python3 -m assets.cah.kit.render archer_fe)
RENDER = {"body": {"char_fe_u_skn": "CHAR_FE1", "char_fe_c_skn": "CHAR_FE1"},
          "head_model": "char_fe_c_skn", "game_model": "char_fe_u_skn",
          "ea_heads": ["HLMT_05", "HLMT_03", "HLMT_04"],
          "kits": [("EA KIT", ["HAIR", "HLMT_05", "SLDR_06", "GNLT_07", "BOOT_03", "BOW_03", "QUIVR"], True)] + parts.kits(STEM),
          "colours": parts.COLOURS,
          "anims": {"char_fe_u_skl": "char_fe_u_idla", "char_fe_c_skl": "char_fe_c_atnb"}}
