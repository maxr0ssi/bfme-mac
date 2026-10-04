"""Angmar: the Witch-king's realm of Carn Dum, in the frozen north. Frost and ice on dark stone,
cold light in the slits, real fire burning cold blue-white (the game's particles, later). Never
the Elves' moonsilver and teal enamel on ivory, never Isengard's black stone with silver edges and
ember, never Mordor's black, ash, orange lava and Morgul green, never the Goblins' crimson, bone
and iron.

Max's pick (2026-10-01): A2 "Carn Dum frost, warm timber", palette A with D's warm planks and
frost-grained timber ("A without question, but maybe A with the wood of D?"), the wood then cooled
a touch on the citadel's build ("maybe the wood is just slightly too warm, just a little": less
orange, toward weathered brown; PALETTES["A2"] below).

EA's own Angmar (KBFortress, KBFortressB, KBFortressX, read 2026-10-01): cool blue-grey dressed
stone (hue ~250, saturation 0.05) with iron-framed arrow slits and rust running from the joints,
a smooth slab plinth, dark timber with white frost in its grain, warm orange-brown plank walls,
scale shingles with an oily violet-green sheen, a reddish beam with iron brackets, pale rune
diamonds set in rubble (KBFortressX). Its fire is blue: the citadel's torch cards draw
EXFireTorchSeqBlue (cyan-blue flames). The Ice Walls upgrade swaps every master sheet for an _ice
copy (ice crusted over the walls' feet). Its banners are the evil factions' shared
Evil_House_Color_Flag (dark ragged cloth with a skull on the pole) on KBHC* models, tinted in the
player's colour; KBHCFortress shows with the Banners upgrade. No Angmar structure INI sets a
coloured night light.

The options (`sagekit palettes angmar`, build/assets/angmar/_palettes/palette_options.jpg) are
recolours of EA's own sheet through its material ramps (assets/angmar/paint.py): stone, rock,
timber, planks, roof, iron, trim (lit metal edges), rust (by colour), slit (the slits, lit) and,
for new faces later, fire, ice and cloth. Every ramp is built from (position, luminance, hue)
stops (`_ramp`), so each keeps EA's value contrast whatever its hue: lights light, darks dark,
wood stays wood, ground readable (the Mordor lessons, Max: "a step back" when all went one dark
grey). Cloth follows the player's colour (house_template, the HC_ meshes); the "cloth" ramp
colours only the previews of new cloth faces."""
import os

from sagekit.style import Palette, Style

from .atlas import AngmarAtlas

NAVY, SLATE, RIME, ICE = (.55, .70, 1.0), (.72, .82, 1.0), (.90, .96, 1.0), (.60, .88, 1.0)
GREY, WARM_GREY, BONE, VIOLET = (1.0, 1.0, 1.0), (1.0, .97, .93), (1.0, .95, .84), (.62, .52, 1.0)
WOOD, ASH_WOOD, RUST_HUE, STEEL = (1.0, .70, .50), (1.0, .86, .74), (1.0, .55, .32), (.78, .88, 1.0)


def _ramp(stops):
    """A ramp from (position, luminance, hue as (r, g, b) proportions) stops: each stop's colour has
    that luminance (clipped at white), so a palette sets hue and value apart."""
    out = []
    for x, lum, (r, g, b) in stops:
        f = lum / (0.3 * r + 0.59 * g + 0.11 * b)
        out.append((x, tuple(round(min(1.0, c * f), 3) for c in (r, g, b))))
    return out


LEAF = _ramp([(0, .02, (.8, .9, 1.0)), (.5, .14, (.9, .95, 1.0)), (1, .42, RIME)])         # frozen scrub
GREY_CLOTH = _ramp([(0, .02, GREY), (.5, .13, GREY), (1, .34, GREY)])                       # preview only


def _palette(name, stone, timber, planks, roof, iron, trim, rust, slit, fire, rock=None, ice=None,
             accents=None, chroma=None):
    rock = rock or stone
    ice = ice or _ramp([(0, .10, NAVY), (.5, .45, ICE), (1, .95, RIME)])
    ramps = dict(stone=stone, rock=rock, timber=timber, planks=planks, roof=roof, iron=iron, trim=trim, rust=rust,
                 slit=slit, fire=fire, ice=ice, wood=planks, cloth=GREY_CLOTH, soot=iron, bronze=trim, gold=trim,
                 silver=trim, inlay=trim, mark=trim, ground=rock, enamel=rock, tiles=roof, leaf=LEAF, bone=trim,
                 hide=planks, water=ice, witch=slit)
    base = dict(occl=(.04, .045, .06), edge=(.80, .86, .94), grime=(.05, .05, .06), moss=(.08, .09, .10),
                dirt=(.13, .13, .14), groove=(.015, .017, .025), glow=(.55, .85, 1.0))
    p = Palette(name, ramps, dict(base, **(accents or {})), tints=dict(stone_alt=(1.0, 1.0, 1.0),
                                                                        stone_alt2=(1.0, 1.0, 1.0)))
    p.chroma = chroma or {}                 # {material: how much of EA's own colour variation to keep}
    return p


