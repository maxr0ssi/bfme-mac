#!/usr/bin/env python3
"""spellsurvey - every special power the game can cast, and what it does to the engine, from the
INSTALLED effective INI (our archives over EA's: sagekit-fx's fxlist/fxparticlesystem/system.ini, the
faction and hero packs), read the way sagekit reads it (sagekit/game.py, first archive wins).

    python3 tools/spellsurvey.py                 ranked table (every power with an engine cost)
    python3 tools/spellsurvey.py --all           every power, ranked
    python3 tools/spellsurvey.py --spell NAME    one power in detail (its closure: objects, weapons,
                                                 FX lists, particle systems, textures)
    python3 tools/spellsurvey.py --ea            EA's INI only (pristine), for comparison
    python3 tools/spellsurvey.py --map 6000      map side in world units (default 5000: mp eastfarthing
                                                 hills; the largest MP maps are 6000)

For each power (a module with SpecialPowerTemplate in any object) it follows OCLs, weapons (OCL
nuggets, projectiles, map-wide nuggets), created objects (their FireWeaponUpdate, OCL modules,
CloudBreak grids, ParticleSysBone, auras, lifetimes), FX lists and particle systems (slave and
per-particle systems), and counts: objects created per cast, particle systems and their steady-state
particles (BurstCount x Lifetime / BurstDelay, capped by SystemLifetime), scans over every object on
the map (Radius >= 5000) per cast and per second, fire-logic cells per second (FireLogicNugget:
pi r^2 in 10-unit cells, capped at the map), global weather changes, and the textures a first cast
loads (with their kind: a TGA with mips is the expensive one, docs/PERFORMANCE.md §13).
The ms columns are ESTIMATES from per-item costs measured elsewhere (§13, §19, §24); the counts are
exact readings of the INI. docs/PERFORMANCE.md §24 has the ranking and what was measured."""
import math
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sagekit.game import Install  # noqa: E402

TOP = {"Object", "ChildObject", "ObjectReskin", "FXList", "FXParticleSystem", "ParticleSystem",
       "ObjectCreationList", "Weapon", "ModifierList", "SpecialPower", "Science", "CommandButton",
       "CommandSet", "Upgrade", "AudioEvent", "MappedImage", "Armor", "Locomotor", "Multisound",
       "DialogEvent", "MusicTrack", "Rank", "ExperienceLevel", "CreateAHeroBling", "AutoResolveWeapon",
       "AutoResolveArmor", "AutoResolveBody", "Terrain", "Road", "HouseColor", "Video", "NewEvaEvent"}
KINDS = {"Object": "obj", "ChildObject": "obj", "ObjectReskin": "obj", "FXList": "fx",
         "FXParticleSystem": "ps", "ParticleSystem": "ps", "ObjectCreationList": "ocl", "Weapon": "wpn",
         "ModifierList": "mod", "SpecialPower": "sp", "Science": "sci"}
CREATE_KEYS = {"objectnames", "payload", "transport", "sunbeamobject", "taintobject", "spawntemplatename",
               "thingtospawn", "replacewith", "initialpayload", "replacementobjectname", "projectileobject",
               "projectiletemplatename", "objectname", "spawnobject"}
SKIP_KEYS = {"commandset", "selectportrait", "buttonimage", "triggeredby", "conflictswith", "upgradetogrant",
             "grantupgrade", "requiredsciences", "prerequisitesciences", "soundambient", "voiceselect",
             "displayname", "description", "evaevent", "ailuaeventslist", "removesupgrades", "upgradename"}
# per-item costs (ESTIMATES, ms): sources in docs/PERFORMANCE.md §24.3
C_OBJ = 0.15          # one object created with its modules and drawable
C_PSYS = 0.02         # one particle system created
C_PART = 0.0006       # one live particle, per drawn frame (update + draw; §13 particle manager)
C_SCAN = 0.002        # one object visited by a map-wide nugget (filter + modifier), §19
C_FIRECELL = 0.0005   # one fire-logic cell queried for height/water (§24.2, from the stall samples)
OBJECTS_ON_MAP = 1300  # 8-player game, 2026-10-05 session peak 1328
MAX_PARTICLES = 4000   # gamelod.ini MaxParticleCount at the highest preset: the manager drops the oldest


