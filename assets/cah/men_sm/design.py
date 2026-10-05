"""The cah pack's Men of the West, Shieldmaiden (subclass 1): Rohan's helms (the Eorlingas'
horse-crest, the Golden Hall's guard, the shieldmaiden's own), Dol Amroth's swan helm and Arnor's
star crown; Rohan's gilded pauldrons, the Cloak of the Mark, the sun-wheel shield and a Rohirrim
sword; and the fun choices. Every design is the Captain's (assets/cah/men_cg) on her own body.

Drawn in CHHW_SM_U_SKN's rest space and mapped into CHHW_SM_C_SKN and the mounted CHHW_SM_M_SKN
by exact fits of EA's parts matched by UV (men_cg/fit.py): head and shoulders by HLMT_02, shields
by SHLD_01 (within 0.2 on the creation screen), the sword by SWRD_05.

    python3 -m assets.cah.men_sm.build
    python3 -m assets.cah.kit.render men_sm
"""
import sys

from ..men_cg import body as B
from ..men_cg import common as C
from ..men_cg import fun as F
from ..men_cg import helms as Hm
from ..men_cg import paint as T

NAME, CLASS_FILE = "men_sm", "menofthewest"
SUBCLASSES = [{"index": 1, "name": "Shield Maiden", "models": ["CHHW_SM_U_SKN", "CHHW_SM_C_SKN", "CHHW_SM_M_SKN"]}]
MODELS = {"CHHW_SM_U_SKN": "SKHW_SM_U_SKN", "CHHW_SM_C_SKN": "SKHW_SM_C_SKN", "CHHW_SM_M_SKN": "SKHW_SM_M_SKN"}
SKELETONS = {"chhw_sm_u_skn": "chhw_sm_u_skl", "chhw_sm_c_skn": "chhw_sm_c_skl", "chhw_sm_m_skn": "chhw_sm_m_skl"}
KIND = {"chhw_sm_u_skn": "u", "chhw_sm_c_skn": "c", "chhw_sm_m_skn": "m"}
DESIGN = "chhw_sm_u_skn"
EXPECTED = {
    "chhw_sm_u_skn": "ce9d6b86511440b62dc4f6f0a303eb5873ceaced3a01ed884375924e61c98b32",
    "chhw_sm_c_skn": "4dd40a3820298933173784741529fefcdd2f85145efa44c1a22e1af1d88b84b8",
    "chhw_sm_m_skn": "35b33bc958ddddcc484d4cbb259d67155ff99958b3189671d26059cdee406cb4",
    "chhw_sm_u_skl": "c18f8d75425ff6f9044a0a20a859e3352b721c480b888b153f225797d5a234b4",
    "chhw_sm_c_skl": "632d8404a1dbd549f7f4483a6a8f1e7b893c8a92178495f0ad927913983e1b00",
    "chhw_sm_m_skl": "37fb7289cf4fca70c6c43d71dace8069835700111c680b879440c801a6743217",
    "chhw_sm_u_atka": "60ecde8f7eef5582207d010f20e93208f65f7fa96ae3fc5a94d0ff3a5f996456",
    "chhw_sm_u_idla": "d987e1396b89d4fb4b909be90e5bd91dd64ce27e6177d15ffeb1f728db39fe68",
    "chhw_sm_c_wpna": "e133970ea1d0bfccc8539e8d56d094f5063e47b1988b2dc849701f560b80bcb6",
    "chhw_sm_c_atnb": "dbdfc6085cc01277612eb3e8056165227de4bff5ee635d260fb23293a12bb019",
    "chhw_sm_m_atka": "99d8d16d8c35983a023b59efbf06165441f3bd107ec85be9539a344814918969",
    "chhw_sm_m_idla": "9b19ad4f756eae99e3418c17723d3341f020071da2640d46a16f5fc79692371b",
}
CHECK_ANIM = {"chhw_sm_u_skl": "chhw_sm_u_atka", "chhw_sm_c_skl": "chhw_sm_c_wpna", "chhw_sm_m_skl": "chhw_sm_m_atka"}
FIT_REFS = ()
OWN_SPACE = ("chhw_sm_c_skn", "chhw_sm_m_skn")                # placed by men_cg/fit.wrap, per group
REFS = {"CreateAHero_Helmet": ("HLMT_02",), "CreateAHero_ShoulderPlates": ("HLMT_02",),
        "CreateAHero_Shield": (("SHLD_01", .25),), "CreateAHero_Weapon": ("SWRD_05",)}
