"""The cah pack's Olog-hai: more choices for the Troll (subclass 0), the Snow Troll (1) and the Hill
Troll (2). Three rigs of different sizes, rest poses and bone names (and in-game and creation-screen
models at different scales), so every part is drawn on each model's own measured anatomy
(assets/cah/evil/anatomy.py; OWN_SPACE); one upgrade serves all three. Serious parts follow our
Mordor (F2) and Angmar buildings; the fun ones are fixed colours, the tutu sits in the shoulder row
(the menu has no skirt row) and every troll carries EA's one troll weapon set.

    python3 -m assets.cah.ologhai.build [--skip-paint]
    python3 -m assets.cah.evil.render ologhai
"""
import sys

from ..evil import arms, body, fun, helms
from ..evil import spec as E

from ..evil.paint import paint as _paint

NAME, CLASS_FILE = "ologhai", "ologhai"
SUBCLASSES = [{"index": 0, "name": "Troll", "models": ["CHSS_TL_U_SKN", "CHSS_TL_C_SKN"]},
              {"index": 1, "name": "Snow Troll", "models": ["CHTL_ST_U_SKN", "CHTL_ST_C_SKN"]},
              {"index": 2, "name": "Hill Troll", "models": ["CHTL_HT_U_SKN", "CHTL_HT_C_SKN"]}]
MODELS = {"CHSS_TL_U_SKN": "SKSS_TL_U_SKN", "CHSS_TL_C_SKN": "SKSS_TL_C_SKN", "CHTL_ST_U_SKN": "SKTL_ST_U_SKN",
          "CHTL_ST_C_SKN": "SKTL_ST_C_SKN", "CHTL_HT_U_SKN": "SKTL_HT_U_SKN", "CHTL_HT_C_SKN": "SKTL_HT_C_SKN"}
SKELETONS = {"chss_tl_u_skn": "chss_tl_u_skl", "chss_tl_c_skn": "chss_tl_c_skl", "chtl_st_u_skn": "chtl_st_u_skl",
             "chtl_st_c_skn": "chtl_st_c_skl", "chtl_ht_u_skn": "chtl_ht_u_skl", "chtl_ht_c_skn": "chtl_ht_c_skl"}