def strip(line):
    return re.split(r";|//", line, maxsplit=1)[0].rstrip()


class Ini:
    def __init__(self, pristine=False):
        self.inst = Install(pristine=pristine)
        self.defs, self.blocks, self.order = {}, {k: {} for k in set(KINDS.values())}, []
        self.parent = {}
        texts = []
        for m in self.inst.members("data/ini"):
            if m.endswith((".ini", ".inc")) and "\\campaigns\\" not in m:
                texts.append((m, self.inst.read(m).decode("latin-1")))
        for m, t in texts:
            for line in t.splitlines():
                mm = re.match(r"\s*#define\s+(\S+)\s+(\S+)", line)
                if mm and mm.group(1).upper() not in self.defs:
                    self.defs[mm.group(1).upper()] = mm.group(2)
        for m, t in texts:
            cur = None
            for line in t.splitlines():
                s = strip(line)
                if s and not s[0].isspace():
                    tok = s.split()
                    if tok[0] in TOP:
                        cur = None
                        kind = KINDS.get(tok[0])
                        if kind and len(tok) > 1 and tok[1] not in self.blocks[kind]:
                            cur = []
                            self.blocks[kind][tok[1]] = cur
                            self.order.append((kind, tok[1], m))
                            if tok[0] in ("ChildObject", "ObjectReskin") and len(tok) > 2:
                                self.parent[tok[1]] = tok[2]
                        continue
                if cur is not None and s:
                    cur.append(s.strip())
        self.lower = {k: {n.lower(): n for n in v} for k, v in self.blocks.items()}

    def val(self, v):
        return self.defs.get(v.upper(), v)

    def num(self, v, default=0.0):
        try:
            return float(self.val(v).rstrip("%"))
        except (ValueError, AttributeError):
            return default

    def lines(self, kind, name):
        """a block's lines; objects with their parents' lines first (ChildObject / ObjectReskin)"""
        out, seen = [], set()
        while name and name not in seen and name in self.blocks[kind]:
            seen.add(name)
            out = self.blocks[kind][name] + out
            name = self.parent.get(name) if kind == "obj" else None
        return out

    def find(self, kind, name):
        return self.lower[kind].get(name.lower())


def kv(line):
    if "=" not in line:
        return None, line.split()
    k, v = line.split("=", 1)
    return k.strip().lower(), v.split()


def modules(lines):
    """[(type, tag, [lines])] of an object's Behavior/Draw/Body/ClientUpdate modules (to the next one)"""
    out, cur = [], None
    for ln in lines:
        mm = re.match(r"(Behavior|Draw|Body|ClientUpdate)\s*=\s*(\S+)\s*(\S*)", ln, re.I)
        if mm:
            cur = (mm.group(2), mm.group(3), [])
            out.append(cur)
        elif cur:
            cur[2].append(ln)
    return out


class Cost:
    def __init__(self):
        self.objects = 0.0          # created per cast
        self.grid = 0               # map-wide grid objects
        self.psys = 0.0             # particle systems started per cast
        self.particles = 0.0        # steady-state particles while active
        self.scans_cast = 0         # map-wide nuggets at cast
        self.scans_ps = 0.0         # map-wide nuggets per second while active
        self.fire_ps = 0.0          # fire-logic cells per second (flag-0 circles)
        self.fire_cast = 0.0
        self.weather = set()
        self.notes = []
        self.textures = set()
        self.duration = 0.0
        self.seen = set()

    def cast_ms(self):
        return ((self.objects + self.grid) * C_OBJ + self.psys * C_PSYS + self.scans_cast * OBJECTS_ON_MAP * C_SCAN
                + self.fire_cast * C_FIRECELL + (2 * OBJECTS_ON_MAP * C_SCAN if self.weather else 0))

    def spike_ms(self):          # the worst single frame while active (one periodic shot)
        per_shot = 0.0
        if self.fire_ps:
            per_shot += self.fire_ps * 2 * C_FIRECELL
        if self.scans_ps:
            per_shot += OBJECTS_ON_MAP * C_SCAN
        return max(self.cast_ms(), per_shot)

    def frame_ms(self):          # added to every frame while active
        per_s = self.scans_ps * OBJECTS_ON_MAP * C_SCAN + self.fire_ps * C_FIRECELL
        return min(self.particles, MAX_PARTICLES) * C_PART + per_s / 30.0


