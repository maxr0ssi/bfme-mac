"""The cah pack's Elven Archer (archer subclass 0): Elven, Ranger and fun choices appended to the
Create-a-Hero rows of CHAR_EL_U_SKN (in game) and CHAR_EL_C_SKN (creation screen).

The parts (parts.py) are drawn once, in this model's creation-screen rest space, and shared with
the Female Elven Archer (assets/cah/archer_fe); place.py maps them into each model by region.

    python3 -m assets.cah.archer_el.build [--skip-paint]
    python3 -m sagekit.units.cah --stage | --install | --revert [--dry-run]
"""
from . import parts

NAME, CLASS_FILE, STEM, FLAGS = "archer_el", "archer", "AREL", (52, 53, 54)
SUBCLASSES = [{"index": 0, "name": "Elven Archer", "models": ["CHAR_EL_U_SKN", "CHAR_EL_C_SKN"]}]
MODELS = {"CHAR_EL_U_SKN": "SKAR_EL_U_SKN", "CHAR_EL_C_SKN": "SKAR_EL_C_SKN"}
SKELETONS = {"char_el_u_skn": "char_ar_u_skl", "char_el_c_skn": "char_ar_c_skl"}
KIND = {"char_el_u_skn": "u", "char_el_c_skn": "c"}
DESIGN = "char_el_c_skn"
OWN_SPACE = ("char_el_u_skn",)                 # place.py maps each part into the game model by region
EXPECTED = {
    "char_el_u_skn": "caeba4a5262f5d79a39f15037f8791a94eb8612719922ed873801c2e3d239580",
    "char_el_c_skn": "04b15bf84f11dfe1c50308cb882eabbf4ef48ddf3a261eda8524e1ad610b3cdb",
    "char_ar_u_skl": "46a840d31c22390e4730067980a975c5a32ca0af6d62ea6d5b5a7fb852c94510",
    "char_ar_c_skl": "3d80d43d5f0904231a0a5171707e71c11d541ec0b5b16cd1b6ae42b46631d3e8",
    "char_ar_u_atka": "8d46ae595d5688f26adedcdfbe69e3971fcaf9d8ea46bf85eb9010ed5e4f56fa",
    "char_ar_u_idla": "db8c92bb4cb2ef7aa37e88f7bb636ff846eb01fd01f09eb110419aef5343704b",
    "char_ar_c_wpna": "6636aa6ac72a9f0e323a96f579dc1f27b9f35b8852292a6a9075f4b1290cf7b1",
    "char_ar_c_atnb": "e52d22959d1d6747b1e2ec351e51693dd9637945162b69ecb5f3ab9912c87764",
}
CHECK_ANIM = {"char_ar_u_skl": "char_ar_u_atka", "char_ar_c_skl": "char_ar_c_wpna"}
DESIGN_HAND = "BOWBONE"                        # EA's bows ride it (B_HAND_L in game); place.py sets the bones
HAND = {"char_ar_c_skl": "BOWBONE", "char_ar_u_skl": "B_HAND_L"}
TEMPLATE, TEMPLATE_TEX = "HLMT_03", "CHAR_EL_OF3D_HLMT_03.tga"     # EA's hood: ours copy its material
SHEETS = {"serious": "SKCAH_ARELGEAR.tga", "fun": "SKCAH_ARELFUN.tga"}
MASKS = {"SKCAH_ARELGEAR.tga": "HC_SKCAH_ARELGEAR.tga", "SKCAH_ARELFUN.tga": "HC_SKCAH_ARELFUN.tga"}
WEAPON_LIKE, WEAPON_NOTE = "WEAPONSET_CREATE_A_HERO_WS_37", "EA's elven bows (ranged and melee)"
BONES, budget = parts.BONES, parts.budget
PARTS = parts.named(__import__("sys").modules[__name__])
ALSO_SHOW = {}          # EA's bows also show WestronSword, which neither archer model carries

# the overview (python3 -m assets.cah.kit.render archer_el)
RENDER = {"body": {"char_el_u_skn": "LOWLOD", "char_el_c_skn": "OBJCHAR_EL"},
          "head_model": "char_el_c_skn", "game_model": "char_el_u_skn",
          "ea_heads": ["HLMT_01", "HLMT_02", "HLMT_03"],
          "kits": [("EA KIT", ["HLMT_03", "SLDR_04", "GNLT_04", "BOOT_03", "BOW_03", "QUIVR"], True)] + parts.kits(STEM),
          "colours": parts.COLOURS,
          "anims": {"char_ar_u_skl": "char_ar_u_idla", "char_ar_c_skl": "char_ar_c_atnb"}}
