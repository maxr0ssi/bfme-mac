"""The cah pack's Men of the West, Captain of Gondor (subclass 0): Gondor's helms (the Citadel
Guard, the winged helm of the kings, an Ithilien hood), Dol Amroth's swan helm, Arnor's star crown
and a Rohirrim helm; Gondor's pauldrons, the Mantle of the White Tree, the tower shield and sword;
and the fun choices. The Shieldmaiden (assets/cah/men_sm) shares these designs on her own body.

The parts are drawn in CHHW_CG_U_SKN's rest space and mapped into the creation-screen model
(CHHW_CG_C_SKN) and the mounted one (CHHW_MW_M_SKN, its own skeleton) by exact fits of EA's
parts both carry, matched by UV (fit.py): helmets and shoulders by HLMT_01, shields by
SHLD_01, the sword by SWRD_05.

    python3 -m assets.cah.men_cg.build      # EA sources, sheets, models, INI fragment, checks
    python3 -m assets.cah.kit.render men_cg
"""
import sys

from . import body as B
from . import common as C
from . import fun as F
from . import helms as Hm
from . import paint as T

NAME, CLASS_FILE = "men_cg", "menofthewest"
SUBCLASSES = [{"index": 0, "name": "Captain Of Gondor", "models": ["CHHW_CG_U_SKN", "CHHW_CG_C_SKN", "CHHW_MW_M_SKN"]}]
MODELS = {"CHHW_CG_U_SKN": "SKHW_CG_U_SKN", "CHHW_CG_C_SKN": "SKHW_CG_C_SKN", "CHHW_MW_M_SKN": "SKHW_MW_M_SKN"}
SKELETONS = {"chhw_cg_u_skn": "chhw_cg_u_skl", "chhw_cg_c_skn": "chhw_cg_c_skl", "chhw_mw_m_skn": "chhw_mw_m_skl"}
KIND = {"chhw_cg_u_skn": "u", "chhw_cg_c_skn": "c", "chhw_mw_m_skn": "m"}
DESIGN = "chhw_cg_u_skn"
EXPECTED = {
    "chhw_cg_u_skn": "6a25d25220773b9f2c7499e1e57b0789d341d81dc27713eb13ceafc99fae1f24",
    "chhw_cg_c_skn": "647437f5e0a2c9af4265ca50bbbbb5dc4bea7ffbabfec1e264b27d4ec8be9f9d",
    "chhw_mw_m_skn": "ef7b1bdc6e79a91d945e6984ad7ea680c6ee07e8c03b5d9d866bbca587b9d1b5",
    "chhw_cg_u_skl": "0f58ab1eec84c4831ef97bbd8bb09d6394ed6c747be277e792d4e9116346a5ef",
    "chhw_cg_c_skl": "349cfbada74c51919680c35b1a10e54ead61b0e48ee9ba210d49394e5d6f1c8a",
    "chhw_mw_m_skl": "3e7d2a0daa567e9d35f3ef98c148cc2c0c7537cada343a03bbd2b19df4df9c93",
    "chhw_cg_u_atka": "a48a67845809c1bae99fd4d94d8be1722acf943b1db7c1211b8c34507f1399be",
    "chhw_cg_u_idla": "513d217d19f3e9723252c15f9e7feb393a37fa086c0428f9c32872d4be16c57f",
    "chhw_cg_c_wpna": "75b77b268c55a861c5cefa75bbca39bef000877a401c54e79db8cff873dca714",
    "chhw_cg_c_atnb": "24a9624691c0ed9bb019517dc1ac9f2e74edab39c8fc4892b4f0c5931af91145",
    "chhw_mw_m_atka": "a00df3eae367c4eb02285a701c3ab0cf390f4513d2b25512de163a68115a18c1",
    "chhw_mw_m_idla": "2f20660bedded8c3c26a46de533984c6f4e2e0d9578bb449333b536f2dc0aaa3",
}
CHECK_ANIM = {"chhw_cg_u_skl": "chhw_cg_u_atka", "chhw_cg_c_skl": "chhw_cg_c_wpna", "chhw_mw_m_skl": "chhw_mw_m_atka"}
FIT_REFS = ()
OWN_SPACE = ("chhw_cg_c_skn", "chhw_mw_m_skn")                # placed by fit.wrap, per group
REFS = {"CreateAHero_Helmet": ("HLMT_01",), "CreateAHero_ShoulderPlates": ("HLMT_01",), "CreateAHero_Shield": ("SHLD_01",),
        "CreateAHero_Weapon": ("SWRD_05",)}