class Walker:
    def __init__(self, ini, map_side):
        self.ini, self.map_side = ini, map_side
        self.cells = (map_side / 10.0) ** 2

    def ps_particles(self, name, depth=0):
        ln = self.ini.lines("ps", name)
        f = {}
        for s in ln:
            k, v = kv(s)
            if k and v and k not in f:
                f[k] = v
        def rng(k, d):
            v = f.get(k)
            if not v:
                return d
            a = [self.ini.num(x, d) for x in v[:2]]
            return sum(a) / len(a)
        life, burst, delay = rng("lifetime", 30), rng("burstcount", 1), rng("burstdelay", 1)
        sysl = rng("systemlifetime", 0)
        one = f.get("isoneshot", ["no"])[0].lower() == "yes"
        rate = burst / max(delay, 1.0)
        live = burst if one else rate * (min(life, sysl) if sysl > 0 else life)
        for k in ("slavesystem", "perparticleattachedsystem"):
            if k in f and depth < 2 and self.ini.find("ps", f[k][0]):
                sub = self.ps_particles(self.ini.find("ps", f[k][0]), depth + 1)[0]
                live += sub * (live if k == "perparticleattachedsystem" else 1)
        tex = f.get("particlename", [None])[0]
        return live, tex

    def walk(self, kind, name, cost, mult=1.0, depth=0):
        name = self.ini.find(kind, name)
        if not name or depth > 8 or (kind, name) in cost.seen:
            return
        cost.seen.add((kind, name))
        ln = self.ini.lines(kind, name)
        if kind == "ps":
            live, tex = self.ps_particles(name)
            cost.psys += mult
            cost.particles += live * mult
            if tex and re.search(r"\.(tga|dds)$", tex, re.I):
                cost.textures.add(tex.lower())
            return
        if kind == "wpn":
            self.weapon(name, ln, cost, mult, depth)
            return
        if kind == "obj":
            self.obj(name, ln, cost, mult, depth)
            return
        # OCL, FX list, modifier list and anything else: follow names; CreateObject nuggets by Count
        nug = []
        for s in ln + ["End"]:
            k, v = kv(s)
            if k is None:                                  # a nugget opens or closes: settle the last
                count = next((self.ini.num(v2[0], 1) for k2, v2 in nug if k2 == "count" and v2), 1)
                for k2, v2 in nug:
                    if k2 in ("objectnames", "payload"):
                        objs = [o for o in v2 if self.ini.find("obj", o)]
                        for o in objs:                     # several names: one of them (random)
                            n = count / len(objs) if k2 == "objectnames" else (self.ini.num(v2[1], 1) if len(v2) > 1 else 1)
                            cost.objects += n * mult
                            self.walk("obj", o, cost, mult * n, depth + 1)
                    else:
                        self.follow(k2, v2, cost, mult, depth)
                nug = []
            else:
                nug.append((k, v))

    def follow(self, k, v, cost, mult, depth):
        if k is None or k in SKIP_KEYS or not v:
            return
        for t in v:
            for kind in ("ocl", "fx", "ps", "wpn"):
                if self.ini.find(kind, t):
                    self.walk(kind, t, cost, mult, depth + 1)
            if k in CREATE_KEYS and self.ini.find("obj", t):
                cost.objects += mult
                self.walk("obj", t, cost, mult, depth + 1)

    def weapon(self, name, ln, cost, mult, depth):
        delay, nug, radius = 0.0, None, {}
        for s in ln:
            k, v = kv(s)
            if k is None and v and v[0].endswith("Nugget"):
                nug = v[0]
            elif k == "delaybetweenshots" and v:
                delay = self.ini.num(v[0])
            elif k == "radius" and v and nug:
                radius[nug] = max(radius.get(nug, 0), self.ini.num(v[0]))
            elif k == "end":
                nug = None
            else:
                self.follow(k, v, cost, mult, depth)
        for nug, r in radius.items():
            if nug == "FireLogicNugget":
                cells = min(math.pi * (r / 10) ** 2, self.cells)
                cost.fire_cast += cells * mult
                cost.notes.append("%s: FireLogicNugget r=%g (%d cells)" % (name, r, cells))
            elif r >= 5000:
                cost.scans_cast += mult
                cost.notes.append("%s: %s r=%g (every object on the map)" % (name, nug, r))
        cost.weapon_delay = getattr(cost, "weapon_delay", {})
        cost.weapon_delay[name] = delay

    def obj(self, name, ln, cost, mult, depth):
        life = 0.0
        for typ, tag, body in modules(ln):
            t = typ.lower()
            f = {}
            for s in body:
                k, v = kv(s)
                if k:
                    f.setdefault(k, v)
                if k == "particlesysbone" and len(v) > 1:
                    self.walk("ps", v[1], cost, mult, depth + 1)
                elif k == "model" and v and v[0].lower() != "none":
                    cost.models = getattr(cost, "models", set()) | {v[0].lower()}
            if t in ("lifetimeupdate", "deletionupdate") and "minlifetime" in f:
                life = max(life, self.ini.num(f["minlifetime"][0]))
            if t == "cloudbreakspecialpower" and "sunbeamobject" in f:
                sp = self.ini.num(f.get("objectspacing", ["0"])[0])
                n = (int(math.ceil((self.map_side - sp) / sp)) - 1) ** 2 if sp > 0 else 0
                cost.grid += n * mult
                cost.notes.append("%s: CloudBreak grid of %s every %g units: %d objects on a %g-unit map"
                                  % (name, f["sunbeamobject"][0], sp, n, self.map_side))
                self.walk("obj", f["sunbeamobject"][0], cost, mult * n, depth + 1)
            if t == "fireweaponupdate":
                w = None
                for s in body:
                    k, v = kv(s)
                    if k == "weaponname" and v:
                        w = v[0]
                    if k == "oneshot" and v and w:
                        before = (cost.scans_cast, cost.fire_cast)
                        self.walk("wpn", w, cost, mult, depth + 1)
                        if v[0].lower() == "no":
                            d = getattr(cost, "weapon_delay", {}).get(self.ini.find("wpn", w) or w, 0) or 1000
                            cost.scans_ps += (cost.scans_cast - before[0]) * 1000.0 / d
                            cost.fire_ps += (cost.fire_cast - before[1]) * 1000.0 / d
                            cost.scans_cast, cost.fire_cast = before
                        w = None
            if t == "attributemodifierauraupdate":
                r, d = self.ini.num(f.get("range", ["0"])[0]), self.ini.num(f.get("refreshdelay", ["2000"])[0])
                if r >= 5000:
                    cost.scans_ps += mult * 1000.0 / max(d, 1)
                    cost.notes.append("%s: aura r=%g every %g ms" % (name, r, d))
            for k, v in f.items():
                if k not in ("particlesysbone", "weaponname", "model"):
                    self.follow(k, v, cost, mult, depth)
        cost.duration = max(cost.duration, life)


