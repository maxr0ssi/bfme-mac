"""The Archers' choices, in APPEND order (saved heroes index the rows: never reorder or remove),
shared by both archer folders: each folder names them with its own stem and weapon flags.

(code, group, design, name, description, sheet, tile remap); the code makes the sub-object
SK<STEM>_<code> (15 characters at most)."""
from . import fun as F, serious as S
from .place import Space, wrap

HLM, SH, SD, WP = "CreateAHero_Helmet", "CreateAHero_ShoulderPlates", "CreateAHero_Shield", "CreateAHero_Weapon"
CATALOGUE = [
    ("HOODLO", HLM, S.hood_lorien, "Hood of Lorien", "A deep elven hood with a mallorn vine, two gold leaves at the throat.",
     "serious", None, "head"),
    ("CIRCRV", HLM, S.circlet_rivendell, "Circlet of Rivendell", "Blue-silver, a crystal set in a mithril leaf.",
     "serious", None, "head"),
    ("HELMRV", HLM, S.helm_rivendell, "Winged Helm of Rivendell", "Mithril wings swept back from the temples.",
     "serious", None, "head"),
    ("CIRCMW", HLM, S.circlet_mirkwood, "Antlered Circlet of Mirkwood", "Dark wood and antler, autumn leaves at the brow.",
     "serious", None, "head"),
    ("HELMNL", HLM, S.helm_noldor, "Tall Helm of the Noldor", "A fluted golden helm with a tall swept crest.",
     "serious", None, "head"),
    ("HOODRG", HLM, S.hood_ranger, "Ranger's Hood", "A deep camo cowl and the star of the Dunedain.", "serious", None, "head"),
    ("HOODPK", HLM, F.hood_pink, "Pink Hood", "Bubblegum pink, with a heart. Matches the pink cape.", "fun", F.PINK_SET, "head"),
    ("TIARA", HLM, F.tiara, "Sparkly Tiara", "Every point has a gem on it.", "fun", None, "head"),
    ("CATEARS", HLM, F.cat_ears, "Cat Ears", "Ginger, with pink insides.", "fun", None, "head"),
    ("FLOWERS", HLM, F.flower_crown, "Flower Crown", "Eleven flowers, all picked in Lothlorien.", "fun", None, "head"),
    ("UNICORN", HLM, F.unicorn, "Unicorn Horn", "Pearl, spiral, very pointy.", "fun", None, "head"),
    ("CLOAKLO", SH, S.cloak_lorien, "Cloak of Lorien", "A long elven cloak, pinned by two gold mallorn leaves.",
     "serious", None, "back"),
    ("CLOAKRG", SH, S.cloak_ranger, "Ranger's Cloak", "Green-brown camo of the North, the star of the Dunedain.",
     "serious", None, "back"),
    ("PAULMW", SH, S.pauldrons_mirkwood, "Mirkwood Leaf Pauldrons", "Layered leaves of green leather edged in gold.",
     "serious", None, "back"),
    ("CAPEPK", SH, F.cape_pink, "Pink Cape", "Bubblegum pink, white fluff, heart clasps. Matches the pink hood.",
     "fun", None, "back"),
    ("RAINBOW", SH, F.cloak_rainbow, "Rainbow Cloak", "Every colour at once.", "fun", None, "back"),
    ("SHLDLF", SD, S.shield_leaf, "Leaf Shield of Lorien", "A leaf-shaped shield with a gold mallorn leaf.",
     "serious", None, "arm"),
    ("KNIVES", SD, S.knives_galadhrim, "Long Knives of the Galadhrim", "Twin leaf-bladed knives, sheathed at the back.",
     "serious", None, "back"),
    ("SHLDHT", SD, F.shield_heart, "Heart Shield", "Puffy, pink and sparkly.", "fun", None, "arm"),
    ("BOWGL", WP, S.bow_galadhrim, "Bow of the Galadhrim", "Pale birch and gold. Fights as EA's elven bows.",
     "serious", None, "bow"),
    ("CARROT", WP, F.bow_carrot, "Carrot Bow", "A very large carrot. Fights as EA's elven bows.", "fun", None, "bow"),
    ("CANDY", WP, F.bow_candy, "Candy Cane Bow", "Peppermint. Fights as EA's elven bows.", "fun", None, "bow"),
]
BONES = {HLM: {"B_HEAD", "BAT_HEAD"},
         SH: {"BAT_SPINE2", "BAT_RIBS", "BAT_UARML", "BAT_UARMR"},
         SD: {"BAT_FARML", "BAT_SPINE1", "BAT_RIBS", "B_WAIST"},
         WP: {"BOWBONE", "B_HAND_L", "B_HANDL"}}
# vertex caps (in game, creation screen); cloaks are large sheets (docs/CAH.md)
BUDGET = {HLM: (650, 950), SH: (700, 1100), SD: (600, 900), WP: (540, 700)}
OWN_BUDGET = {"CLOAKLO": (900, 1350), "CLOAKRG": (900, 1350), "CAPEPK": (900, 1350), "RAINBOW": (900, 1350)}
COLOURS = [(40, 62, 38), (62, 74, 66), (60, 105, 175)]     # previews: leaf green, Lorien grey, crystal blue


def budget(name, group, kind):
    return OWN_BUDGET.get(name.split("_", 1)[1], BUDGET[group])[0 if kind in ("u", "m") else 1]


def named(spec):
    """The kit's PARTS for a folder: sub-objects SK<STEM>_<code>, the rows' shared upgrades, weapons
    on its own flags; each design wrapped to place itself in the model being built."""
    from ..kit.ini import row_upgrade
    from ..kit.models import folder
    space = Space(folder(spec)[1])
    count, flags, out = {}, iter(spec.FLAGS), []
    for code, group, fn, name, desc, sheet, remap, reg in CATALOGUE:
        if group == WP:
            up = "Upgrade_SKH_CHW%02d" % next(flags)
        else:
            count[group] = count.get(group, 0) + 1
            up = row_upgrade(group, count[group])
        out.append(("SK%s_%s" % (spec.STEM, code), group, wrap(fn, space, reg), name, desc, sheet, remap, up))
    return out


def kits(stem):
    k = lambda *codes: ["SK%s_%s" % (stem, c) for c in codes]
    return [("LORIEN", k("HOODLO", "CLOAKLO", "SHLDLF", "BOWGL") + ["GNLT_01", "BOOT_01"], False),
            ("RANGER", k("HOODRG", "CLOAKRG", "KNIVES", "BOWGL"), False),
            ("NOLDOR", k("HELMNL", "PAULMW", "SHLDLF", "BOWGL"), False),
            ("PINK SET", k("HOODPK", "CAPEPK", "SHLDHT", "CANDY"), False),
            ("RAINBOW", k("UNICORN", "RAINBOW", "SHLDHT", "CARROT"), False)]
