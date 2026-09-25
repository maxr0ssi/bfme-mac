"""The Dwarven look: honey granite, burnished gold and bronze, gold-inlaid runes on dark basalt
(the user's pick, "palette A"), chosen over a cool blue-grey Erebor variant."""
from sagekit.style import Palette, Style

from .atlas import DwarvenAtlas

PALETTE = Palette(
    "Honey granite & gold",
    ramps={
        "stone": [(0, (.12, .10, .08)), (.25, (.31, .27, .22)), (.45, (.50, .45, .37)), (.62, (.64, .58, .49)),
                  (.8, (.78, .72, .62)), (1, (.93, .89, .81))],
        "bronze": [(0, (.10, .06, .02)), (.3, (.40, .24, .09)), (.5, (.64, .42, .16)), (.7, (.84, .62, .28)),
                   (.9, (.98, .84, .52)), (1, (1, .95, .78))],
        "gold": [(0, (.20, .12, .02)), (.4, (.66, .46, .12)), (.65, (.93, .74, .30)), (.85, (1, .90, .55)), (1, (1, .98, .85))],
        "wood": [(0, (.10, .04, .02)), (.4, (.38, .16, .07)), (.7, (.62, .32, .14)), (1, (.86, .58, .32))],
        "ground": [(0, (.04, .04, .04)), (.4, (.11, .10, .09)), (.7, (.20, .18, .16)), (1, (.34, .30, .26))],
        "inlay": [(0, (.45, .30, .08)), (.5, (.88, .66, .22)), (.8, (1, .86, .45)), (1, (1, .97, .78))],
        "iron": [(0, (.03, .03, .03)), (.5, (.12, .11, .10)), (1, (.36, .34, .31))],
        "rock": [(0, (.06, .05, .04)), (.4, (.26, .22, .17)), (.7, (.45, .39, .30)), (1, (.70, .63, .52))],
        "tiles": [(0, (.10, .08, .05)), (.5, (.55, .46, .32)), (1, (.90, .82, .64))],
        "trim": [(0, (.14, .09, .03)), (.35, (.48, .33, .12)), (.6, (.76, .56, .22)), (.85, (.95, .80, .45)), (1, (1, .95, .78))],
    },
    accents={"occl": (0.34, 0.24, 0.17), "edge": (1.0, 0.93, 0.80), "grime": (0.20, 0.15, 0.10),
             "moss": (0.36, 0.38, 0.16), "dirt": (0.36, 0.28, 0.19), "glow": None},
    tints={"stone_alt": (1.04, 0.97, 0.92), "stone_alt2": (0.95, 0.96, 0.98)},
)


class DwarvenStyle(Style):
    faction = "dwarves"
    name = "Erebor: honey granite and gold"
    palette = PALETTE
    atlas = DwarvenAtlas()
    ini_dir = "data\\ini\\object\\goodfaction\\structures\\dwarven"
    sheet_dir = "art\\compiledtextures\\db"
    master_variants = {"damaged": "DBFortress1_D.tga", "snow": "DBFortress1_Snow.tga", "stonework": "DBFortress_U.tga"}
    budget_mb = 256

    def sheet_size(self, name):
        return 2048 if name.lower().startswith("dbfortress1") else 1024

    def sheet_layers(self):
        from sagekit.paint import layers as L
        return [L.Recolour(), L.MetalRims(min_plate=0.45), L.Inlay()]

    def shapes(self):
        from .shapes import DwarvenShapes
        return DwarvenShapes()

    def layers(self, building):
        from sagekit.paint import layers as L
        return [
            L.Recolour(),
            L.TagRamp("trim", "trim"),            # new cornices, step reveals and frame bands: bronze
            L.MetalRims(),
            L.BuildingDecals(building),
            L.WoodGrain(),
            L.Ashlar(),
            L.Occlusion(),
            L.EdgeWear(),
            L.Streaks(),
            L.GroundDirt(),
            L.Moss(),
            L.Inlay(),
        ]
