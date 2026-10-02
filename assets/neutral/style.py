"""Wilderland: the look of EA's capturable buildings, kept and sharpened. Nobody's faction, so the
colours stay EA's own (weathered olive and blue-grey boards, grey fieldstone, silvered shingles)
graded for the RTS camera: a little more contrast and colour so timber reads as timber and stone
as stone, never muddy. New work is timber and stone of the same sheet, a faded madder cloth, dark
iron, brass and warm lamp light.

When a player captures a neutral building it takes on the capturer's look (sagekit/capture.py):
a small dress of kit pieces per faction, shown only while that faction holds it, each painted in
that faction's own ramps (DRESS_RAMPS, read from the faction's style) with its cloth in the
capturer's house colour."""
import importlib

from sagekit.style import Palette, Style

from .atlas import DRESS_PREFIXES, DRESS_ROLES, NeutralAtlas

TIMBER = [(0, (.07, .05, .035)), (.3, (.25, .19, .13)), (.6, (.50, .41, .30)), (.85, (.72, .63, .50)), (1, (.88, .82, .70))]
STONE = [(0, (.10, .10, .095)), (.3, (.33, .32, .30)), (.6, (.58, .56, .52)), (.85, (.76, .74, .69)), (1, (.90, .88, .84))]
MADDER = [(0, (.09, .025, .02)), (.35, (.36, .09, .06)), (.6, (.58, .19, .11)), (.85, (.76, .38, .24)), (1, (.90, .62, .46))]
IRON = [(0, (.03, .03, .03)), (.5, (.13, .13, .14)), (.85, (.32, .32, .33)), (1, (.50, .50, .50))]
BRASS = [(0, (.12, .08, .03)), (.4, (.42, .30, .12)), (.7, (.70, .54, .26)), (.9, (.90, .78, .48)), (1, (1, .93, .74))]
ROCK = [(0, (.06, .06, .06)), (.35, (.22, .21, .20)), (.65, (.42, .40, .37)), (1, (.66, .63, .58))]
HOARD = [(0, (.25, .15, .02)), (.35, (.62, .43, .10)), (.65, (.92, .72, .26)), (.85, (1, .88, .50)), (1, (1, .97, .80))]
BONE = [(0, (.20, .17, .12)), (.4, (.55, .50, .40)), (.75, (.80, .76, .64)), (1, (.95, .92, .84))]
EMBER = [(0, (.35, .05, .0)), (.4, (.80, .22, .02)), (.75, (1, .52, .10)), (1, (1, .85, .45))]
WEB = [(0, (.45, .46, .46)), (.5, (.72, .73, .73)), (1, (.93, .94, .95))]
GLOW = [(0, (.55, .25, .05)), (.5, (.95, .62, .22)), (.8, (1, .82, .45)), (1, (1, .95, .78))]

# the capture dress: per faction, its style and the ramp each role is painted in
DRESS_FACTIONS = {"dw": "dwarves", "el": "elves", "mn": "men", "is": "isengard", "mo": "mordor", "gb": "goblins",
                  "an": "angmar"}
DRESS_RAMPS = {
    "dw": dict(stone="stone", gilt="gold", metal="ground", wood="wood", bone="stone", glow="inlay"),
    "el": dict(stone="stone", gilt="gold", metal="inlay", wood="wood", bone="stone", glow="crystal"),
    "mn": dict(stone="stone", gilt="gold", metal="inlay", wood="wood", bone="stone", glow="gold"),
    "is": dict(stone="stone", gilt="silver", metal="iron", wood="wood", bone="bone", glow="fire"),
    "mo": dict(stone="stone", gilt="steel", metal="iron", wood="wood", bone="bone", glow="fire"),
    "gb": dict(stone="rock", gilt="bronze", metal="iron", wood="wood", bone="bone", glow="fire"),
    "an": dict(stone="stone", gilt="silver", metal="iron", wood="timber", bone="bone", glow="ice"),
}


def faction_style(prefix):
    mod = importlib.import_module("assets.%s.style" % DRESS_FACTIONS[prefix])
    return next(v() for v in vars(mod).values() if isinstance(v, type) and getattr(v, "faction", None) == DRESS_FACTIONS[prefix])


def dress_ramps():
    """{'<prefix>_<role>': ramp} from each faction's own palette."""
    out = {}
    for p in DRESS_PREFIXES:
        pal = faction_style(p).palette
        out.update({"%s_%s" % (p, role): pal[name] for role, name in DRESS_RAMPS[p].items()})
    return out


PALETTE = Palette(
    "Wilderland: EA's timber, stone and shingle, sharpened",
    ramps=dict(stone=STONE, wood=TIMBER, bronze=BRASS, gold=BRASS, ground=STONE, inlay=BRASS, iron=IRON,
               rock=ROCK, tiles=STONE, cloth=MADDER, brass=BRASS, glow=GLOW, hoard=HOARD, bone=BONE, ember=EMBER,
               web=WEB, **dress_ramps()),
    accents={"occl": (.22, .20, .18), "edge": (1.0, .96, .88), "grime": (.20, .17, .13), "moss": (.30, .34, .16),
             "dirt": (.34, .28, .20), "glow": None},
    tints={"stone_alt": (1.03, .99, .95), "stone_alt2": (.96, .98, 1.02)},
)
# new faces of these atlas regions painted as a material: (ramp, gain, lift); and every dress tag in
# its faction's ramp
TAGRAMPS = dict({"cloth": ("cloth", .9, .14), "brass": ("brass", .9, .18), "iron": ("iron", .9, .05),
                 "glow": ("glow", .6, .45), "rock": ("rock", 1.0, .02), "gold": ("hoard", .9, .15),
                 "bone": ("bone", .7, .3), "ember": ("ember", .6, .4), "web": ("web", .5, .45)},
                **{"%s_%s" % (p, role): ("%s_%s" % (p, role), .95 if role != "glow" else .6, .12 if role != "glow" else .4)
                   for p in DRESS_PREFIXES for role in DRESS_ROLES if role != "cloth"})


class NeutralStyle(Style):
    faction = "neutral"
    name = PALETTE.name
    palette = PALETTE
    atlas = NeutralAtlas()
    ini_dir = "data\\ini\\object\\neutral\\"
    sheet_dir = "art\\compiledtextures\\nb\\"
    master_variants = {"damaged": "NBInn_D1.tga", "snow": "NBInn_snow.tga"}
    house_template = "NBHCElvnBarx"     # the capture dress's cloth model is a copy (sagekit/capture.py)
    budget_mb = 160                     # a dozen capturable buildings and lairs, STANDARD tier
    # (no sheet_layers: EA's other neutral sheets stay as they are; `sagekit sheets neutral` has nothing to do)

    def shapes(self):
        from .shapes import NeutralShapes
        return NeutralShapes()

    def layers(self, building):
        from sagekit.paint import layers as L

        from .paint import Grade
        return [Grade(),
                *[L.TagRamp(tag, r, gain=g, lift=k) for tag, (r, g, k) in TAGRAMPS.items()],
                L.BuildingDecals(building),
                L.WoodGrain(depth=0.18),
                L.Occlusion(),
                L.EdgeWear(base=0.16, metal=0.34),
                L.Streaks(),
                L.GroundDirt(),
                L.Moss()]
