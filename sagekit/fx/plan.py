"""A faction's FX recipe and what it resolves to: which of EA's particle systems and FX lists get a
copy in the faction's colours, and which references move to the copies.

    assets/<faction>/fx.py      one FactionFX subclass: the faction's ramps, its spell book powers,
                                the classes its building fire and smoke take, per-system overrides

Three kinds of reference move, nothing else:

    spell book powers   the power's module in EA's shared book (EvilSpellBook / GoodSpellBook)
                        copied into the faction's book (a ChildObject) with `ReplaceModule`, its FX
                        fields (TriggerFX, TaintFX, HealFX, ...) naming FX lists of ours; every
                        other field EA's, word for word
    FX lists            a copy of EA's list whose ParticleSystem nuggets name our systems (and
                        FXListAtBonePos our lists); every other nugget EA's
    building fire       `ParticleSysBone` lines of EA's Draw modules in the faction's structure INIs
    and smoke           (Style.ini_dirs) naming one of BUILDING's systems: the system's name only

A system's class decides its ramp: magic (spell glows), fire (flames, embers), smoke (dark plumes);
natural ones (snow, dust, grass, leaves, debris, models of props) and model particles are never
tinted. `classify` guesses from the texture, shader and keys; the recipe's `systems` overrides it.
"""
import importlib
import inspect
import os
import re

from .. import paths
from . import blocks
from .tint import keyframes, luma

CLASSES = ("magic", "fire", "smoke")
# EA's building fire and smoke: the ParticleSysBone systems EA's damaged, really damaged and rubble
# states burn on every faction's structures (counted 2026-10-04 over the structure INIs)
BUILDING = {"FireBuildingSmall": "fire", "FireBuildingMedium": "fire", "FireBuildingLarge": "fire",
            "FireBuildingLarge02": "fire", "FireBuildingLarge03": "fire", "FireSmall": "fire", "FireSmoke": "fire",
            "SmokeBuildingLarge": "smoke", "SmokeBuildingMediumRubble": "smoke", "SmokeBuildingMedium": "smoke",
            "SmokeBuildingSmall": "smoke"}
COLOURED = 1.6                              # a texture whose channels differ more than this keeps EA's keys
FX_FIELD = re.compile(r"^\w*FX$")           # a module's FX list fields: TriggerFX, TaintFX, HealFX, ElvenWoodFX, FX
NATURAL = re.compile(r"snow|grass|leaf|flower|dirt|chunk|debris|rock|splinter|woodchip|butterfly|bench|keg|stool|"
                     r"water|ripple|splash|wave05|feather|bat0", re.I)
FIREY = re.compile(r"fire|ember|flame|lava|magma|spark", re.I)
SMOKEY = re.compile(r"smoke|cloud|dust|fog|mist|vapor|steam|plume", re.I)
PS_MEMBER = "data\\ini\\fxparticlesystem.ini"
FX_MEMBER = "data\\ini\\fxlist.ini"
BOOK_MEMBER = "data\\ini\\object\\system\\system.ini"


class FactionFX:
    """A faction's FX recipe (assets/<faction>/fx.py)."""
    faction = None          # sagekit faction id
    tag = None              # our names' infix: SagekitAngmar<EA name>, FX_SagekitAngmar<EA name>
    books = ()              # the faction's spell book ChildObjects (the Men: MenSpellBook, ArnorSpellBook)
    ramps = {}              # {class: tint.Ramp}; a class without one keeps EA's colours
    powers = ()             # SpecialPower templates of the books whose own FX take the faction's colours
    systems = {}            # {EA system: class or None (never tint)}: overrides of classify()
    structures = ()         # the classes of BUILDING the faction's structures take ("fire", "smoke")
    notes = ""

    def style(self):
        mod = importlib.import_module("assets.%s.style" % self.faction)
        from ..style import Style
        return next(c for _, c in inspect.getmembers(mod, inspect.isclass)
                    if issubclass(c, Style) and c is not Style and c.__module__ == mod.__name__)()

    def ours(self, ea_name):
        return "Sagekit%s%s" % (self.tag, ea_name)

    def our_fx(self, ea_fx):
        rest = ea_fx[3:] if ea_fx.upper().startswith("FX_") else ea_fx
        return "FX_Sagekit%s%s" % (self.tag, rest)

    def our_tag(self, ea_tag):
        return "%s_Sagekit%s" % (ea_tag, self.tag)