WEAPON_REF, DESIGN_HAND = "SWRD_05", "HAND"
PER_SKELETON = {
    "chhw_sm_u_skl": {"HEAD": "BONE14", "SPINE": "BONE13", "UARM_L": "BONE09", "UARM_R": "BONE05", "SHIELD": "B_HAND_L"},
    "chhw_sm_c_skl": {"HEAD": "B_HEAD", "SPINE": "BAT_SPINE2", "UARM_L": "BAT_UARML", "UARM_R": "BAT_UARMR", "SHIELD": "B_HANDL"},
    "chhw_sm_m_skl": {"HEAD": "BAT_HEAD", "SPINE": "BAT_SPINE2", "UARM_L": "BAT_UARML", "UARM_R": "BAT_UARMR", "SHIELD": "B_HANDL"}}
HAND = {"chhw_sm_u_skl": "B_HAND_R", "chhw_sm_c_skl": "B_HAND_R", "chhw_sm_m_skl": "SPEARBONE"}   # where EA's SWRD_05 rides
BONES = C.bones({k: dict(v, HAND=HAND[k]) for k, v in PER_SKELETON.items()})
TEMPLATE, TEMPLATE_TEX = "HLMT_01", "CHHW_SM_GEAR_01.tga"         # in all three models
SHEETS = {"serious": "SKCAH_HWSMGEAR.tga", "fun": "SKCAH_HWSMFUN.tga"}
MASKS = {"SKCAH_HWSMGEAR.tga": "HC_SKCAH_HWSMGEAR.tga", "SKCAH_HWSMFUN.tga": "HC_SKCAH_HWSMFUN.tga"}
HEAD_SEAT = C.seat(0.02, 19.85, .84)                               # canonical head (men_cg/helms.py) -> hers
WEAPON_LIKE, WEAPON_NOTE = "WEAPONSET_CREATE_A_HERO_WS_04", "EA's swords of the West"

# CHHW_SM_U_SKN's anatomy for men_cg/body.py (rest space: +X front, +Y left, +Z up)
ANATOMY = dict(
    shoulder=(-0.5, 2.1, 16.95), up=(0.0, .55, .83), pauldron=1.15, arm=(0.0, .7, -.71),
    cloak_cx=-0.25, fold=.16, cloak_saddle=4,
    cloak=[(2.4, 3.9, 9.0), (2.25, 3.75, 10.2), (2.1, 3.6, 11.4), (1.98, 3.45, 12.6), (1.9, 3.3, 13.8), (1.86, 3.2, 14.8),
           (1.8, 3.1, 15.7), (1.66, 2.9, 16.5), (1.46, 2.6, 17.1), (1.2, 2.2, 17.5)],
    collar=(-0.25, 1.25, 1.65, 17.4), collar_r=.24, clasp=(0.65, 1.25, 17.0),
    shield=((0.04, 7.98, 11.64), (0.0, .882, .472), (1.0, 0.0, 0.0)), shield_size=(4.0, 2.5), shield_off=.4,
    grip=((0.0, -7.402, 11.021), (1.0, 0.0, 0.0), (0.0, -.986, .17)), guard_at=.75)
A = ANATOMY
PINK_PLUME = {T.HORSEHAIR: T.PINKHAIR}