KIND = {m: m[-5] for m in SKELETONS}
DESIGN = "chtl_st_u_skn"
OWN_SPACE = tuple(SKELETONS)
EXPECTED = {
    "chss_tl_u_skn": "f06c79ee88dbade7f278c13d797143cdbe5e6fc6a4cbbcb25f95fb08e8a4e169",
    "chss_tl_c_skn": "9e99d008c753c65094ee5a29364d60921a8df11ff158a101cf5e395859041b5f",
    "chtl_st_u_skn": "54aaa73b52b34885bf1b20be1444806577c582c157b7702e5570daf39af3fd91",
    "chtl_st_c_skn": "b64e2db160a2f3238bc21df630e0e38ee37b8b46cc7898d59351ed08792b582c",
    "chtl_ht_u_skn": "13615c38c4b22890618db7214f6d817d2f57c0ae050de3aca4a5fc4787429b54",
    "chtl_ht_c_skn": "dbe919168ff9a2d97698399f80fd208b4392534c0d3e0e8af112ea9e23b95d3d",
    "chss_tl_u_skl": "ed7d3014f71a9a2f0a3caf8f1f4293373e124b48993965ad83287a9dec5378c6",
    "chss_tl_c_skl": "29c05f46b04ededa35429bda1366296b1556f70ccfc25283035d190045ffffa6",
    "chtl_st_u_skl": "9d1ceaa695796fbc055307fac63439bc5a54a250cd5e5c918b42e299f2dbb91b",
    "chtl_st_c_skl": "ad373ddae1a1f2a049375f129adcb81510a202ae9bf6a3819b4549877186ecc9",
    "chtl_ht_u_skl": "94c2cc44fb04bd2ac32e125175cbb283db13d953cd8a50e4536474993576b856",
    "chtl_ht_c_skl": "b20e4a269d39718ee39473feaeeafb3ae9f8c23490d17bc1f6c5de29b3ab43d9",
    "chss_tl_u_atka": "18891d571febe22920c06df75e176785a9fa8cea362bad07b8870a9100c7cbf4",
    "chss_tl_c_wpna": "422d02e8091e74634cb43937a0e9c441d91d01c9ee5ae776c2945bcdc1cd6804",
    "chss_tl_u_idla": "991ffb2730333b2f6043e9f6d7a049aca369e8185d7e78ae63875bb23f159b26",
    "chss_tl_c_atnb": "0c2db1a4db0ec16654cefbefc16b004f87995cf52333746e1645cffbb901c0bb",
    "chtl_st_u_atka": "77fe20802ba72da80ff14ef380c963efe31a5eaf2deff268a299eef00f045e31",
    "chtl_st_c_wpna": "7f486b69e258a03a9d020e7595de78fd1f5efd6aace846c30daa037c9d1cd9e4",
    "chtl_st_u_idla": "a9a4ce86c0c3ea5990138fadd7707dffd1e681c864441a6f2eec2cca2d5fd421",
    "chtl_st_c_atnb": "aa17c546f1742fb7452eecb13f50fa6c752ccefea0110f7aa92a391d938a72c4",
    "chtl_ht_u_atka": "1bf8f9806082db8ff7c1ec8385722378508cac36d35f7f1bf5414e7b9daffd0f",
    "chtl_ht_c_wpna": "29ca10391e6629b7089725e9164287192a34bc16f5f2efd3850557cbcf918b19",
    "chtl_ht_u_idla": "d71f173344b7a13eb0734429c601ad885c8db7cb4ad3d2d30eec3ebb151a2bbd",
    "chtl_ht_c_atnb": "fe57252606bfaeb7fe9811d5022a16a23d6c37185b24e544fe0986df051f1593",
}
CHECK_ANIM = {s: s[:-4] + ("_atka" if s[8] == "u" else "_wpna") for s in SKELETONS.values()}
FIT_REFS, WEAPON_REF, DESIGN_HAND = (), None, "-"
HAND = {s: "-" for s in SKELETONS.values()}
TEMPLATE = {m: ("HLMT_02", "MUMntTroll_CHERO_high.tga") for m in SKELETONS}
SHEETS = {"serious": "SKCAH_TLGEAR.tga", "fun": "SKCAH_TLFUN.tga"}
MASKS = {"SKCAH_TLGEAR.tga": "HC_SKCAH_TLGEAR.tga", "SKCAH_TLFUN.tga": "HC_SKCAH_TLFUN.tga"}
BONES = E.BONES
WEAPON_LIKE, WEAPON_NOTE = "WEAPONSET_CREATE_A_HERO_WS_33", "EA's troll weapons (one set for all three trolls)"
_TL = {"weapon": ["HMR_02"], "shoulder": "SLDR_01", "weapon_scale": .058, "tweak": {}}
_ST = {"weapon": ["HMR_04"], "shoulder": "SLDR_01", "shield": ["SHLD_01"], "weapon_scale": .058, "tweak": {}}
E.register(sys.modules[__name__], {      # trolls without EA's shield carry one where the Snow Troll does
    "chss_tl_u_skn": dict(_TL, shield_like="chtl_st_u_skn"), "chss_tl_c_skn": dict(_TL, shield_like="chtl_st_c_skn"),
    "chtl_st_u_skn": _ST, "chtl_st_c_skn": _ST, "chtl_ht_u_skn": dict(_ST, shield_like="chtl_st_u_skn"), "chtl_ht_c_skn": _ST})