def recipes():
    """{faction: FactionFX} for every assets/<faction>/fx.py."""
    out = {}
    for f in sorted(os.listdir(paths.ASSETS)):
        if os.path.isfile(os.path.join(paths.ASSETS, f, "fx.py")):
            mod = importlib.import_module("assets.%s.fx" % f)
            cls = [c for _, c in inspect.getmembers(mod, inspect.isclass)
                   if issubclass(c, FactionFX) and c is not FactionFX and c.__module__ == mod.__name__]
            if len(cls) != 1:
                raise ValueError("assets/%s/fx.py must define exactly one FactionFX" % f)
            r = cls[0]()
            if r.faction != f:
                raise ValueError("assets/%s/fx.py: faction is %r" % (f, r.faction))
            out[f] = r
    return out


def classify(rows):
    """(class, why) EA's system suggests: magic, fire, smoke, natural or model."""
    tex = (blocks.field(rows, "System", "ParticleName") or "").lower()
    shader = (blocks.field(rows, "System", "Shader") or "ADDITIVE").upper()
    draw = next((n.split("=")[1].strip() for n, _ in blocks.modules_of(rows) if n.lower().startswith("draw")), "DefaultDraw")
    keys, _ = keyframes(rows)
    lit = [rgb for _, rgb, _, _ in keys if luma(rgb) > 4]
    sat = max(((max(c) - min(c)) / 255.0 for c in lit), default=0.0)
    if draw in ("RenderObjectDraw",) and shader != "W3D_EMISSIVE":
        return "natural", "a model particle (%s)" % tex
    if draw in ("ButterflyDraw", "LightningDraw"):
        return "natural", draw
    if NATURAL.search(tex):
        return "natural", "texture %s" % tex
    if not lit:
        return "natural", "no lit colour key"
    if FIREY.search(tex) and sat >= 0.12:
        return "fire", "fire texture %s, keys saturated %.2f" % (tex, sat)
    if SMOKEY.search(tex) and shader.startswith("ALPHA") and sat < 0.12:
        return "smoke", "grey %s plume" % tex
    if sat >= 0.12:
        return "magic", "%s keys saturated %.2f" % (shader.lower(), sat)
    return "natural", "grey keys (%.2f)" % sat


