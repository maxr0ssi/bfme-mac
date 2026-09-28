"""`python3 -m sagekit new <faction> [--write]`: one stub recipe per design unit of EA's.

A design unit is a healthy model a player builds (a structure or wall object of the faction, not a
helper, campaign variant or map castle piece) whose body - its largest static mesh painted from a
building sheet, a mesh with a normal map first, one standing on the ground before one raised on
another (a statue's figure) - has at least 100 triangles (a wall piece's: 50, and its tallest mesh,
not the wall stubs beside a hub or tower); meshes the rule cannot tell from it are named in the
stub's docstring. A mesh the object's SubObjectsUpgrades both show and hide (the farm's level-up
walls V1, V2 and their stand-ins) comes after the others; a structure's model with no mesh on a
building sheet may be painted from a unit sheet (the statue's GUHeroStat). Each Draw module of an object is one
family (the fortress's upgrades are Draw modules of the citadel: each is a unit with `parts`), and
each build variation in it (BUILD_VARIATION_ONE / _TWO: GBFDOTOWA, GBFDOTOWB) a unit of its own
(`<name>_b`); a ChildObject counts with the Draw modules it inherits (GondorFarm: FarmInterface's);
a model drawn by several objects is one unit; a body that is another unit's body under a
second model (EBBbattleTwrS, the snow tower) is a variant, not a unit; a second static mesh of 1000+
triangles on a building sheet is a unit of its own, chained on the first with `base`.

Each stub carries what the survey of the game says about it (sagekit/scaffold_write.py writes it):
source, target, sheet, parts, HOUSE_DRAW (objects EA gave no house-colour model), world_space (a
body on a tilted bone), own_model (a model another faction draws too, sagekit/ownership.py),
own_textures with free names (sagekit/names.py), the nearest Dwarven recipe, views sized to the
model, and design() returning []: it passes validate and builds through extract as it stands.
Existing recipes are never touched.
"""
import math
import re

from .formats.textures import compiled_path
from .formats.w3d import W3DFile
from .formats.w3dframes import IDENTITY, apply, mesh_frames

STRUCTURES = {"men": "goodfaction\\structures\\men", "elves": "goodfaction\\structures\\elven",
              "dwarves": "goodfaction\\structures\\dwarven", "isengard": "evilfaction\\structures\\isengard",
              "mordor": "evilfaction\\structures\\mordor", "goblins": "evilfaction\\structures\\wild",
              "angmar": "evilfaction\\structures\\angmar"}
MIN_TRIS, SECOND_TRIS, TILT = 100, 1000, 5.0
MIN_WALL_TRIS = 50          # wall pieces are low (Gondor's hub OBJECT03 has 94 triangles)
VARIATION_SUFFIX = {"BUILD_VARIATION_ONE": "", "BUILD_VARIATION_TWO": "_b", "BUILD_VARIATION_THREE": "_c"}
UNIT_SHEET = re.compile(r"^.u", re.I)       # GUHeroStat: a unit sheet (a statue's figure)
SUBOBJECTS = re.compile(r"^\s*(Show|Hide)SubObjects\s*=\s*([^;/]*)", re.I)
KINDOF = re.compile(r"^\s*KindOf\s*=\s*([^;/]*)", re.I)
GROUNDED = 0.1              # a body's foot within this share of the model's height of its ground

# the survey's scope rules (faction_survey: analyse.py)
HELPER = re.compile(r"Foundation|ExpansionPad|CenterGeneric|_temp$|Proxy|CampFloor|CastleFloor|Tutorial|CPCreator|"
                    r"Discounter|TowerShadow|TaintLand|TaintObject|Grove$|ElvenWood|FearCreator|Killer|CPShadow|"
                    r"FloodgateFlood|^WargSentry$|Warg_Slaved|EconomyKeep|UpgradeNode|CampCentralTent", re.I)
VARIANT = re.compile(r"^WOR_|^MER_|^EGH_|_Celduin|BlueMountains|CarnDum|CINE$|DarkEye|GoodRivIntro|ForGoodIthilien|"
                     r"_Snow$|Independ|Multiplayer$|ElderRaces|_Tutorial|Side(Expansion)?$|^Citadel", re.I)
