"""The cah pack's Corrupted Men: more choices for both subclasses (0 and 1; EA's two Men of the
East and South on one skeleton). Serious parts follow Harad (brass, crimson, a turban and a mail
veil) and the Easterlings (black lacquer lamellar and gold), with Mordor's helm and cloak for the
Black Numenorean; fun parts are fixed colours. Parts are drawn on each model's measured anatomy
(assets/cah/evil/anatomy.py; OWN_SPACE).

    python3 -m assets.cah.corruptedman.build [--skip-paint]
    python3 -m assets.cah.evil.render corruptedman
"""
import sys

from ..evil import arms, body, fun, helms
from ..evil import spec as E
from ..evil.paint import paint as _paint

NAME, CLASS_FILE = "corruptedman", "corruptedman"
SUBCLASSES = [{"index": 0, "name": "Corrupted Man 1", "models": ["CHCM_CM_U_SKN", "CHCM_CM_C_SKN"]},
              {"index": 1, "name": "Corrupted Man 2", "models": ["CHCM_FN_U_SKN", "CHCM_FN_C_SKN"]}]
MODELS = {"CHCM_CM_U_SKN": "SKCM_CM_U_SKN", "CHCM_CM_C_SKN": "SKCM_CM_C_SKN",
          "CHCM_FN_U_SKN": "SKCM_FN_U_SKN", "CHCM_FN_C_SKN": "SKCM_FN_C_SKN"}
SKELETONS = {"chcm_cm_u_skn": "chcm_cm_u_skl", "chcm_cm_c_skn": "chcm_cm_c_skl",
             "chcm_fn_u_skn": "chcm_cm_u_skl", "chcm_fn_c_skn": "chcm_cm_c_skl"}
KIND = {"chcm_cm_u_skn": "u", "chcm_cm_c_skn": "c", "chcm_fn_u_skn": "u", "chcm_fn_c_skn": "c"}
DESIGN = "chcm_cm_u_skn"
OWN_SPACE = tuple(SKELETONS)
EXPECTED = {
    "chcm_cm_u_skn": "b192a9e6b38d0c33e800910c71b31a051c685a561ef198a7b631bf00457e7993",
    "chcm_cm_c_skn": "045e1a182d9ea51f81e230692f28daba9988717fba4795e3d0962f1f5779b582",
    "chcm_fn_u_skn": "0ab9b064e5a07b7ec929f20d2577463bc8584eb1d32e89493ef28eccd3a0e308",
    "chcm_fn_c_skn": "69008293cbc26187fcc476190b89f3e7d1eb956f5de86f784487f30b9c88996f",
    "chcm_cm_u_skl": "96c9091d3647548f8ba319ace3bdee333df79feb01415c1293b880896c84dd90",
    "chcm_cm_c_skl": "a1a32ba6166dbb92c45450c3a30422b491419c12639661a6303176fdb3045d26",
    "chcm_cm_u_atka": "055cac4fefd3e555cd03517b4019a84ebcdd8d7092538fd0d3ade0e55acacfe2",
    "chcm_cm_c_wpna": "bf0b0428c2d3441c48a4468f5842919ac4540bfda1b25beb96cd36192315d20d",
    "chcm_cm_u_idla": "f5eb7ef600df414202761624bd97e37875086396f2bd877023839697e9cb4065",
    "chcm_cm_c_atnb": "666e944280588db50e4e1c127d30d5344814438862dd1e58b11e6daea14bd1f0",
}
CHECK_ANIM = {"chcm_cm_u_skl": "chcm_cm_u_atka", "chcm_cm_c_skl": "chcm_cm_c_wpna"}
FIT_REFS, WEAPON_REF, DESIGN_HAND = (), None, "-"
HAND = {s: "-" for s in SKELETONS.values()}
TEMPLATE = {m: ("HLMT_08", "CHCM_CM_OF3D_HLMT_08.tga") for m in SKELETONS}
SHEETS = {"serious": "SKCAH_CMGEAR.tga", "fun": "SKCAH_CMFUN.tga"}
MASKS = {"SKCAH_CMGEAR.tga": "HC_SKCAH_CMGEAR.tga", "SKCAH_CMFUN.tga": "HC_SKCAH_CMFUN.tga"}
BONES = E.BONES
WEAPON_LIKE, WEAPON_NOTE = "WEAPONSET_CREATE_A_HERO_WS_25", "EA's corrupted men's swords (WS_25)"
_MAN = {"weapon": ["SWRD_05"], "shoulder": "SLDR_02", "tweak": {}}
E.register(sys.modules[__name__], {m: _MAN for m in SKELETONS})
BOTH = [0, 1]
H, SH, SD, W = "CreateAHero_Helmet", "CreateAHero_ShoulderPlates", "CreateAHero_Shield", "CreateAHero_Weapon"
PARTS = E.parts("CMEN", [
    ("SKCMN_HLMT_HAR", H, helms.helm_harad, "Helm of the Haradrim", "A brass spire over a crimson turban and a mail veil.", "serious", None, BOTH),
    ("SKCMN_HLMT_EAS", H, helms.helm_easterling, "Easterling Lamellar Helm", "Black lacquer laced in gold, behind a gold mask.", "serious", None, BOTH),
    ("SKCMN_HLMT_MOR", H, helms.helm_mordor, "Helm of the Dark Tower", "Black iron under a crown of hooked spikes; the Eye on the brow.", "serious", None, BOTH),
    ("SKCMN_FUN_TOP", H, fun.hat_top, "Top Hat and Monocle", "Frightfully civilised.", "fun", None, BOTH),
    ("SKCMN_FUN_PARTY", H, fun.hat_party, "Party Hat", "Festivities in the East.", "fun", None, BOTH),
    ("SKCMN_FUN_PINK", H, helms.helm_mordor, "Pink Spiked Helm", "The Dark Tower, in hot pink.", "serious", fun.PINK_SPIKED, BOTH),
    ("SKCMN_SLDR_HAR", SH, body.pauldrons_harad, "Haradrim Shoulder Guards", "Engraved brass and a crimson sash.", "serious", None, BOTH),
    ("SKCMN_SLDR_EAS", SH, body.pauldrons_easterling, "Easterling Lamellar", "Three tiers of lacquered plates laced in gold.", "serious", None, BOTH),
    ("SKCMN_CAPE_MOR", SH, body.cloak_mordor, "Mordor War Cloak", "A ragged cloak with spiked iron clasps.", "serious", None, BOTH),
    ("SKCMN_FUN_BANNR", SH, body.cape_banner, "Rainbow War Banner", "Carried with pride.", "fun", None, BOTH),
    ("SKCMN_WPN_SCIM", W, arms.scimitar_harad, "Haradrim Scimitar", "Fights as EA's corrupted men's swords.", "serious", None, BOTH),
    ("SKCMN_FUN_LOLLY", W, arms.lollipop, "Giant Lollipop", "Sticky. Fights as a sword.", "fun", None, BOTH),
], range(60, 62))
budget = E.budget_of({"SKCMN_CAPE_MOR", "SKCMN_FUN_BANNR"})