ENTRIES = [   # (sub-object, group, design, name, description, sheet, remap) in APPEND order
    ("SKHWSM_HEORL", "CreateAHero_Helmet", Hm.helm_eorl, "Helm of the Eorlingas",
     "Gilded spangen, a golden horse on the brow and a long horsehair tail.", "serious", None),
    ("SKHWSM_HGUARD", "CreateAHero_Helmet", Hm.helm_guard, "Helm of the Golden Hall",
     "The royal guard's tall gilded helm, with a white horsetail.", "serious", None),
    ("SKHWSM_HMAID", "CreateAHero_Helmet", Hm.helm_shieldmaiden, "Shieldmaiden's Helm",
     "A light steel helm, green-enamelled, with swept cheek guards.", "serious", None),
    ("SKHWSM_HSWAN", "CreateAHero_Helmet", Hm.helm_swan, "Swan Helm of Dol Amroth",
     "Silver on sea-blue, a white swan rising from the crown.", "serious", None),
    ("SKHWSM_HARN", "CreateAHero_Helmet", Hm.helm_arnor, "Star Crown of Arnor",
     "A fluted mithril helm crowned with seven stars, the Elendilmir on the brow.", "serious", None),
    ("SKHWSM_SPMARK", "CreateAHero_ShoulderPlates", lambda m: B.pauldrons(m, A, plate=T.GILT, trim=T.STEEL), "Gilded Pauldrons",
     "Engraved gilt shoulder plates of the Mark, edged in steel.", "serious", None),
    ("SKHWSM_SPCLOAK", "CreateAHero_ShoulderPlates", lambda m: B.cloak_mark(m, A), "Cloak of the Mark",
     "A green riding cloak with a gold-braided hem.", "serious", None),
    ("SKHWSM_SHSUN", "CreateAHero_Shield", lambda m: B.shield_round(m, A), "Shield of the Mark",
     "Rohan's golden sun-wheel on green, with a great domed boss.", "serious", None),
    ("SKHWSM_WSWORD", "CreateAHero_Weapon", lambda m: B.sword(m, A, length=11.8, guard=1.3, droop=-.2, pommel=T.GOLD,
                                                               guard_tag=T.GOLD, horse=True), "Sword of the Rohirrim",
     "A broad blade with a gilded guard and a horse's-head pommel.", "serious", None),
    ("SKHWSM_FCHEESE", "CreateAHero_Helmet", F.crown_cheese, "Crown of Cheese", "Fit for a queen.", "fun", None),
    ("SKHWSM_FUMB", "CreateAHero_Helmet", F.umbrella, "Tiny Umbrella", "For the rains of Rohan.", "fun", None),
    ("SKHWSM_HEORLP", "CreateAHero_Helmet", Hm.helm_eorl, "Helm of the Eorlingas, Pink Plume", "Riders of Rohan, but fabulous.",
     "serious", PINK_PLUME),
    ("SKHWSM_FPINK", "CreateAHero_ShoulderPlates", lambda m: F.cape_pink(m, A), "Pink Cape", "Bright pink, with a bow.",
     "fun", None),
    ("SKHWSM_FRAINB", "CreateAHero_ShoulderPlates", lambda m: B.cloak(m, A, T.F_RAINBOW, T.F_GOLD, T.F_FLUFF, clasp=T.F_GOLD,
                                                                      clasp_gem=T.F_PINKGEM), "Rainbow Cloak",
     "Every colour at once.", "fun", None),
    ("SKHWSM_FPIZZA", "CreateAHero_Shield", lambda m: F.shield_pizza(m, A), "Pizza Shield", "Extra cheese.", "fun", None),
    ("SKHWSM_FLEG", "CreateAHero_Weapon", lambda m: F.turkey_leg(m, A), "Turkey Leg", "Fights as a sword of the West.",
     "fun", None),
]
PARTS = C.name_parts(C.wrapped(sys.modules[__name__], ENTRIES), (48, 49))
budget = C.budget_fn({n: C.CLOAK for n in ("SKHWSM_SPCLOAK", "SKHWSM_FPINK", "SKHWSM_FRAINB")})
# every part rides the hero's bones in models of our own (assets/cah/kit/attach.py, docs/CAH.md); EA's
# models are not copied. Staged with python3 -m sagekit.units.cah --stage.
ATTACH, ATTACH_STEM = [p[0] for p in PARTS], "SKSM"

# the overview (python3 -m assets.cah.kit.render men_sm)
RENDER = {"body": {"chhw_sm_u_skn": "CHHW_SM", "chhw_sm_c_skn": "CHHW_SM", "chhw_sm_m_skn": "CHHW_SM"},
          "extra": {"chhw_sm_m_skn": ["HORSE"]},  # review renders: the horse
          "head_model": "chhw_sm_c_skn", "game_model": "chhw_sm_u_skn",
          "ea_heads": ["HLMT_00", "HLMT_01", "HLMT_02", "HLMT_05"],
          "kits": [("EA KIT", ["HLMT_05", "SLDR_05", "GNLT_04", "BOOT_04", "SHLD_01", "SWRD_05"], True),
                   ("ROHAN", ["SKHWSM_HEORL", "SKHWSM_SPCLOAK", "SKHWSM_SHSUN", "SKHWSM_WSWORD", "GNLT_04", "BOOT_04"], False),
                   ("GOLDEN HALL", ["SKHWSM_HGUARD", "SKHWSM_SPMARK", "SKHWSM_SHSUN", "SKHWSM_WSWORD", "GNLT_05", "BOOT_05"], False),
                   ("PINK", ["SKHWSM_HEORLP", "SKHWSM_FPINK", "SKHWSM_FPIZZA", "SKHWSM_FLEG", "GNLT_04", "BOOT_04"], False),
                   ("RAINBOW", ["SKHWSM_FCHEESE", "SKHWSM_FRAINB", "SKHWSM_FPIZZA", "SKHWSM_FLEG", "GNLT_05", "BOOT_05"], False)],
          "colours": [(150, 120, 60), (40, 84, 40), (70, 140, 90)],
          "anims": {"chhw_sm_u_skl": "chhw_sm_u_idla", "chhw_sm_c_skl": "chhw_sm_c_atnb", "chhw_sm_m_skl": "chhw_sm_m_idla"}}
