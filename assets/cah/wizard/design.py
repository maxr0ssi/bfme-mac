"""The cah pack's Wizards (Wanderer, Avatar, Hermit; one skeleton, so every part fits all three):
the Istari's hats (the Grey Pilgrim's, the White Council's, Radagast's with its nest, the Blue
Wizards' cowl), a travelling cloak and the Blue Wizards' starred mantle, a rune-carved staff; and
the fun choices (a pink hat, a star-spangled hat, the cheese crown and tiny umbrella the Men wear,
a glitter-trimmed cloak, a pink cape, a giant lollipop).

Drawn in CHWZ_YW_U_SKN's rest space. The creation-screen models (CHWZ_*_C_SKN) have their own
skeleton with the body in the same place and the staff in the other hand: hats and cloaks go in as
drawn, the staff by an exact fit of EA's STFF_05 matched by UV (assets/cah/men_cg/fit.py).

    python3 -m assets.cah.wizard.build
    python3 -m assets.cah.kit.render wizard
"""
import sys

from ..men_cg import common as C
from ..men_cg import fun as MF
from . import hats as Z
from . import paint as W

NAME, CLASS_FILE = "wizard", "wizard"
SUBCLASSES = [{"index": 0, "name": "Wanderer", "models": ["CHWZ_YW_U_SKN", "CHWZ_YW_C_SKN"]},
              {"index": 1, "name": "Avatar", "models": ["CHWZ_AV_U_SKN", "CHWZ_AV_C_SKN"]},
              {"index": 2, "name": "Hermit", "models": ["CHWZ_HR_U_SKN", "CHWZ_HR_C_SKN"]}]
MODELS = {"CHWZ_YW_U_SKN": "SKWZ_YW_U_SKN", "CHWZ_YW_C_SKN": "SKWZ_YW_C_SKN", "CHWZ_AV_U_SKN": "SKWZ_AV_U_SKN",
          "CHWZ_AV_C_SKN": "SKWZ_AV_C_SKN", "CHWZ_HR_U_SKN": "SKWZ_HR_U_SKN", "CHWZ_HR_C_SKN": "SKWZ_HR_C_SKN"}
SKELETONS = {"chwz_yw_u_skn": "chwz_yw_u_skl", "chwz_yw_c_skn": "chwz_yw_c_skl", "chwz_av_u_skn": "chwz_yw_u_skl",
             "chwz_av_c_skn": "chwz_yw_c_skl", "chwz_hr_u_skn": "chwz_yw_u_skl", "chwz_hr_c_skn": "chwz_yw_c_skl"}