ALL = [0, 1, 2]
H, SH, SD, W = "CreateAHero_Helmet", "CreateAHero_ShoulderPlates", "CreateAHero_Shield", "CreateAHero_Weapon"
PARTS = E.parts([
    ("SKOLG_HLMT_MOR", H, helms.helm_mordor, "Helm of the Dark Tower", "Black iron under a crown of hooked spikes; the Eye on the brow.", "serious", None, ALL),
    ("SKOLG_HLMT_ANG", H, helms.helm_angmar, "Iron Crown of Angmar", "Tall tines, their tips frozen to rime.", "serious", None, ALL),
    ("SKOLG_FUN_FLOWR", H, fun.flower_crown, "Flower Crown", "Picked fresh this morning.", "fun", None, ALL),
    ("SKOLG_FUN_BUCKT", H, fun.bucket, "Bucket", "It was on the head when found.", "fun", None, ALL),
    ("SKOLG_FUN_PARTY", H, fun.hat_party, "Party Hat", "Somebody is a year closer to turning to stone.", "fun", None, ALL),
    ("SKOLG_FUN_PINK", H, helms.helm_mordor, "Pink Spiked Helm", "The Dark Tower, in hot pink.", "serious", fun.PINK_SPIKED, ALL),
    ("SKOLG_SLDR_MOR", SH, body.pauldrons_mordor, "Mordor War-plates", "Black iron and hooked steel spikes.", "serious", None, ALL),
    ("SKOLG_SLDR_ANG", SH, body.pauldrons_angmar, "Frost-plates of Angmar", "Blue iron and tines frozen white.", "serious", None, ALL),
    ("SKOLG_CAPE_MOR", SH, body.cloak_mordor, "Mordor War Cloak", "A ragged cloak with spiked iron clasps.", "serious", None, ALL),
    ("SKOLG_FUN_TUTU", SH, body.tutu, "Tutu", "Light on its feet. Mostly.", "fun", None, ALL),
    ("SKOLG_FUN_BANNR", SH, body.cape_banner, "Rainbow War Banner", "Carried with pride.", "fun", None, ALL),
    ("SKOLG_SHLD_MOR", SD, arms.shield_mordor, "Shield of the Black Gate", "Hooked spikes round the Eye.", "serious", None, ALL),
    ("SKOLG_FUN_HUGME", SD, arms.shield_hugme, "Hug Me Sign", "Nobody has.", "fun", None, ALL),
    ("SKOLG_WPN_MAUL", W, arms.maul_mordor, "Mordor Siege Maul", "Fights as EA's troll weapons.", "serious", None, ALL),
    ("SKOLG_FUN_LOLLY", W, arms.lollipop, "Giant Lollipop", "Sticky. Fights as a troll weapon.", "fun", None, ALL),
    ("SKOLG_WPN_CLUB", W, arms.club_angmar, "Rime-club of Angmar", "Fights as EA's troll weapons.", "serious", None, ALL),
], range(62, 65))
budget = E.budget_of({"SKOLG_CAPE_MOR", "SKOLG_FUN_BANNR", "SKOLG_FUN_TUTU"})
# every part rides the hero's bones in models of our own (assets/cah/kit/attach.py, docs/CAH.md); EA's
# models are not copied. Staged with python3 -m sagekit.units.cah --stage.
ATTACH, ATTACH_STEM = [p[0] for p in PARTS], "SKTL"
# the fun parts whose hat cloth takes the Paint colour (kit/attach_lint.py paint_lint); every other fun
# part keeps its fixed colours, and every serious part has its enamel, cloth or leather on Paint
FUN_TINTED = ["SKOLG_FUN_PARTY"]


def paint(work):
    return _paint(work, "skcah_tlgear", "skcah_tlfun")


_HL = [p[0] for p in PARTS if p[1] == H]
_BODY = {"chss_tl_u_skn": "DEFAULT", "chss_tl_c_skn": "DEFAULT", "chtl_st_u_skn": "SNTL_HT", "chtl_st_c_skn": "SNTL_HT",
         "chtl_ht_u_skn": "CHTL_HT_C_SKN", "chtl_ht_c_skn": "CHTL_HT_C_SKN"}
