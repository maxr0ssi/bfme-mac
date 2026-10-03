"""The cah pack's Servants of Sauron: more choices for the Orc Raider (subclass 2) and the Uruk (3).

The two stand on different skeletons with no exact map between them, so every part is drawn on
each model's own measured anatomy (assets/cah/evil/anatomy.py; OWN_SPACE); one upgrade serves both
subclasses where both list it. Serious parts follow our Mordor (F2), Isengard, Angmar and Goblin
buildings; fun parts are fixed colours.

    python3 -m assets.cah.servantsofsauron.build [--skip-paint]
    python3 -m assets.cah.evil.render servantsofsauron
"""
import sys

from ..evil import arms, body, fun, helms
from ..evil import spec as E
from ..evil.paint import paint as _paint

NAME, CLASS_FILE = "servantsofsauron", "servantsofsauron"
OR, UK = 2, 3
SUBCLASSES = [{"index": OR, "name": "Orc Raider", "models": ["CHSS_OR_U_SKN", "CHSS_OR_C_SKN"]},
              {"index": UK, "name": "Uruk", "models": ["CHSS_UK_U_SKN", "CHSS_UK_C_SKN"]}]
MODELS = {"CHSS_OR_U_SKN": "SKSS_OR_U_SKN", "CHSS_OR_C_SKN": "SKSS_OR_C_SKN",
          "CHSS_UK_U_SKN": "SKSS_UK_U_SKN", "CHSS_UK_C_SKN": "SKSS_UK_C_SKN"}
SKELETONS = {"chss_or_u_skn": "chss_gb_u_skl", "chss_or_c_skn": "chss_gb_c_skl",
             "chss_uk_u_skn": "chss_uk_u_skl", "chss_uk_c_skn": "chss_uk_c_skl"}
KIND = {"chss_or_u_skn": "u", "chss_or_c_skn": "c", "chss_uk_u_skn": "u", "chss_uk_c_skn": "c"}
DESIGN = "chss_or_u_skn"
OWN_SPACE = tuple(SKELETONS)
EXPECTED = {
    "chss_or_u_skn": "067537c267360c19499f72401bd994c1275bf89c7acab8619d152e9dc63e2f59",
    "chss_or_c_skn": "b351d4e5428fa681eb5fa6bd94e2fffd224ed11b7e092112afe802a952282a65",
    "chss_uk_u_skn": "73e2b32e461348a6cd53b499c9930ecdcf2139c1cbf0f17630ebc0e109fee71f",
    "chss_uk_c_skn": "4341ac37ac21af6b0e8bb57937c7c0f45ad3832ee5645291fdea24e6b9979b2d",
    "chss_gb_u_skl": "410c35b9e9853d1cd03e94941375a4830287ea1a2d7ec3909f065cb3fcdf2e6c",
    "chss_gb_c_skl": "383c6d914bbf7f7f90558e44cbf10c7316d724567c6ab400ac6d390365d0c0e5",
    "chss_uk_u_skl": "e805134c5bc65b09ed2707ed842896c43ca840171cf6714ae5a785d53172c2b9",
    "chss_uk_c_skl": "384c70738691f4a31f423be8134bdc561d6e34e4b6da208f87a493c7347a3bf3",
    "chss_gb_u_atka": "2a8625a6587c190c4d33d80d4df466e1ee8629348b8959a900604b58c6cc6ca9",
    "chss_gb_c_wpna": "ebf2bcf70513d9cfa574337a4615af670fd59d95b8256cf048575cb4045b2a5e",
    "chss_gb_u_idla": "173db87f18573b108fd0788cf1fc5b55af6d6f0b03fe6981ab6c66ac9d253960",
    "chss_gb_c_atnb": "11ffdf86f58a9972c7bd0d07848879f73eae1b2ed658cda7dc8dcfaf64e6faf8",
    "chss_uk_u_atka": "7f2e4316d8feb64ede657f569153972f1194f38a9fe8584037c622edf6e291df",
    "chss_uk_c_wpna": "acbe94c1f660c908798bda57f7920aab0ed7ea39bfdb58370ca70c990c226742",
    "chss_uk_u_idla": "b675d58289d7ee244a25b460a517f5b3a4c8d838df585b3496e3cba3b85134e9",
    "chss_uk_c_atnb": "387f53499c3f1bc4bec4932f5d40531eb0a73a3cb12904ee4fab7a7cde6a3413",
}
CHECK_ANIM = {"chss_gb_u_skl": "chss_gb_u_atka", "chss_gb_c_skl": "chss_gb_c_wpna",
              "chss_uk_u_skl": "chss_uk_u_atka", "chss_uk_c_skl": "chss_uk_c_wpna"}