KIND = {m: m[8] for m in SKELETONS}
DESIGN = "chwz_yw_u_skn"
EXPECTED = {
    "chwz_yw_u_skn": "14a523d73c863b75c445427feff7b67c2a49bc08485769f7fb8d0dc81a117fb1",
    "chwz_av_u_skn": "9cc58575f3ccb71855211a126b41ad8f66a992472e89278680975697bc5627a5",
    "chwz_hr_u_skn": "9012e3e2dcdc0acb060d583648806d1ad263ee5c6afda2b4193f2df0e73aca81",
    "chwz_yw_c_skn": "d04c9dbf3349c97e9a7f786784bbc38519ffb3abd4ac9a5bec389e620dcd0cb8",
    "chwz_av_c_skn": "412012760edd57df48b11ffed86a7f8cfce2bfece7add49ad66f92f9fb564945",
    "chwz_hr_c_skn": "468ca4df4644e916829e4c0beed063a790fa4706ed22ec13969156f7ceea5e7f",
    "chwz_yw_u_skl": "2817499e7f3a40352b0cb3be3f49af08d0fb4ee2e3518a33ecfbb781c7b27988",
    "chwz_yw_c_skl": "f69b4548ac6cb6de09bd56c95d90af046b57542d40597470360dc97f3bccc75b",
    "chwz_yw_u_atka": "91fd23d6586dbbafd253a23f15fa4ae3f0cec22cbfa2b04cdc7e93d30e5a7aa6",
    "chwz_yw_u_idla": "9c9826ea801bc84db231aa69c87431d50703594e9250df231a1d65e3345b1786",
    "chwz_yw_c_wpna": "fd95585c37417a3c0e0167a25209b0cd6e372c3b2aac516b9dc95d2689ff6a92",
    "chwz_yw_c_atnb": "f9fc1f9ccd825824dba1dab8174cffec28a4f294e0a9bef74f91993a090123b6",
}
CHECK_ANIM = {"chwz_yw_u_skl": "chwz_yw_u_atka", "chwz_yw_c_skl": "chwz_yw_c_wpna"}
FIT_REFS = ()
OWN_SPACE = ("chwz_yw_c_skn", "chwz_av_c_skn", "chwz_hr_c_skn")    # placed by men_cg/fit.wrap, per group
REFS = {"CreateAHero_Weapon": ("STFF_05",)}                       # the rest: the same rest pose
WEAPON_REF, DESIGN_HAND = "STFF_05", "HAND"
BODY = {"HEAD": "B_HEAD", "SPINE": "BAT_SPINE2", "UARM_L": "BAT_UARML", "UARM_R": "BAT_UARMR"}
PER_SKELETON = {"chwz_yw_u_skl": BODY, "chwz_yw_c_skl": BODY}
HAND = {"chwz_yw_u_skl": "B_HAND_L", "chwz_yw_c_skl": "B_HAND_R"}  # where EA's STFF_05 rides
BONES = C.bones({k: dict(v, HAND=HAND[k]) for k, v in PER_SKELETON.items()})
TEMPLATE, TEMPLATE_TEX = "HLMT_08", "CHWZ_WZ_OF3D_HLMT_08.tga"
SHEETS = {"serious": "SKCAH_WZGEAR.tga", "fun": "SKCAH_WZFUN.tga"}
MASKS = {"SKCAH_WZGEAR.tga": "HC_SKCAH_WZGEAR.tga", "SKCAH_WZFUN.tga": "HC_SKCAH_WZFUN.tga"}
HEAD_SEAT = C.seat(0.12, 21.85, .84, kz=1.0)                       # canonical head (men_cg/helms.py) -> a wizard's
WEAPON_LIKE, WEAPON_NOTE = "WEAPONSET_CREATE_A_HERO_WS_40", "EA's wizard staffs"

# CHWZ_YW_U_SKN's anatomy (rest space: +X front, +Y left, +Z up)
ANATOMY = dict(
    pauldron=1.3, cloak_cx=0.0, fold=.15, cloak_saddle=0,
    cloak=[(3.6, 3.7, 5.5), (3.35, 3.55, 7.8), (3.05, 3.4, 10.0), (2.75, 3.25, 12.2), (2.45, 3.1, 14.2), (2.3, 3.05, 15.8),
           (2.2, 3.0, 17.2), (2.05, 2.9, 18.3), (1.8, 2.65, 19.1), (1.5, 2.35, 19.6)],
    collar=(-0.15, 1.45, 1.95, 19.45), collar_r=.3, clasp=(1.05, 1.25, 18.9),
    staff=((0.163, -12.121, 5.077), (.017, -.629, -.777), (-.999, .023, -.04)), staff_span=(-18.19, 5.16, -6.49))
A = ANATOMY
PINK = {W.GREYFELT: W.PINKFELT, W.BAND: W.HOTPINK}
SPANGLED = {W.WHITEFELT: W.SPANGLE, W.RUNES: W.GOLD, W.WHITE: W.GOLD, W.SILVER: W.GOLD}