def _curve(k, gamma, hues, top=1.0):
    """A ramp whose luminance at x is k * x**gamma (capped at top): EA's values kept up to a scale (k)
    and a deeper shadow (gamma > 1); its hue runs through `hues` [(x, (r, g, b))]."""
    def hue(x):
        for (x0, c0), (x1, c1) in zip(hues, hues[1:]):
            if x <= x1:
                f = (x - x0) / (x1 - x0) if x1 > x0 else 0
                return tuple(a + (b - a) * f for a, b in zip(c0, c1))
        return hues[-1][1]
    return _ramp([(i / 10, min(top, max(.006, k * (i / 10) ** gamma)), hue(i / 10)) for i in range(11)])


BLUE, DEEP = (.42, .60, 1.0), (.50, .62, 1.0)
PALETTES = {
    "A": _palette(
        "A Carn Dum frost",
        stone=_curve(.95, 1.4, [(0, BLUE), (.45, SLATE), (.8, RIME)]),
        timber=_curve(1.1, 1.7, [(0, DEEP), (.45, SLATE), (.75, RIME)]),
        planks=_curve(.80, 1.15, [(0, (1.0, .80, .68)), (.6, (.98, .86, .78)), (1, (.92, .92, .94))]),
        roof=_curve(.85, 1.5, [(0, DEEP), (.5, BLUE), (.85, ICE)]),
        iron=_curve(.60, 1.3, [(0, DEEP), (1, SLATE)]),
        trim=_curve(1.0, .8, [(0, SLATE), (.5, ICE), (1, RIME)]),
        rust=_curve(.45, 1.3, [(0, DEEP), (1, SLATE)]),                      # EA's rust runs: frozen stains
        slit=_ramp([(0, .01, NAVY), (.4, .14, (.3, .72, 1.0)), (.75, .50, (.45, .85, 1.0)), (1, .85, RIME)]),
        fire=_ramp([(0, .02, NAVY), (.4, .25, (.3, .7, 1.0)), (.75, .65, ICE), (1, .97, RIME)]),
        accents=dict(glow=(.45, .80, 1.0))),
    "B": _palette(
        "B Witch-king's pall",
        stone=_curve(.82, 1.4, [(0, (.86, .82, 1.0)), (.35, WARM_GREY), (.7, BONE)]),
        timber=_curve(1.05, 1.6, [(0, (.86, .82, 1.0)), (.4, WARM_GREY), (.75, BONE)]),
        planks=_curve(.85, 1.1, [(0, (1.0, .90, .80)), (1, (1.0, .95, .88))]),          # bleached, ashen
        roof=_curve(.80, 1.4, [(0, (.60, .48, 1.0)), (.5, (.74, .66, 1.0)), (1, (.92, .90, 1.0))]),
        iron=_curve(.55, 1.3, [(0, (.86, .82, 1.0)), (1, WARM_GREY)]),
        trim=_curve(1.0, .8, [(0, WARM_GREY), (.5, BONE), (1, BONE)]),
        rust=_curve(.45, 1.3, [(0, (.86, .82, 1.0)), (1, WARM_GREY)]),
        slit=_ramp([(0, .01, VIOLET), (.4, .12, (.48, .34, 1.0)), (.75, .42, (.66, .54, 1.0)), (1, .78, (.88, .84, 1.0))]),
        fire=_ramp([(0, .02, VIOLET), (.4, .20, (.5, .38, 1.0)), (.75, .55, (.80, .76, 1.0)), (1, .95, (.95, .94, 1.0))]),
        accents=dict(edge=(.90, .86, .78), glow=(.62, .50, 1.0))),
    "C": _palette(
        "C Iron and ice",
        stone=_curve(.78, 1.4, [(0, (1.0, .62, .42)), (.45, (1.0, .74, .58)), (.7, (.98, .92, .90)), (.9, RIME)]),
        timber=_curve(1.05, 1.6, [(0, (1.0, .68, .50)), (.45, (1.0, .82, .70)), (.75, RIME)]),
        planks=_curve(.60, 1.2, [(0, (1.0, .62, .44)), (1, (1.0, .76, .60))]),
        roof=_curve(.80, 1.3, [(0, (1.0, .52, .30)), (.5, (1.0, .66, .46)), (.85, STEEL)]),
        iron=_curve(.75, 1.2, [(0, (1.0, .50, .28)), (.6, (1.0, .60, .40)), (1, (.95, .85, .80))]),
        trim=_curve(1.0, .8, [(0, STEEL), (.6, STEEL), (1, RIME)]),
        rust=_curve(.95, 1.1, [(0, (1.0, .46, .22)), (1, (1.0, .62, .38))]),
        slit=_ramp([(0, .01, STEEL), (.4, .08, STEEL), (.75, .32, STEEL), (1, .65, RIME)]),
        fire=_ramp([(0, .02, STEEL), (.4, .22, STEEL), (.75, .60, RIME), (1, .97, RIME)]),
        accents=dict(edge=(.80, .86, .94), glow=(.70, .82, 1.0)),
        chroma=dict(rust=0.4)),
    "D": _palette(
        "D Blue fire on grey stone",
        stone=_curve(1.0, 1.1, [(0, (.72, .80, 1.0)), (.5, (.80, .86, 1.0)), (.85, RIME)]),
        timber=_curve(1.05, 1.3, [(0, (1.0, .86, .78)), (.4, (.95, .93, .95)), (.75, RIME)]),
        planks=_curve(.95, 1.0, [(0, WOOD), (.6, WOOD), (1, (1.0, .82, .66))]),
        roof=_curve(.95, 1.1, [(0, (.86, .82, 1.0)), (.7, (.92, .90, 1.0)), (1, RIME)]),
        iron=_curve(.75, 1.1, [(0, (.9, .9, 1.0)), (1, (.92, .94, 1.0))]),
        trim=_curve(1.0, .85, [(0, (.9, .92, 1.0)), (1, RIME)]),
        rust=_curve(.9, 1.0, [(0, RUST_HUE), (1, (1.0, .66, .46))]),
        slit=_ramp([(0, .01, (.2, .55, 1.0)), (.4, .14, (.2, .6, 1.0)), (.75, .50, (.35, .75, 1.0)),
                    (1, .85, (.75, .92, 1.0))]),
        fire=_ramp([(0, .02, (.2, .5, 1.0)), (.4, .25, (.2, .6, 1.0)), (.75, .62, (.4, .8, 1.0)), (1, .97, RIME)]),
        accents=dict(glow=(.30, .65, 1.0)),
        chroma=dict(roof=1.0, planks=0.6, rust=0.5)),
}