_EA = {"chss_tl": ["GNLT_01", "BOOT_01"], "chtl_st": ["GNLT_10", "BOOT_01"], "chtl_ht": ["GNLT_10", "BOOT_01"]}
_K = lambda m, label, parts, ea=False: (m, label, parts + _EA[m[:7]], ea)
RENDER = {"body": _BODY, "colours": [(70, 62, 52), (150, 28, 22), (150, 28, 22)],
          "anims": {s: s[:-4] + ("_idla" if s[8] == "u" else "_atnb") for s in SKELETONS.values()},
          "heads": ([("chss_tl_c_skn", "EA TROLL HLMT_02", ["HLMT_02"], True)] + [("chss_tl_c_skn", "TROLL " + h[6:], [h], False) for h in _HL] +
                    [("chtl_st_c_skn", "EA SNOW HLMT_08", ["HLMT_08"], True)] + [("chtl_st_c_skn", "SNOW " + h[6:], [h], False) for h in _HL] +
                    [("chtl_ht_c_skn", "EA HILL HLMT_05", ["HLMT_05"], True)] + [("chtl_ht_c_skn", "HILL " + h[6:], [h], False) for h in _HL]),
          "kits": [_K("chss_tl_c_skn", "EA TROLL", ["HLMT_02", "SLDR_01", "TROLLHAMMER"], True),
                   _K("chss_tl_c_skn", "TROLL: MORDOR", ["SKOLG_HLMT_MOR", "SKOLG_SLDR_MOR", "SKOLG_SHLD_MOR", "SKOLG_WPN_MAUL"]),
                   _K("chss_tl_c_skn", "TROLL: TUTU", ["SKOLG_FUN_FLOWR", "SKOLG_FUN_TUTU", "SKOLG_FUN_LOLLY"]),
                   _K("chtl_st_c_skn", "SNOW: ANGMAR", ["SKOLG_HLMT_ANG", "SKOLG_SLDR_ANG", "SKOLG_SHLD_MOR", "SKOLG_WPN_CLUB"]),
                   _K("chtl_st_c_skn", "SNOW: BUCKET", ["SKOLG_FUN_BUCKT", "SKOLG_FUN_BANNR", "SKOLG_FUN_HUGME", "SKOLG_FUN_LOLLY"]),
                   _K("chtl_ht_c_skn", "HILL: MORDOR", ["SKOLG_HLMT_MOR", "SKOLG_CAPE_MOR", "SKOLG_WPN_MAUL"]),
                   _K("chtl_ht_c_skn", "HILL: TUTU", ["SKOLG_FUN_PINK", "SKOLG_FUN_TUTU", "SKOLG_FUN_HUGME", "SKOLG_FUN_LOLLY"])],
          "close": [_K("chtl_st_c_skn", "TUTU", ["SKOLG_FUN_TUTU"]) + (["SKOLG_FUN_TUTU"], 1.12),
                    _K("chtl_st_c_skn", "HUG ME", ["SKOLG_FUN_HUGME"]) + (["SKOLG_FUN_HUGME"], 1.12, 60),
                    _K("chss_tl_c_skn", "BLACK GATE SHIELD", ["SKOLG_SHLD_MOR"]) + (["SKOLG_SHLD_MOR"], 1.12, 60),
                    _K("chtl_ht_c_skn", "SIEGE MAUL", ["SKOLG_WPN_MAUL"]) + (["SKOLG_WPN_MAUL"], 1.6, -30),
                    _K("chtl_ht_c_skn", "FROST-PLATES", ["SKOLG_SLDR_ANG"]) + (["SKOLG_SLDR_ANG"], 0.96),
                    _K("chtl_st_c_skn", "WAR-PLATES", ["SKOLG_SLDR_MOR"]) + (["SKOLG_SLDR_MOR"], .96),
                    _K("chss_tl_c_skn", "RIME-CLUB", ["SKOLG_WPN_CLUB"]) + (["SKOLG_WPN_CLUB"], 1.4, -30),
                    _K("chss_tl_c_skn", "WAR CLOAK", ["SKOLG_CAPE_MOR"]) + (["SKOLG_CAPE_MOR"], 1.3, 200),
                    _K("chtl_ht_c_skn", "RAINBOW BANNER", ["SKOLG_FUN_BANNR"]) + (["SKOLG_FUN_BANNR"], 1.3, 200)],
          "game": [_K("chss_tl_u_skn", "EA TROLL", ["HLMT_02", "SLDR_01", "TROLLHAMMER"], True),
                   _K("chss_tl_u_skn", "TROLL: MORDOR", ["SKOLG_HLMT_MOR", "SKOLG_SLDR_MOR", "SKOLG_SHLD_MOR", "SKOLG_WPN_MAUL"]),
                   _K("chtl_st_u_skn", "SNOW: ANGMAR", ["SKOLG_HLMT_ANG", "SKOLG_SLDR_ANG", "SKOLG_WPN_CLUB"]),
                   _K("chtl_st_u_skn", "SNOW: TUTU", ["SKOLG_FUN_FLOWR", "SKOLG_FUN_TUTU", "SKOLG_FUN_LOLLY"]),
                   _K("chtl_ht_u_skn", "HILL: BUCKET", ["SKOLG_FUN_BUCKT", "SKOLG_FUN_BANNR", "SKOLG_FUN_HUGME", "SKOLG_FUN_LOLLY"]),
                   _K("chtl_ht_u_skn", "HILL: PINK", ["SKOLG_FUN_PINK", "SKOLG_FUN_TUTU", "SKOLG_WPN_MAUL"])]}