OLDWALL = re.compile(r"^[A-Z]BWall(Ramp2?|Rmprt|rampart|Gate|Seg|PG|Twr|Treb|Upgrd)$|^GBMinwallBE$", re.I)
MAP_FILE = re.compile(r"(^|\\)(\w*campsandcastles|baraddur|blackgate|mountdoom|eyeofsauron|toweroforthanc|\w*whitetower|"
                      r"scaffolding|\w*castlewalls|\w*forbiddenpool|\w*silvertree|\w*tents|goblintent\d|trolldrum|holes)\.ini$", re.I)
WALL = re.compile(r"(Wall(Segment|Gate|PosternGate|Tower|Trebuchet|Catapult|Hub)Small|WallCliffCap|WallHubSmallUpgradeable|"
                  r"^(Elven|Isengard)CastleWall(Segment|Hub|Gate))$")
FX_SHEET = re.compile(r"^(ex|cu|pg0|fell|s3_|flagpole|dummy|lm_|nbase|wbfoundation|gb_window|gbfire|gbnight|gbvet|"
                      r"moltenmetal|g_arrow|.u)", re.I)
UPGRADE_FLAG = re.compile(r"^(FORTRESS_IMPROVEMENT_\d+|UPGRADE_(?!NUMENOR_STONEWORK).*|.*LEVEL\d*|WEAPONSET_\w+)$")
HC_MODEL = re.compile(r"^[A-Za-z]{2}HC")

# (regex on object name + model, role, nearest Dwarven recipe), first match wins (the survey's)
ROLES = [
    (r"Moat|Spikes?\b|RazorSpines|FSpike", "fortress_addon", "fortress_monument"),
    (r"WallHubSmallExpansion|CastleWallHubExpansion|FWHub|HTow\b", "fortress_wall_hub", "fortress_wall_hub"),
    (r"(Catapult|Trebuchet|Ballista|MineLauncher)\w*Expansion", "catapult_tower", "catapult_tower"),
    (r"(ArrowTower|BattleTower|Watchtower|GiantSentry|EreborTower|TowerTower|IsengardTower)\w*Expansion", "tower_expansion",
     "erebor_tower"),
    (r"Expansion", "hall_expansion", "hall"),
    (r"CliffCap|WallNE\b", "wall_end", "wall_end"),
    (r"Postern|WallPGN?\b|PostGat", "wall_postern", "wall_postern"),
    (r"WallGate|AngwGN|GateN", "wall_gate", "wall_gate"),
    (r"WallTower|WallTwr|ArrwWal", "wall_tower", "wall_tower"),
    (r"WallCatapult|WallTreb|TrSlgWl|TrlSlingWall", "wall_trebuchet", "wall_trebuchet"),
    (r"WallHub|Rmprt|rampart|WalHub", "wall_hub", "wall_hub"),
    (r"WallSegment|WallN\b|WallRamp|WallSeg|CastleWall", "wall_segment", "wall_segment"),
    (r"SummonedCitadel", "citadel", "citadel"),
    (r"Citadel|Fortress\b", "fortress", "fortress"),
    (r"Barracks|Hall\b|UrukPit|OrcPit|Cave\b|Den\b|Temple|HallofTwilight", "barracks", "barracks"),
    (r"Archer|Arch", "archery", "archery_range"),
    (r"Stable|Pasture|WargPit|Kennel|MumakilPen|SpiderPit|TrollCage", "stable", "barracks"),
    (r"Forge|Workshop|SiegeWorks|Armory|ForgeWorks|Seige", "siege", "siege_works"),
    (r"Farm|Mill\b|LumberMill|Furnace|SlaughterHouse|MineShaft|Market|StoneMaker|Tavern|Fissure|TreasureTrove|Hearth",
     "economy", "hearth"),
    (r"Statue|Mirror|Mallorn|Well\b|EntMoot", "special", "statue"),
    (r"BattleTower|Keep\b|SentryTower|WargSentry|Tower", "tower", "sentry_tower"),
    (r"Bunker|Barricade", "bunker", "bunker"),
]
UPGRADE_NEAREST = [(r"Oil|Barrel|Cauld|Excav|FFArrow|FFire|Orcfire|Munition", "fortress_barrels"),
                   (r"Flam|Fire|Braz", "fortress_braziers"),
                   (r"Statue|Status|Sorcery|Spines|Spike|Sanctum|HoLa|Throne|Tower|Nest|Eagle|Fount", "fortress_monument")]
FACTION_WORDS = ("Elven", "Elder", "Dwarven", "Dwarf", "Men", "Gondor", "Arnor", "Isengard", "Mordor", "Wild", "Goblin",
                 "Angmar", "Eregion")