WEAPON_REF, DESIGN_HAND = "SWRD_05", "HAND"
PER_SKELETON = {
    "chhw_cg_u_skl": {"HEAD": "BAT_HEAD", "SPINE": "BAT_RIBS", "UARM_L": "BAT_UARML", "UARM_R": "BAT_UARMR", "SHIELD": "BAT_FARML"},
    "chhw_cg_c_skl": {"HEAD": "B_HEAD", "SPINE": "BAT_SPINE2", "UARM_L": "BAT_UARML", "UARM_R": "BAT_UARMR", "SHIELD": "BAT_FARML"},
    "chhw_mw_m_skl": {"HEAD": "BAT_HEAD", "SPINE": "BAT_SPINE2", "UARM_L": "BAT_UARML", "UARM_R": "BAT_UARMR", "SHIELD": "B_HAND_L"}}
HAND = {"chhw_cg_u_skl": "B_HAND_R", "chhw_cg_c_skl": "B_HAND_R", "chhw_mw_m_skl": "B_HANDR"}   # where EA's SWRD_05 rides
BONES = C.bones({k: dict(v, HAND=HAND[k]) for k, v in PER_SKELETON.items()})
TEMPLATE, TEMPLATE_TEX = "HLMT_01", "CHHW_SWN_GEAR_01.tga"      # in all three models
SHEETS = {"serious": "SKCAH_HWCGGEAR.tga", "fun": "SKCAH_HWCGFUN.tga"}
MASKS = {"SKCAH_HWCGGEAR.tga": "HC_SKCAH_HWCGGEAR.tga", "SKCAH_HWCGFUN.tga": "HC_SKCAH_HWCGFUN.tga"}
HEAD_SEAT = C.seat(-0.22, 20.17, 1.03)                              # canonical head (helms.py) -> this head
WEAPON_LIKE, WEAPON_NOTE = "WEAPONSET_CREATE_A_HERO_WS_04", "EA's swords of the West"

# CHHW_CG_U_SKN's anatomy for body.py (rest space: +X front, +Y left, +Z up)
ANATOMY = dict(
    shoulder=(-0.75, 2.85, 17.55), up=(0.0, .5, .87), pauldron=1.45, arm=(-.04, .68, -.73),
    cloak_cx=-0.4, fold=.2, cloak_saddle=4,
    cloak=[(2.75, 3.35, 9.2), (2.6, 3.25, 10.4), (2.45, 3.15, 11.6), (2.32, 3.05, 12.8), (2.27, 3.0, 14.0), (2.27, 3.0, 15.2),
           (2.22, 2.95, 16.3), (2.08, 2.85, 17.3), (1.85, 2.7, 18.1), (1.58, 2.5, 18.6)],
    collar=(-0.35, 1.6, 2.15, 18.5), collar_r=.3, clasp=(0.85, 1.6, 18.0),
    shield=((0.04, 9.59, 11.23), (0.0, .882, .472), (1.0, 0.0, 0.0)), shield_size=(4.6, 2.9), shield_off=.45,
    grip=((0.0, -8.769, 10.574), (1.0, 0.0, 0.0), (0.0, .755, .655)), guard_at=.75)
A = ANATOMY
GOLD_PLATED = {T.MITHRIL: T.GOLDPLATE, T.WINGS: T.GILT}
PINK_PLUME = {T.HORSEHAIR: T.PINKHAIR}