def paint(work):
    return _paint(work, "skcah_cmgear", "skcah_cmfun")


_HL = [p[0] for p in PARTS if p[1] == H]
_EA = ["GNLT_01", "BOOT_01"]
RENDER = {"body": {"chcm_cm_u_skn": "CHCM_CM_H", "chcm_cm_c_skn": "CHCM_CM", "chcm_fn_u_skn": "CHCM_CM_H",
                   "chcm_fn_c_skn": "CHCM_FN"},
          "colours": [(70, 62, 52), (150, 28, 22), (210, 160, 60)],
          "anims": {"chcm_cm_u_skl": "chcm_cm_u_idla", "chcm_cm_c_skl": "chcm_cm_c_atnb"},
          "heads": ([("chcm_cm_c_skn", "EA HLMT_08", ["HLMT_08", "HLMT_09"], True), ("chcm_cm_c_skn", "EA HLMT_02", ["HLMT_02"], True)] +
                    [("chcm_cm_c_skn", h[6:], [h], False) for h in _HL] +
                    [("chcm_fn_c_skn", "HARADRIM " + h[6:], [h], False) for h in _HL[:3]]),
          "kits": [("chcm_cm_c_skn", "EA EASTERLING", ["HLMT_08", "HLMT_09", "SLDR_03", "SWRD_05"] + _EA, True),
                   ("chcm_cm_c_skn", "EASTERLING", ["SKCMN_HLMT_EAS", "SKCMN_SLDR_EAS", "SKCMN_WPN_SCIM"] + _EA, False),
                   ("chcm_fn_c_skn", "HARADRIM", ["SKCMN_HLMT_HAR", "SKCMN_SLDR_HAR", "SKCMN_WPN_SCIM"] + _EA, False),
                   ("chcm_fn_c_skn", "BLACK NUMENOREAN", ["SKCMN_HLMT_MOR", "SKCMN_CAPE_MOR", "SKCMN_WPN_SCIM"] + _EA, False),
                   ("chcm_cm_c_skn", "TOP HAT", ["SKCMN_FUN_TOP", "SKCMN_FUN_BANNR", "SKCMN_FUN_LOLLY"] + _EA, False),
                   ("chcm_fn_c_skn", "PINK", ["SKCMN_FUN_PINK", "SKCMN_CAPE_MOR", "SKCMN_FUN_LOLLY"] + _EA, False)],
          "close": [("chcm_cm_c_skn", "SCIMITAR", ["SKCMN_WPN_SCIM"] + _EA, False, ["SKCMN_WPN_SCIM"], 0.9, -30),
                    ("chcm_cm_c_skn", "LOLLIPOP", ["SKCMN_FUN_LOLLY"] + _EA, False, ["SKCMN_FUN_LOLLY"], 0.9, -30),
                    ("chcm_fn_c_skn", "HARAD GUARDS", ["SKCMN_SLDR_HAR"] + _EA, False, ["SKCMN_SLDR_HAR"], 0.7),
                    ("chcm_cm_c_skn", "LAMELLAR", ["SKCMN_SLDR_EAS"] + _EA, False, ["SKCMN_SLDR_EAS"], 0.7),
                    ("chcm_cm_c_skn", "BANNER", ["SKCMN_FUN_BANNR"] + _EA, False, ["SKCMN_FUN_BANNR"], 1.1, 200)],
          "game": [("chcm_cm_u_skn", "EA EASTERLING", ["HLMT_08", "HLMT_09", "SLDR_03", "SWRD_05"] + _EA, True),
                   ("chcm_cm_u_skn", "EASTERLING", ["SKCMN_HLMT_EAS", "SKCMN_SLDR_EAS", "SKCMN_WPN_SCIM"] + _EA, False),
                   ("chcm_fn_u_skn", "HARADRIM", ["SKCMN_HLMT_HAR", "SKCMN_SLDR_HAR", "SKCMN_WPN_SCIM"] + _EA, False),
                   ("chcm_fn_u_skn", "TOP HAT", ["SKCMN_FUN_TOP", "SKCMN_FUN_BANNR", "SKCMN_FUN_LOLLY"] + _EA, False)]}