class Plan:
    """What a recipe resolves to against the game's INI texts {member: text}."""

    def __init__(self, r, texts, tints=None):
        self.r, self.texts, self.tints = r, texts, tints
        self.ps_index = blocks.systems(texts[PS_MEMBER])
        self.fx_index = blocks.fxlists(texts[FX_MEMBER])
        self.systems = {}       # EA system -> (ours, class, why)
        self.fxlists = {}       # EA FX list -> ours (only lists with something of ours in them)
        self.modules = []       # (book, parent, tag, {field: ours}, power)
        self.skipped = {}       # EA system -> (class, why) seen in the powers' FX, left EA's
        self.powers = {}        # power -> [EA FX list]
        self.resolve()

    # ------------------------------------------------------------------ systems
    def ps_rows(self, name):
        span = self.ps_index.get(name.lower())
        return blocks.body(self.texts[PS_MEMBER], span) if span else None

    def system_class(self, name):
        if name in self.r.systems:
            return self.r.systems[name], "the recipe's choice"
        rows = self.ps_rows(name)
        return classify(rows) if rows else ("natural", "not in fxparticlesystem.ini")

    def take_system(self, name, cls=None, why=None):
        """Our copy's name when EA's system `name` (and its slaves) takes a ramp, else None."""
        rows = self.ps_rows(name)
        if rows is None:
            self.skipped[name] = ("natural", "not an FXParticleSystem")
            return None
        if cls is None:
            cls, why = self.system_class(name)
        tex = (blocks.field(rows, "System", "ParticleName") or "").split()
        tint = self.tints(tex[0]) if self.tints and tex else (1.0, 1.0, 1.0)
        if cls in self.r.ramps and name not in self.r.systems and max(tint) > COLOURED * min(tint):
            cls, why = "natural", "its texture %s is coloured (%s): keys alone cannot reach the ramp" % (
                tex[0], " ".join("%.2f" % v for v in tint))
        if cls not in self.r.ramps:
            self.skipped[name] = (cls, why)
            return None
        canon = blocks.PS_HEAD.match(rows[0]).group(1)
        if canon not in self.systems:
            self.systems[canon] = (self.r.ours(canon), cls, why)
            for ref in blocks.refs(rows):           # a slave: its own class, a glow burns with its master's
                own, why_ = self.system_class(ref)
                self.take_system(ref, cls if own in ("magic", "fire") and ref not in self.r.systems else own,
                                 "slave of %s (%s)" % (canon, why_))
        return self.systems[canon][0]

    # ------------------------------------------------------------------ FX lists
    def take_fx(self, name, depth=0):
        """Our copy of EA's FX list `name` when anything in it takes a ramp, else None."""
        span = self.fx_index.get(name.lower())
        if span is None or depth > 4:
            return None
        canon = span[0]
        if canon in self.fxlists:
            return self.fxlists[canon]
        rows = blocks.body(self.texts[FX_MEMBER], span)
        hit = False
        for kind, fields, _, _ in blocks.nuggets(rows):
            if kind.lower() == "particlesystem" and fields.get("Name"):
                hit |= self.take_system(fields["Name"].split()[0]) is not None
            elif kind.lower() == "fxlistatbonepos" and fields.get("FX"):
                hit |= self.take_fx(fields["FX"].split()[0], depth + 1) is not None
        if hit:
            self.fxlists[canon] = self.r.our_fx(canon)
        return self.fxlists.get(canon)

    def fx_rows(self, ea):
        """Our copy of EA's FX list (rows), its references moved to our systems and lists."""
        text = self.texts[FX_MEMBER]
        rows = blocks.rename(blocks.body(text, self.fx_index[ea.lower()]), ea, self.fxlists[ea])
        for kind, fields, a, z in blocks.nuggets(rows):
            key = {"particlesystem": "Name", "fxlistatbonepos": "FX"}.get(kind.lower())
            if not key:
                continue
            for i in range(a + 1, z):
                k = rows[i].split(";")[0].split("=")[0].strip()
                if k == key:
                    v = rows[i].split("=", 1)[1].split(";")[0].split()[0]
                    new = self.systems.get(v, (None,))[0] if key == "Name" else self.fxlists.get(v)
                    if new:
                        rows[i] = blocks.set_value(blocks.drop_comment(rows[i]), new)
        nl = "\r\n" if rows[0].endswith("\r\n") else "\n"
        return ["; sagekit (sagekit/fx): EA's %s in the %s colours%s" % (ea, self.r.tag, nl)] + rows

    # ------------------------------------------------------------------ spell books
    def resolve(self):
        text = self.texts[BOOK_MEMBER]
        objs = blocks.objects(text)
        rows = blocks.lines(text)
        for book in self.r.books:
            if book.lower() not in objs:
                raise ValueError("%s: no spell book %s in %s" % (self.r.faction, book, BOOK_MEMBER))
            parent = objs[book.lower()][1]
            _, _, a, z = objs[parent.lower()]
            for power in self.r.powers:
                found = False
                for i in range(a + 1, z):
                    m = blocks.MODULE_HEAD.match(rows[i].split(";")[0])
                    if not m:
                        continue
                    fields = blocks.module_fields(text, parent, m.group(3))
                    if not any(k == "SpecialPowerTemplate" and v.lower() == power.lower() for k, v in fields):
                        continue
                    found = True
                    moved = {}
                    for k, v in fields:
                        if FX_FIELD.match(k) and v.lower() != "none":
                            self.powers.setdefault(power, []).append(v)
                            ours = self.take_fx(v)
                            if ours:
                                moved[k] = ours
                    if moved:
                        self.modules.append((book, parent, m.group(3), moved, power))
                if not found:
                    raise ValueError("%s: %s's parent %s has no module for %s" % (self.r.faction, book, parent, power))
        for name, cls in BUILDING.items():
            if cls in self.r.structures and cls in self.r.ramps:
                self.take_system(name, cls, "building %s" % cls)

    def building_systems(self):
        """{EA system: ours} the faction's structures move to (BUILDING's, by the recipe's classes)."""
        return {n: self.systems[n][0] for n, c in BUILDING.items()
                if c in self.r.structures and n in self.systems}