FIT_REFS, WEAPON_REF, DESIGN_HAND = (), None, "-"
HAND = {s: "-" for s in SKELETONS.values()}
TEMPLATE = {m: ("HLMT_02", "CHSS_UK_Helmet01.tga") for m in SKELETONS}
SHEETS = {"serious": "SKCAH_SSGEAR.tga", "fun": "SKCAH_SSFUN.tga"}
MASKS = {"SKCAH_SSGEAR.tga": "HC_SKCAH_SSGEAR.tga", "SKCAH_SSFUN.tga": "HC_SKCAH_SSFUN.tga"}
BONES = E.BONES
WEAPON_LIKE, WEAPON_NOTE = "WEAPONSET_CREATE_A_HERO_WS_24", "EA's orc and uruk swords (WS_24)"
_ORC = {"weapon": ["AXE_02"], "shoulder": "SLDR_01", "tweak": {}}        # the orc has no shield: the uruk's, on his forearm
_URUK = {"weapon": ["SWD_04"], "shoulder": "SLDR_01", "shield": ["SHLD_01"], "tweak": {}}
E.register(sys.modules[__name__], {"chss_or_u_skn": dict(_ORC, shield_like="chss_uk_u_skn"),
                                   "chss_or_c_skn": dict(_ORC, shield_like="chss_uk_c_skn"),
                                   "chss_uk_u_skn": _URUK, "chss_uk_c_skn": _URUK})
BOTH, URUK = [OR, UK], [UK]
H, SH, SD, W = "CreateAHero_Helmet", "CreateAHero_ShoulderPlates", "CreateAHero_Shield", "CreateAHero_Weapon"
PARTS = E.parts("SOS", [
    ("SKSOS_HLMT_MOR", H, helms.helm_mordor, "Helm of the Dark Tower", "Black iron under a crown of hooked spikes; the Eye on the brow.", "serious", None, BOTH),
    ("SKSOS_HLMT_ISE", H, helms.helm_isengard, "Helm of the White Hand", "An uruk's black-iron kettle, edged in silver.", "serious", None, BOTH),
    ("SKSOS_HLMT_ANG", H, helms.helm_angmar, "Iron Crown of Angmar", "Tall tines, their tips frozen to rime.", "serious", None, BOTH),
    ("SKSOS_HLMT_GOB", H, helms.helm_goblin, "Goblin Skull-cap", "Crimson paint and a beast's horned skull.", "serious", None, BOTH),
    ("SKSOS_FUN_PARTY", H, fun.hat_party, "Party Hat", "Somebody is a year closer to the Dark Lord.", "fun", None, BOTH),
    ("SKSOS_FUN_TOP", H, fun.hat_top, "Top Hat and Monocle", "Frightfully civilised.", "fun", None, BOTH),
    ("SKSOS_FUN_PINK", H, helms.helm_mordor, "Pink Spiked Helm", "The Dark Tower, in hot pink.", "serious", fun.PINK_SPIKED, BOTH),
    ("SKSOS_SLDR_MOR", SH, body.pauldrons_mordor, "Mordor War-plates", "Black iron and hooked steel spikes.", "serious", None, BOTH),
    ("SKSOS_SLDR_GOB", SH, body.pauldrons_goblin, "Goblin Bone-plates", "Crimson iron, a lashed skull, bone spikes.", "serious", None, BOTH),
    ("SKSOS_SLDR_ISE", SH, body.pauldrons_isengard, "Plates of the White Hand", "Silver-edged black iron, stamped with the Hand.", "serious", None, BOTH),
    ("SKSOS_CAPE_MOR", SH, body.cloak_mordor, "Mordor War Cloak", "A ragged cloak with spiked iron clasps.", "serious", None, BOTH),
    ("SKSOS_FUN_BANNR", SH, body.cape_banner, "Rainbow War Banner", "Carried with pride.", "fun", None, BOTH),
    ("SKSOS_SHLD_WH", SD, arms.shield_whitehand, "Shield of the White Hand", "Tall black iron with the Hand of Saruman.", "serious", None, BOTH),
    ("SKSOS_SHLD_MOR", SD, arms.shield_mordor, "Shield of the Black Gate", "Hooked spikes round the Eye.", "serious", None, BOTH),
    ("SKSOS_FUN_HUGME", SD, arms.shield_hugme, "Hug Me Sign", "Nobody has.", "fun", None, BOTH),
    ("SKSOS_WPN_CLEAV", W, arms.cleaver_mordor, "Morgul Cleaver", "Fights as EA's orc and uruk swords.", "serious", None, BOTH),
    ("SKSOS_FUN_CHICK", W, arms.rubber_chicken, "Rubber Chicken", "Squeaks. Fights as a sword.", "fun", None, BOTH),
], range(58, 60))
budget = E.budget_of({"SKSOS_CAPE_MOR", "SKSOS_FUN_BANNR"})