def _warm_wood(base, timber, planks, grain, name):
    """`base` with these timber and planks ramps (and the ramps drawn from them: wood, hide) and
    `grain`, the share of EA's own colour variation kept in the boards (chroma); the rest of base
    unchanged."""
    ramps = dict(base.ramps, timber=timber, planks=planks, wood=planks, hide=planks)
    p = Palette(name, ramps, dict(base.accents), tints=dict(base.tints))
    p.chroma = dict(getattr(base, "chroma", {}), planks=grain)
    return p


# Max's pick (2026-10-01, on the palette board): "A without question, but maybe A with the wood of D?" -
# A's blue-black stone, rime and icy slits with D's warm planks and frost-grained timber. On the citadel's
# pass 3 build: "maybe the wood is just slightly too warm, just a little" - so D's wood a touch cooler: the
# planks' hue from orange (1, .70, .50) toward a weathered brown (1, .78, .62), less of EA's orange grain
# kept (chroma 0.35, D's 0.6), the timber's darks a shade greyer; still clearly warm against the stone
PALETTES["A2"] = _warm_wood(
    PALETTES["A"],
    timber=_curve(1.05, 1.3, [(0, (1.0, .89, .83)), (.4, (.95, .93, .95)), (.75, RIME)]),
    planks=_curve(.93, 1.0, [(0, (1.0, .78, .62)), (.6, (1.0, .79, .64)), (1, (1.0, .85, .73))]),
    grain=0.35, name="A2 Carn Dum frost, warm timber")