def powers(ini):
    """[(power, owner object, module type, [lines])] for every module naming a SpecialPowerTemplate"""
    out = []
    for kind, name, member in ini.order:
        if kind != "obj":
            continue
        for typ, tag, body in modules(ini.blocks["obj"][name]):
            sp = [kv(s)[1][0] for s in body if kv(s)[0] == "specialpowertemplate" and kv(s)[1]]
            if sp:
                out.append((sp[0], name, typ, body, member))
    return out


def science_cost(ini, power):
    req = None
    for s in ini.lines("sp", power):
        k, v = kv(s)
        if k == "requiredsciences" and v:
            req = v[0]
    if not req:
        return ""
    for s in ini.lines("sci", req):
        k, v = kv(s)
        if k == "sciencepurchasepointcostmp" and v:
            return "%g" % ini.num(v[0])
    return "?"


def survey(ini, map_side):
    w = Walker(ini, map_side)
    rows = []
    for power, owner, typ, body, member in powers(ini):
        c = Cost()
        for s in body:
            k, v = kv(s)
            if k == "changeweather" and v:
                c.weather.add(v[0])
            if k == "weatherduration" and v:
                c.duration = max(c.duration, ini.num(v[0]))
            w.follow(k, v, c, 1.0, 0)
        if typ.lower() == "cloudbreakspecialpower":
            w.obj(owner + "/" + power, ["Behavior = %s x" % typ] + body, c, 1.0, 0)
        rows.append((power, owner, typ, c, member))
    return rows