def paint(work):
    return _paint(work, "skcah_ssgear", "skcah_ssfun")


RENDER = {"body": {"chss_or_u_skn": "CHSS_OR_H", "chss_or_c_skn": "CHSS_OR", "chss_uk_u_skn": "OBJCHSS_UK",
                   "chss_uk_c_skn": "OBJCHSS_UK"},
          "colours": [(150, 30, 24), (60, 58, 52), (210, 160, 60)],
          "anims": {"chss_gb_u_skl": "chss_gb_u_idla", "chss_gb_c_skl": "chss_gb_c_atnb",
                    "chss_uk_u_skl": "chss_uk_u_idla", "chss_uk_c_skl": "chss_uk_c_atnb"}}
_HL = [p[0] for p in PARTS if p[1] == H]
RENDER["heads"] = ([("chss_or_c_skn", "EA ORC HLMT_07", ["HLMT_07"], True)] + [("chss_or_c_skn", "ORC " + h[6:], [h], False) for h in _HL] +
                   [("chss_uk_c_skn", "EA URUK HLMT_01", ["HLMT_01"], True)] + [("chss_uk_c_skn", "URUK " + h[6:], [h], False) for h in _HL])
_ORC_EA, _UK_EA = ["GNLT_07", "B00T_05"], ["GNLT_04", "BOOT_03"]
RENDER["kits"] = [("chss_or_c_skn", "EA ORC", ["HLMT_07", "SLDR_05", "AXE_02"] + _ORC_EA, True),
                  ("chss_or_c_skn", "ORC: MORDOR", ["SKSOS_HLMT_MOR", "SKSOS_SLDR_MOR", "SKSOS_WPN_CLEAV"] + _ORC_EA, False),
                  ("chss_or_c_skn", "ORC: PARTY", ["SKSOS_FUN_PARTY", "SKSOS_FUN_BANNR", "SKSOS_FUN_CHICK"] + _ORC_EA, False),
                  ("chss_uk_c_skn", "EA URUK", ["HLMT_01", "SLDR_04", "SWD_04", "SHLD_01"] + _UK_EA, True),
                  ("chss_uk_c_skn", "URUK: WHITE HAND", ["SKSOS_HLMT_ISE", "SKSOS_SLDR_ISE", "SKSOS_SHLD_WH", "SKSOS_WPN_CLEAV"] + _UK_EA, False),
                  ("chss_uk_c_skn", "URUK: HUG ME", ["SKSOS_FUN_PINK", "SKSOS_CAPE_MOR", "SKSOS_FUN_HUGME", "SKSOS_FUN_CHICK"] + _UK_EA, False),
                  ("chss_uk_c_skn", "URUK: TOP HAT", ["SKSOS_FUN_TOP", "SKSOS_FUN_BANNR", "SKSOS_FUN_CHICK"] + _UK_EA, False)]