NOTES = {
    "A": "Blue-black stone and slate, rime-white frost on every light, icy cyan-blue in the slits",
    "A2": "A with D's wood: warm planks and timber against blue-black stone and rime (Max's pick)",
    "B": "Charcoal stone, dead bone-white lights and edges, ashen wood, cold violet-blue witch-light",
    "C": "Rust-dark iron-brown stone and plates, frost-white crust on the lights, pale steel-blue edges",
    "D": "EA's own, colder: grey-blue stone, warm boards, the shingles' sheen, rust, EA's blue torch-fire",
}
# the palette the builds paint with: A2, Max's pick; ANGMAR_PALETTE (A, A2, B, C or D) overrides it for a build
# of another option on the real design (as assets/isengard/wall_hub/building.py's ISENGARD_HUB_CROWN)
PALETTE = PALETTES[(os.environ.get("ANGMAR_PALETTE") or "A2").upper()]
# new faces of these atlas regions painted as a material: (ramp, gain, lift)
TAGRAMPS = {"trim": ("trim", 0.9, 0.25), "cloth": ("cloth", 0.85, 0.2), "flame": ("fire", 0.25, 0.74),
            "ice": ("ice", 1.1, 0.3), "chain": ("iron", 0.8, 0.0),
            # the kit's (shapes*.py): steel edges, rime (frost white), cold glow (ember), soot
            "iron": ("iron", 1.0, 0.0), "steel": ("trim", 0.8, 0.4), "rime": ("ice", 0.4, 0.6),
            "ember": ("fire", 0.5, 0.42),
            "soot": ("iron", 0.5, 0.0)}


class AngmarStyle(Style):
    faction = 'angmar'
    name = PALETTE.name
    palette = PALETTE
    atlas = AngmarAtlas()
    ini_dir = 'data\\ini\\object\\evilfaction\\structures\\angmar\\'
    sheet_dir = 'art\\compiledtextures\\kb\\'
    sheet_skip = Style.sheet_skip + ("nrm_ice", "normal", "_height",    # KBFortressNRM_Ice, KBHall_Normal,
                                     "dummy.", "low.", "med.")          # KBMillNormal, KBFortress_Height; EA's
                                                                        # placeholders (LOD labels, KBDen's dummy)
    master_variants = {'damaged': 'KBFortress_D1.tga', 'snow': 'KBFortress_snow.tga'}
    house_template = 'KBHCBtlTwr'   # copied for buildings EA gave no house-colour model (the walls, expansions)
    # the palette options tool (sagekit/palettes.py): the choices, their notes, where they are shown
    palettes = PALETTES
    palette_notes = NOTES
    palette_ea_note = "Cool grey stone, warm boards, frost-grained timber, oily violet-green shingles, rust"
    palette_building = 'fortress'
    palette_views = ('board', 'keep')
    swatches = (("stone", "stone", 0.45), ("stone lit", "stone", 0.75), ("timber / frost", "timber", 0.7),
                ("planks", "planks", 0.5), ("roof", "roof", 0.5), ("iron", "iron", 0.5), ("trim", "trim", 0.7),
                ("rust", "rust", 0.5), ("slits", "slit", 0.75))

    def shapes(self):
        """The Angmar kit (assets/angmar/shapes.py; Blender side, needs mathutils)."""
        from .shapes import AngmarShapes
        return AngmarShapes()

    def sheet_size(self, name):
        """EA's own 512 for the mill's and the forge works' sheets (their redesigns paint their bodies on
        sheets of their own; the recolours are left to EA's level-up meshes and leftovers), else 1024."""
        return 512 if name.lower().startswith(("kbmill", "kbforge")) else super().sheet_size(name)

    def sheet_atlas(self, name):
        """KBFortressB's and KBFortressX's tables (atlas_sheets.py) before the faction atlas: both
        names start with KBFortress, which the base class would take for the master's family."""
        from .atlas_sheets import sheet_atlas
        return sheet_atlas(name, self.atlas.ground_sat) or super().sheet_atlas(name)

    def recolour(self, building=None):
        """The first paint layer: AngmarRecolour, with a building's own sheet's table for its EA faces."""
        from .atlas_sheets import sheet_atlas
        from .paint import angmar_layers
        own = sheet_atlas(building.sheet_atlas.texture) if building is not None and building.two_sheets else None
        return angmar_layers()["AngmarRecolour"](atlas=self.atlas if building is not None else None, sheet_atlas=own)

    def sheet_layers(self):
        return [self.recolour()]

    def layers(self, building):
        from sagekit.paint import layers as L

        return [self.recolour(building),
                *[L.TagRamp(tag, r, gain=g, lift=k) for tag, (r, g, k) in TAGRAMPS.items()],
                L.BuildingDecals(building),
                L.WoodGrain(depth=0.22),
                L.Occlusion(),
                L.EdgeWear(base=0.3, metal=0.5),
                L.Streaks(),
                L.GroundDirt()]