def snake(s):
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", s).lower().strip("_")


def object_stem(obj):
    """ElvenCastleWallGate -> wall_gate, EregionForge -> forge, ElvenFortressCrystalMoat -> fortress_crystal_moat."""
    s = obj
    for w in FACTION_WORDS:
        if s.startswith(w) and s[len(w):][:1].isupper():
            s = s[len(w):]
            break
    s = snake(s.replace("Castle", "").replace("Small", "").replace("Expansion", ""))
    return {"wall_cliff_cap": "wall_end"}.get(s, s)


def tag_stem(tag):
    """ModuleTag_EaglesNestDraw -> eagles_nest, ModuleTag_DrawTheEnt -> ent."""
    words = [w for w in snake(re.sub(r"^ModuleTag_?", "", tag).replace("Draw", "_")).split("_") if w and w not in ("the", "draw")]
    return "_".join(words) or "part"


def role_of(obj, model):
    s = obj + " " + model
    return next(((role, near) for rx, role, near in ROLES if re.search(rx, s, re.I)), ("other", None))


def category(obj, file, models):
    if HELPER.search(obj):
        return "helper"
    if VARIANT.search(obj):
        return "variant"
    if any(OLDWALL.match(m) for m in models):
        return "map_castle"
    if WALL.search(obj):                        # before the file rule: the Elves' walls live in *castlewalls.ini
        return "wall"
    return "map_castle" if MAP_FILE.search(file) else "player"


def healthy(draw):
    """[(the model a Draw module shows when healthy, the upgrade flags that switch it on, the build
    variation or None)]: one per build variation (GBFDOTOWA under BUILD_VARIATION_ONE and the
    default, GBFDOTOWB under _TWO; sagekit/formats/ini.py variation_states), else one."""
    from .formats.ini import VARIATION, variation_states
    every = [st for st in draw.states if st.kind == "model" and st.model and st.model.lower() != "none"]
    out = []
    for v in sorted({f for st in every for f in st.flags if f.startswith(VARIATION)}) or [None]:
        states = [st for st in variation_states(draw, "", v) if st in every] if v else every
        pick = next((st for st in states if all(UPGRADE_FLAG.match(f) for f in st.flags if f != v)), None)
        if pick:
            out.append((pick.model, tuple(sorted(f for f in pick.flags if f != v)), v))
        elif states and not v:
            out.append((states[0].model, (), None))
    return out or [(None, (), None)]


def is_building_sheet(t):
    return not FX_SHEET.search(t) and "_nrm" not in t.lower() and "house_color" not in t.lower()


def switched(install, pairs):
    """(mesh names the objects' SubObjectsUpgrade modules both show and hide - level-up pieces and
    their stand-ins -, whether an object is a STRUCTURE): pairs [(ini, object)] - each object's
    block in its file, parents included."""
    from .formats.ini import OBJECT_RE, strip
    shown, hidden, structure = set(), set(), False
    for ini, obj in pairs:
        cur = None
        for raw in install.read(ini).decode("latin-1").splitlines():
            m = OBJECT_RE.match(strip(raw))
            if m and not raw[:1].isspace():
                cur = m.group(2)
                continue
            m = SUBOBJECTS.match(raw)
            if m and cur == obj:
                names = {n.upper() for n in m.group(2).split() if "*" not in n}
                (shown if m.group(1).lower() == "show" else hidden).update(names)
            m = KINDOF.match(raw)
            if m and cur == obj:
                structure |= "STRUCTURE" in m.group(1).upper().split()
    return shown & hidden, structure


def bodies(install, model, units=False, tallest=False):
    """[(mesh name, mesh, diffuse sheet, normal map or None, grounded)] of the model's static meshes
    painted from a building sheet, the unit's body first: a normal-mapped mesh before a plain one,
    a grounded one (standing on the model's ground, not raised on another mesh) before a raised one,
    then by size. The largest mesh is not always the building: EBStatue's figure (9,828 triangles)
    stands on its holder, the mirror's roots grip the dais round the stair. units: unit sheets count
    (a statue); tallest: height before size (a wall tower or hub stands above the wall stubs its
    model carries)."""
    data = install.read(install.model_path(model))
    f, fr = W3DFile(data), frames(install, model)
    zs = {n: [apply(fr.get(n, IDENTITY), v)[2] for v in m.verts] for n, m in f.meshes.items() if m.verts}
    ground = min(min(z) for z in zs.values()) if zs else 0.0
    top = max(max(z) for z in zs.values()) if zs else 1.0
    out = []
    for n, m in f.meshes.items():
        if m.skinned or n.startswith(("HC_", "N_")) or n not in zs:
            continue
        dif = [t for t in m.textures if is_building_sheet(t) or units and UNIT_SHEET.match(t) and "_nrm" not in t.lower()]
        nrm = next((t for t in m.textures if "_nrm" in t.lower() or "normal" in t.lower()), None)
        if dif:
            out.append((n, m, dif[0], nrm, min(zs[n]) - ground <= GROUNDED * (top - ground)))
    height = (lambda x: -round(max(zs[x[0]]))) if tallest else (lambda x: 0)
    return sorted(out, key=lambda x: (x[3] is None, not x[4], height(x), -len(x[1].tris)))