def model_textures(ini, models):
    from sagekit.formats.w3d import texture_names
    out = set()
    for m in models:
        try:
            out |= {t.lower() for t in texture_names(ini.inst.read(ini.inst.model_path(m)))}
        except FileNotFoundError:
            pass
    return out


def textures_cost(ini, texs):
    out = []
    for t in sorted(texs):
        stem = os.path.splitext(t)[0]
        for ext in (".dds", ".tga"):
            m = "art\\compiledtextures\\%s\\%s%s" % (stem[:2], stem, ext)
            a = ini.inst.owner(m)
            if a:
                out.append((t, ext, len(a.read(m))))
                break
        else:
            out.append((t, "missing", 0))
    return out


def main():
    args = sys.argv[1:]
    ea = "--ea" in args
    map_side = float(args[args.index("--map") + 1]) if "--map" in args else 5000.0
    one = args[args.index("--spell") + 1] if "--spell" in args else None
    ini = Ini(pristine=ea)
    rows = survey(ini, map_side)
    if one:
        for power, owner, typ, c, member in rows:
            if power.lower() == one.lower():
                print("%s  (%s in %s, %s)" % (power, typ, owner, member.split("\\")[-1]))
                print("  objects per cast %.0f + grid %d, particle systems %.0f, steady particles %.0f" %
                      (c.objects, c.grid, c.psys, c.particles))
                print("  map-wide scans: %d at cast, %.2f/s; fire cells %.0f at cast, %.0f/s; weather %s; duration %g ms" %
                      (c.scans_cast, c.scans_ps, c.fire_cast, c.fire_ps, ",".join(c.weather) or "-", c.duration))
                print("  estimate: cast %.1f ms, worst frame %.1f ms, +%.2f ms every frame while active" %
                      (c.cast_ms(), c.spike_ms(), c.frame_ms()))
                for n in c.notes:
                    print("  " + n)
                print("  closure: " + ", ".join("%s:%s" % kn for kn in sorted(c.seen)))
                for t, ext, size in textures_cost(ini, c.textures | model_textures(ini, getattr(c, "models", ()))):
                    print("  texture %s %s %d KB" % (t, ext, size // 1024))
        return
    rows.sort(key=lambda r: -(r[3].spike_ms() + 30 * r[3].frame_ms()))
    print("%-34s %-22s %-24s %4s %7s %6s %6s %7s %6s %8s %7s %7s %6s" %
          ("power", "owner", "module", "MP", "objects", "grid", "psys", "parts", "scan/s", "fire/s",
           "cast", "spike", "+frame"))
    for power, owner, typ, c, member in rows:
        if "--all" not in args and c.spike_ms() < 1 and c.frame_ms() < 0.2:
            continue
        print("%-34s %-22s %-24s %4s %7.0f %6d %6.0f %7.0f %6.2f %8.0f %7.1f %7.1f %6.2f%s" %
              (power[:34], owner[:22], typ[:24], science_cost(ini, power), c.objects, c.grid, c.psys,
               c.particles, c.scans_ps, c.fire_ps, c.cast_ms(), c.spike_ms(), c.frame_ms(),
               ("  weather " + ",".join(sorted(c.weather))) if c.weather else ""))


if __name__ == "__main__":
    main()