ENTRIES = [   # (sub-object, group, design, name, description, sheet, remap) in APPEND order
    ("SKWZ_HGREY", "CreateAHero_Helmet", Z.hat_grey, "Grey Pilgrim's Hat",
     "A tall grey hat, its point bent back, with a wide drooping brim.", "serious", None),
    ("SKWZ_HWHITE", "CreateAHero_Helmet", Z.hat_white, "Hat of the White Council",
     "A tall white cone with a silver rune band and a white stone.", "serious", None),
    ("SKWZ_HBROWN", "CreateAHero_Helmet", Z.hat_brown, "Radagast's Hat",
     "Battered brown felt, feathers in the band, and a bird's nest on top.", "serious", None),
    ("SKWZ_HBLUE", "CreateAHero_Helmet", Z.hat_blue, "Cowl of the Blue Wizards",
     "A deep blue hood rising to a point, a star-sapphire on the brow.", "serious", None),
    ("SKWZ_SPCLOAK", "CreateAHero_ShoulderPlates", lambda m: Z.cloak_travel(m, A), "Travelling Cloak",
     "A long cloak with its hood thrown back, fastened with a brass clasp.", "serious", None),
    ("SKWZ_SPSTARS", "CreateAHero_ShoulderPlates", lambda m: Z.cloak_stars(m, A), "Mantle of the Ithryn Luin",
     "A cloak with a hem of silver stars.", "serious", None),
    ("SKWZ_WRUNE", "CreateAHero_Weapon", lambda m: Z.staff_rune(m, A), "Rune-carved Staff",
     "Gnarled wood, a silver rune band and a crystal held in carved prongs.", "serious", None),
    ("SKWZ_FPINKHAT", "CreateAHero_Helmet", Z.hat_grey, "Pink Wizard Hat", "Sparkly.", "serious", PINK),
    ("SKWZ_FSTARHAT", "CreateAHero_Helmet", Z.hat_white, "Star-spangled Hat", "A proper wizard's hat.", "serious", SPANGLED),
    ("SKWZ_FCHEESE", "CreateAHero_Helmet", MF.crown_cheese, "Crown of Cheese", "The Istari of Cheddar.", "fun", None),
    ("SKWZ_FUMB", "CreateAHero_Helmet", MF.umbrella, "Tiny Umbrella", "A wizard is never wet.", "fun", None),
    ("SKWZ_FGLITTER", "CreateAHero_ShoulderPlates", lambda m: Z.cloak_glitter(m, A), "Sparkly Rainbow Cloak",
     "Gold stars and a rainbow glitter trim.", "fun", None),
    ("SKWZ_FPINK", "CreateAHero_ShoulderPlates", lambda m: MF.cape_pink(m, A), "Pink Cape", "Bright pink, with a bow.",
     "fun", None),
    ("SKWZ_FLOLLY", "CreateAHero_Weapon", lambda m: Z.staff_lolly(m, A), "Giant Lollipop", "Fights as a wizard's staff.",
     "fun", None),
]
PARTS = C.name_parts(C.wrapped(sys.modules[__name__], ENTRIES), (50, 51))
budget = C.budget_fn({n: C.CLOAK for n in ("SKWZ_SPCLOAK", "SKWZ_SPSTARS", "SKWZ_FGLITTER", "SKWZ_FPINK")})
# every part rides the hero's bones in models of our own (assets/cah/kit/attach.py, docs/CAH.md); EA's
# models are not copied. Staged with python3 -m sagekit.units.cah --stage.
ATTACH, ATTACH_STEM = [p[0] for p in PARTS], "SKWZ"

# the overview (python3 -m assets.cah.kit.render wizard)
RENDER = {"body": {"chwz_yw_u_skn": ["CHWZ_WD1", "YW_HEAD"], "chwz_yw_c_skn": ["CHWZ_WD1", "YW_HEAD"],
                   "chwz_av_u_skn": ["CHWZ_WD1", "AVATAR_HEAD"], "chwz_av_c_skn": ["CHWZ_WD1", "AVATAR_HEAD"],
                   "chwz_hr_u_skn": ["CHWZ_WD1", "HERMIT_HEAD"], "chwz_hr_c_skn": ["CHWZ_WD1", "HERMIT_HEAD"]},
          "head_model": "chwz_yw_c_skn", "game_model": "chwz_yw_u_skn",
          "ea_heads": ["HLMT_01", "HLMT_03", "HLMT_05", "HLMT_06"],
          "kits": [("EA KIT", ["HLMT_01", "SLDR_01", "STFF_05"], True),
                   ("GREY", ["SKWZ_HGREY", "SKWZ_SPCLOAK", "SKWZ_WRUNE"], False),
                   ("BROWN", ["SKWZ_HBROWN", "SKWZ_SPCLOAK", "SKWZ_WRUNE"], False),
                   ("BLUE", ["SKWZ_HBLUE", "SKWZ_SPSTARS", "SKWZ_WRUNE"], False),
                   ("PINK", ["SKWZ_FPINKHAT", "SKWZ_FPINK", "SKWZ_FLOLLY"], False),
                   ("SPARKLE", ["SKWZ_FSTARHAT", "SKWZ_FGLITTER", "SKWZ_FLOLLY"], False)],
          "colours": [(90, 70, 50), (96, 98, 104), (90, 150, 230)],
          "anims": {"chwz_yw_u_skl": "chwz_yw_u_idla", "chwz_yw_c_skl": "chwz_yw_c_atnb"}}