ENTRIES = [   # (sub-object, group, design, name, description, sheet, remap) in APPEND order
    ("SKHWCG_HCIT", "CreateAHero_Helmet", Hm.helm_citadel, "Helm of the Citadel Guard",
     "The tall sable helm of the Tower Guard, with silver wings and a steel crest.", "serious", None),
    ("SKHWCG_HKING", "CreateAHero_Helmet", Hm.helm_king, "Winged Helm of the Kings",
     "White steel and seabird wings, seven gems and a star on the brow.", "serious", None),
    ("SKHWCG_HITH", "CreateAHero_Helmet", Hm.hood_ithilien, "Ithilien Ranger's Hood",
     "A deep forest hood and a mask drawn up to the eyes.", "serious", None),
    ("SKHWCG_HSWAN", "CreateAHero_Helmet", Hm.helm_swan, "Swan Helm of Dol Amroth",
     "Silver on sea-blue, a white swan rising from the crown.", "serious", None),
    ("SKHWCG_HARN", "CreateAHero_Helmet", Hm.helm_arnor, "Star Crown of Arnor",
     "A fluted mithril helm crowned with seven stars, the Elendilmir on the brow.", "serious", None),
    ("SKHWCG_HEORL", "CreateAHero_Helmet", Hm.helm_eorl, "Helm of the Eorlingas",
     "Gilded spangen, a golden horse on the brow and a long horsehair tail.", "serious", None),
    ("SKHWCG_SPGN", "CreateAHero_ShoulderPlates", lambda m: B.pauldrons(m, A), "Pauldrons of Gondor",
     "Bright steel shoulder domes edged in gold, with riveted lames.", "serious", None),
    ("SKHWCG_SPTREE", "CreateAHero_ShoulderPlates", lambda m: B.mantle_tree(m, A), "Mantle of the White Tree",
     "A sable cloak bearing the White Tree, with a fur collar.", "serious", None),
    ("SKHWCG_SHTWR", "CreateAHero_Shield", lambda m: B.shield_gondor(m, A), "Tower Shield of Minas Tirith",
     "The White Tree beneath seven stars and the crown.", "serious", None),
    ("SKHWCG_WSWORD", "CreateAHero_Weapon", lambda m: B.sword(m, A), "Sword of Gondor",
     "A long fullered blade with a swept guard and a sapphire pommel.", "serious", None),
    ("SKHWCG_FCHEESE", "CreateAHero_Helmet", F.crown_cheese, "Crown of Cheese", "A king needs a crown. Any crown.", "fun", None),
    ("SKHWCG_FUMB", "CreateAHero_Helmet", F.umbrella, "Tiny Umbrella", "It never rains in Minas Tirith.", "fun", None),
    ("SKHWCG_HKINGG", "CreateAHero_Helmet", Hm.helm_king, "Winged Helm, Gold-plated", "Solid gold. Well, gold-ish.",
     "serious", GOLD_PLATED),
    ("SKHWCG_HEORLP", "CreateAHero_Helmet", Hm.helm_eorl, "Helm of the Eorlingas, Pink Plume", "Riders of Rohan, but fabulous.",
     "serious", PINK_PLUME),
    ("SKHWCG_FPINK", "CreateAHero_ShoulderPlates", lambda m: F.cape_pink(m, A), "Pink Cape", "Bright pink, with a bow.",
     "fun", None),
    ("SKHWCG_FRAINB", "CreateAHero_ShoulderPlates", lambda m: B.cloak(m, A, T.F_RAINBOW, T.F_GOLD, T.F_FLUFF, clasp=T.F_GOLD,
                                                                      clasp_gem=T.F_PINKGEM), "Rainbow Cloak",
     "Every colour at once.", "fun", None),
    ("SKHWCG_FPIZZA", "CreateAHero_Shield", lambda m: F.shield_pizza(m, A), "Pizza Shield", "Extra cheese.", "fun", None),
    ("SKHWCG_FPAN", "CreateAHero_Weapon", lambda m: F.frying_pan(m, A), "Frying Pan", "Fights as a sword of the West.",
     "fun", None),
]
PARTS = C.name_parts(C.wrapped(sys.modules[__name__], ENTRIES), (46, 47))
budget = C.budget_fn({n: C.CLOAK for n in ("SKHWCG_SPTREE", "SKHWCG_FPINK", "SKHWCG_FRAINB")})
# every part rides the hero's bones in models of our own (assets/cah/kit/attach.py, docs/CAH.md); EA's
# models are not copied. Staged with python3 -m sagekit.units.cah --stage.
ATTACH, ATTACH_STEM = [p[0] for p in PARTS], "SKCG"

# the overview (python3 -m assets.cah.kit.render men_cg)
RENDER = {"body": {"chhw_cg_u_skn": "CHHW_SMNL", "chhw_cg_c_skn": "CHHW_SMN", "chhw_mw_m_skn": "CHHW_SMNL"},
          "extra": {"chhw_mw_m_skn": ["GUHORSE"]},  # review renders: the horse
          "head_model": "chhw_cg_c_skn", "game_model": "chhw_cg_u_skn",
          "ea_heads": ["HLMT_01", "HLMT_02", "HLMT_05", "HLMT_06"],
          "kits": [("EA KIT", ["HLMT_06", "SLDR_04", "GNLT_04", "BOOT_04", "SHLD_01", "SWRD_05"], True),
                   ("GONDOR", ["SKHWCG_HCIT", "SKHWCG_SPGN", "SKHWCG_SHTWR", "SKHWCG_WSWORD", "GNLT_04", "BOOT_04"], False),
                   ("WHITE TREE", ["SKHWCG_HKING", "SKHWCG_SPTREE", "SKHWCG_SHTWR", "SKHWCG_WSWORD", "GNLT_05", "BOOT_05"], False),
                   ("PINK", ["SKHWCG_FCHEESE", "SKHWCG_FPINK", "SKHWCG_FPIZZA", "SKHWCG_FPAN", "GNLT_04", "BOOT_04"], False),
                   ("RAINBOW", ["SKHWCG_FUMB", "SKHWCG_FRAINB", "SKHWCG_FPIZZA", "SKHWCG_FPAN", "GNLT_05", "BOOT_05"], False)],
          "colours": [(52, 74, 40), (30, 34, 44), (70, 110, 200)],
          "anims": {"chhw_cg_u_skl": "chhw_cg_u_idla", "chhw_cg_c_skl": "chhw_cg_c_atnb", "chhw_mw_m_skl": "chhw_mw_m_idla"}}