RENDER["game"] = [("chss_or_u_skn", "EA ORC", ["HLMT_07", "SLDR_05", "AXE_02"] + _ORC_EA, True),
                  ("chss_or_u_skn", "ORC: MORDOR", ["SKSOS_HLMT_MOR", "SKSOS_SLDR_MOR", "SKSOS_WPN_CLEAV"] + _ORC_EA, False),
                  ("chss_or_u_skn", "ORC: BANNER", ["SKSOS_FUN_PARTY", "SKSOS_FUN_BANNR", "SKSOS_FUN_CHICK"] + _ORC_EA, False),
                  ("chss_uk_u_skn", "URUK: WHITE HAND", ["SKSOS_HLMT_ISE", "SKSOS_SLDR_ISE", "SKSOS_SHLD_WH", "SKSOS_WPN_CLEAV"] + _UK_EA, False),
                  ("chss_uk_u_skn", "URUK: PINK", ["SKSOS_FUN_PINK", "SKSOS_CAPE_MOR", "SKSOS_FUN_HUGME", "SKSOS_FUN_CHICK"] + _UK_EA, False),
                  ("chss_uk_u_skn", "URUK: GOBLIN", ["SKSOS_HLMT_GOB", "SKSOS_SLDR_GOB", "SKSOS_WPN_CLEAV"] + _UK_EA, False)]
RENDER["colours"] = [(70, 62, 52), (150, 28, 22), (210, 160, 60)]
RENDER["close"] = [("chss_uk_c_skn", "SHIELD OF THE WHITE HAND", ["SKSOS_SHLD_WH"] + _UK_EA, False, ["SKSOS_SHLD_WH"], 0.9, 60),
                   ("chss_uk_c_skn", "HUG ME", ["SKSOS_FUN_HUGME"] + _UK_EA, False, ["SKSOS_FUN_HUGME"], 0.9, 60),
                   ("chss_or_c_skn", "ORC: BLACK GATE SHIELD", ["SKSOS_SHLD_MOR"] + _ORC_EA, False, ["SKSOS_SHLD_MOR"], 0.9, 60),
                   ("chss_or_c_skn", "MORGUL CLEAVER", ["SKSOS_WPN_CLEAV"] + _ORC_EA, False, ["SKSOS_WPN_CLEAV"], 1.1, -30),
                   ("chss_uk_c_skn", "RUBBER CHICKEN", ["SKSOS_FUN_CHICK"] + _UK_EA, False, ["SKSOS_FUN_CHICK"], 1.0, -30),
                   ("chss_or_c_skn", "MORDOR WAR-PLATES", ["SKSOS_SLDR_MOR"] + _ORC_EA, False, ["SKSOS_SLDR_MOR"], 0.8),
                   ("chss_or_c_skn", "GOBLIN BONE-PLATES", ["SKSOS_SLDR_GOB"] + _ORC_EA, False, ["SKSOS_SLDR_GOB"], .8),
                   ("chss_uk_c_skn", "PLATES OF THE WHITE HAND", ["SKSOS_SLDR_ISE"] + _UK_EA, False, ["SKSOS_SLDR_ISE"], 0.8),
                   ("chss_uk_c_skn", "MORDOR WAR CLOAK", ["SKSOS_CAPE_MOR"] + _UK_EA, False, ["SKSOS_CAPE_MOR"], 1.1, 200),
                   ("chss_or_c_skn", "RAINBOW WAR BANNER", ["SKSOS_FUN_BANNR"] + _ORC_EA, False, ["SKSOS_FUN_BANNR"], 1.1, 200)]