def rivals(bs):
    """The meshes the rule could not tell from the chosen body: the same kind (normal map, grounded,
    sheet) and at least a quarter of its size - the stub's docstring names them for the designer."""
    if not bs:
        return []
    n0, m0, s0, nrm0, g0 = bs[0]
    return [(n, len(m.tris)) for n, m, s, nrm, g in bs[1:]
            if (nrm is None) == (nrm0 is None) and g == g0 and s.lower() == s0.lower() and len(m.tris) >= len(m0.tris) / 4]


def frames(install, model):
    data = install.read(install.model_path(model))
    return mesh_frames(data, lambda skl: install.read(install.model_path(skl[:-4])))


def tilt(frame):
    """Degrees between the bone's z axis and the world's."""
    R = frame[0]
    return math.degrees(math.acos(max(-1.0, min(1.0, R[2][2]))))


def plan(faction, install, own):
    """[unit dict] for the faction's design units, and [(model, why)] for what was left out."""
    from .building import same_body
    from .formats.ini import variation_states
    from .ownership import empty_model
    root = "data\\ini\\object\\" + STRUCTURES[faction]
    by_obj = install.object_draws(root)             # a ChildObject with the Draw modules it inherits
    units, skipped, seen = [], [], {}
    for obj, ds in by_obj.items():
        fams = [(d,) + h for d in ds if d.type.lower() != "w3dfloordraw" for h in healthy(d)]
        fams = [(d, m, up, v) for d, m, up, v in fams if m and not HC_MODEL.match(m)]
        cat = category(obj, ds[0].file, [m for _, m, _, _ in fams])
        if cat not in ("player", "wall"):
            continue
        main = next((m for d, m, up, v in fams if not up and install.has_model(m)), None)
        skip, structure = switched(install, {(d.file, d.object) for d in ds} | {(install.object_index().get(obj), obj)} - {(None, obj)})
        hc = {m for d in ds for m in d.models() if HC_MODEL.match(m)}      # (a ChildObject's own house draw)
        for d, m, up, v in fams:
            key = m.lower()
            if key in seen:
                seen[key]["objects"].append(obj)
                seen[key]["hc"] |= hc
                continue
            if not install.has_model(m):
                skipped.append((m, "%s: not in any archive" % obj))
                continue
            wallish = cat == "wall" or role_of(obj, m)[0] == "fortress_wall_hub"
            least = MIN_WALL_TRIS if wallish else MIN_TRIS
            bs = bodies(install, m, tallest=wallish) or structure and bodies(install, m, units=True) or []
            bs = [x for x in bs if x[0].upper() not in skip] + [x for x in bs if x[0].upper() in skip]
            if not bs or len(bs[0][1].tris) < least:
                skipped.append((m, "%s %s: no static body of %d+ triangles on a building sheet (%s)" % (
                    obj, d.tag, least, ", ".join("%s %d" % (n, len(x.tris)) for n, x, _, _, _ in bs[:3]) or "none")))
                continue
            twin = next((u for u in units if len(u["mesh"].tris) == len(bs[0][1].tris)
                         and same_body(u["mesh"], bs[0][1], 0.05)), None)
            if twin and m.lower().startswith(twin["source"].lower()):       # EBBbattleTwrS: EBBbattleTwr in snow
                skipped.append((m, "%s: the same body as %s (%s) - a variant, not a unit" % (obj, twin["source"], twin["objects"][0])))
                continue
            role, near = role_of(obj, m)
            if up:
                role = "fortress_upgrade"
                near = next((n for rx, n in UPGRADE_NEAREST if re.search(rx, d.tag + " " + m, re.I)), "fortress_statues")
            theirs = {x.lower() for x in d.models()} - {s.model.lower() for s in variation_states(d, m, v) if s.model}
            u = {"objects": [obj], "source": m, "tag": d.tag, "upgrade": up, "role": role, "nearest": near,
                 "main": m == main, "draw": d, "twin": twin and twin["source"], "rivals": rivals(bs),
                 "variation": v, "suffix": VARIATION_SUFFIX.get(v, "_" + (v or "").rsplit("_", 1)[-1].lower()) if v else "",
                 "theirs": theirs, "hc": set(hc)}
            for i, (n, mesh, sheet, nrm, grounded) in enumerate(bs):
                if i and (len(mesh.tris) < SECOND_TRIS or not grounded):     # a raised figure is not a building
                    continue
                unit = dict(u, target=n, mesh=mesh, sheet=sheet, normal=nrm, second=i > 0)
                units.append(unit)
                seen.setdefault(key, unit)
    drawn = {m.lower() for ds in by_obj.values() for d in ds for m in d.models()}
    by_src = {}
    for u in units:
        by_src.setdefault(u["source"].lower(), []).append(u)
    for u in units:
        u["name"] = _name(u, by_src)
        u["frames"] = frames(install, u["source"])
        u["frame"] = u["frames"].get(u["target"], IDENTITY)
        u["tilt"] = tilt(u["frame"])
        # the unit's own family: not another build variation's models, nor an empty stand-in model
        # (OBBFoundationX, drawn by five factions' foundations) that no redesign touches
        # (and only models the faction's own Draw modules show: not Blue Mountains' bb_tower03 beside GBFARTOWA)
        family = [m for m in own.body_draw_models(u["source"]) if m not in u["theirs"] and m in drawn
                  and not empty_model(own, m, install)]
        u["others"] = {m: own.other_model(m, faction) for m in family}
        u["others"] = {m: o for m, o in u["others"].items() if o}
        u["sheet_others"] = own.other_sheet(u["sheet"], faction)
        u["houses"] = sorted(set(own.house_models(u["source"])) | u["hc"], key=str.lower)
        u["lifecycle"] = [m for m in family if m != u["source"].lower()]
        u["exists"] = bool(install.owner(compiled_path(u["sheet"], ".dds")))
    names = [u["name"] for u in units]
    for u in units:                             # two objects of one role (MenWallHubSmall and
        stem = object_stem(sorted(u["objects"], key=len)[0])        # ...Upgradeable): the object's name
        if names.count(u["name"]) > 1 and u["main"] and not u["second"] and stem != u["name"] and stem not in names:
            u["name"] = stem
    names = [u["name"] for u in units]
    for u in units:                             # two families of one object named alike: add the tag
        if names.count(u["name"]) > 1 and not u["main"]:
            u["name"] += "_" + tag_stem(u["tag"])
    canonical(units)
    return units, skipped


def canonical(units):
    """One spelling per sheet: EA's meshes name GBFortress1.tga in either case (GBFBOil_SKN's pot:
    gbfortress1.tga); a recipe's `sheet` and its own_textures key take the spelling most units use."""
    spell = {}
    for u in units:
        for k in ("sheet", "normal"):
            if u.get(k):
                spell.setdefault(u[k].lower(), []).append(u[k])
    best = {low: max(set(v), key=lambda x: (v.count(x), x != x.lower())) for low, v in spell.items()}
    for u in units:
        for k in ("sheet", "normal"):
            if u.get(k):
                u[k] = best[u[k].lower()]


def _name(u, by_src):
    obj = sorted(u["objects"], key=len)[0]
    if u["second"]:
        base = next(x for x in by_src[u["source"].lower()] if not x["second"])
        return _name(base, by_src) + "_" + snake(u["target"].lower()).replace(" ", "_")
    if u["upgrade"]:
        return "fortress_" + tag_stem(u["tag"])
    if u.get("suffix"):                         # the second build variation: arrow_tower_b
        return _name(dict(u, suffix="", main=True), by_src) + u["suffix"]
    if u["role"] in ("fortress", "wall_end", "wall_segment", "wall_hub", "wall_gate", "wall_tower", "wall_postern",
                     "wall_trebuchet", "fortress_wall_hub"):
        return u["role"]
    stem = object_stem(obj)
    return stem if u["main"] else stem + "_" + tag_stem(u["tag"])


def run(faction, write=False):
    from .scaffold_write import execute
    return execute(faction, write)
