"""What our art costs the game's main thread to draw, against EA's (docs/PERFORMANCE.md §14).

The engine is bound by its main thread, and that thread pays per object and per mesh, not per
triangle (§10.3, §12; the GPU is 11-16 % busy). Per frame, at UltraHigh (shadow mapping):

  - every render object in view runs Visibility_Check and renderOneObject twice, once in the
    shadow-map pass and once in the main view: ~6.5 us each (§12). A Draw module showing a model
    is one render object, meshless ones included (our fire rigs, EA's OBBFoundationX);
  - every FX mesh shown is one draw in the main view (2.5 us, "Rendering mesh FXShader") and one
    in the shadow-map pass (1.8 us); a legacy (DX8) mesh draws once per material pass in the main
    view only (1.4 us, "Rendering mesh DX8Render"; Mesh::Render returns before the FX list in the
    shadow pass for non-FX meshes, §10.3);
  - meshes sharing a material are drawn in one batch (~7 us main + ~4.5 us shadow, self time,
    "RenderFXShaderBatch"): a mesh prototype is a material, so many copies of a building cost one
    batch per mesh, not one per copy;
  - the particle manager's render walks every system on the map: ~1.6 us per system plus ~0.5 us
    per live particle (a fit over 114 particlestats minutes, 2026-09-28..10-04, 0-290 systems and
    0-1,170 particles; r2 0.5). Their simulation (the manager update) is not timed and not counted.
Per-call figures: passtimers in the 2026-09-25 09:50 battle (2,261 main-view and 3,174 shadow-pass
meshes a frame), unchanged within 0.3 us in every session since (logs/gamepatch.log).

A mesh with W3D's hidden flag, a sub-object the INI hides, and a night window by day draw nothing.
EA's buildings carry one HLOD level each (W3D's distance LOD is unused in BFME); the engine's only
LOD is StaticModelLODMode, which swaps in <model>M / <model>L at Medium and Low settings and none at
High or UltraHigh.

    python3 -m sagekit.drawcost_report [<archive name part> ...] [--rows] [--json out.json]
"""
import re
import struct

from .formats.ini import parse_draws, parse_objects, strip
from .formats.w3d import (HLOD, HLOD_HEADER, MATERIAL_PASS, MESH, MESH_HEADER3, SHADERS, TEXTURE_IDS,
                          TEXTURE_STAGE, VERTEX_INFLUENCES, _cstr, chunks)

US = {"object": 6.5,            # Visibility_Check + renderOneObject, per render object per pass (§12)
      "fx_main": 2.5,           # Rendering mesh FXShader, main view
      "fx_shadow": 1.8,         # the same in UpdateShadowMap
      "dx8": 1.4,               # Rendering mesh DX8Render (main view only)
      "batch": 11.5,            # RenderFXShaderBatch self, main 7 + shadow 4.5, per material in view
      "particle": 0.5,          # particle manager render, per live particle (map-wide)
      "system": 1.6,            # the same, per particle system (map-wide; it walks every system)
      "gl_draw": 3.0}           # render thread: Apple's per-draw validation (§8), parallel to the above
HIDDEN, CAST_SHADOW = 0x00001000, 0x00008000
HLOD_LOD_ARRAY, HLOD_SUB_OBJECT_ARRAY_HEADER, HLOD_SUB_OBJECT, HLOD_AGGREGATE_ARRAY = 0x702, 0x703, 0x704, 0x705
NIGHT_KEYS = ("nightwindowname", "firewindowname", "glowwindowname")
STATES = {"healthy": (), "construction": ("PARTIALLY_CONSTRUCTED", "ACTIVELY_BEING_CONSTRUCTED"),
          "damaged": ("DAMAGED",), "really_damaged": ("REALLYDAMAGED",), "rubble": ("RUBBLE",),
          "night": ("NIGHT",)}


class MeshCost:
    def __init__(self, d, o, s):
        self.passes, self.textures, self.fx, self.blend, self.skinned = 0, 1, None, "opaque", False
        stages = []
        for t, o2, s2, _ in chunks(d, o + 8, o + 8 + s):
            if t == MESH_HEADER3:
                self.attr = struct.unpack_from("<I", d, o2 + 12)[0]
                self.name = _cstr(d[o2 + 16:o2 + 32]).upper()
                self.container = _cstr(d[o2 + 32:o2 + 48]).upper()
                self.tris, self.verts = struct.unpack_from("<II", d, o2 + 48)
            elif t == MATERIAL_PASS:
                self.passes += 1
                stages += [(o3, s3) for t3, o3, s3, _ in chunks(d, o2 + 8, o2 + 8 + s2) if t3 == TEXTURE_STAGE]
            elif t == SHADERS and s2 >= 16:
                dst, src = d[o2 + 8 + 3], d[o2 + 8 + 7]              # W3dShaderStruct DestBlend, SrcBlend
                self.blend = "opaque" if dst == 0 else ("additive" if (src, dst) == (1, 1) else "alpha")
            elif t == VERTEX_INFLUENCES:
                self.skinned = True
        m = re.search(rb"([A-Za-z0-9_]+)\.fx\0", d[o:o + 8 + s])
        self.fx = m.group(1).decode("latin-1") if m else None
        for o3, s3 in stages[:1]:                                   # distinct textures in stage 0
            for t4, o4, s4, _ in chunks(d, o3 + 8, o3 + 8 + s3):
                if t4 == TEXTURE_IDS and s4 > 4:
                    self.textures = len(set(struct.unpack_from("<%dI" % (s4 // 4), d, o4 + 8)))
        self.hidden = bool(self.attr & HIDDEN)
        self.house = self.name.startswith("HC_")

    @property
    def key(self):
        return "%s.%s" % (self.container, self.name) if self.container else self.name

    def draws(self):
        """(main-view draws, shadow-pass draws) when shown."""
        if self.fx:
            return 1, 1
        return max(1, self.passes) * self.textures, 0


class ModelCost:
    """A model file: its meshes, and which of them the top HLOD level draws."""

    def __init__(self, name, data):
        self.name, self.meshes, self.levels, self.drawn = name.upper(), {}, [], []
        for t, o, s, _ in chunks(data, 0, len(data)):
            if t == MESH:
                m = MeshCost(data, o, s)
                self.meshes[m.key] = m
            elif t == HLOD:
                for t2, o2, s2, _ in chunks(data, o + 8, o + 8 + s):
                    if t2 in (HLOD_LOD_ARRAY, HLOD_AGGREGATE_ARRAY):
                        size, subs = None, []
                        for t3, o3, s3, _ in chunks(data, o2 + 8, o2 + 8 + s2):
                            if t3 == HLOD_SUB_OBJECT_ARRAY_HEADER:
                                size = struct.unpack_from("<f", data, o3 + 12)[0]
                            elif t3 == HLOD_SUB_OBJECT:
                                subs.append(_cstr(data[o3 + 12:o3 + 44]).upper())
                        (self.levels.append((size, subs)) if t2 == HLOD_LOD_ARRAY else self.drawn.extend(subs))
        if self.levels:
            self.drawn += max(self.levels, key=lambda lv: lv[0] or 0.0)[1]
        elif not self.drawn:                                        # a lone mesh file
            self.drawn = list(self.meshes)

    def shown(self, night=(), hide=()):
        """The meshes drawn: top level, not hidden, not a night window by day, not hidden by the INI."""
        night = {n.upper() for n in night}
        hide = {n.upper() for n in hide}
        out = []
        for k in self.drawn:
            m = self.meshes.get(k)
            if m is None or m.hidden or m.name in hide or m.name in night:
                continue
            out.append(m)
        return out


def cost_of(models):
    """Totals for [(ModelCost, shown meshes, [live particles per system])]: one render object per entry."""
    c = dict(objects=0, meshes=0, main=0, shadow=0, tris=0, verts=0, house=0, skinned=0, rigs=0,
             house_objects=0, materials=set(), models=set(), systems=0, particles=0.0, us=0.0, gl=0)
    for model, shown, systems in models:
        c["objects"] += 1
        c["models"].add(model.name)
        c["rigs"] += not model.meshes                               # meshless: a fire rig, a foundation
        c["house_objects"] += bool(shown) and all(m.house for m in shown)
        for m in shown:
            main, shadow = m.draws()
            c["meshes"] += 1
            c["main"] += main
            c["shadow"] += shadow
            c["tris"] += m.tris
            c["verts"] += m.verts
            c["house"] += m.house
            c["skinned"] += m.skinned
            c["materials"].add((model.name, m.key))
            c["us"] += (US["fx_main"] if m.fx else US["dx8"] * main) + US["fx_shadow"] * shadow
        c["systems"] += len(systems)
        c["particles"] += sum(systems)
    c["us"] += 2 * US["object"] * c["objects"] + US["particle"] * c["particles"] + US["system"] * c["systems"]
    c["gl"] = c["main"] + c["shadow"]
    return c


# ------------------------------------------------------------------------------------ INI side
def pick(draw, flags):
    """The ModelConditionState the engine picks for `flags`: most flags in common, then fewest extra
    (Generals' SparseMatchFinder), the first in file order on a tie. NONE is no flag."""
    best, score = None, None
    for st in draw.states:
        if st.kind != "model":
            continue
        have = {f for f in st.flags if f != "NONE"}
        s = (len(have & flags), -len(have - flags))
        if score is None or s > score:
            best, score = st, s
    return best


def state_lines(lines, st):
    out = []
    for raw in lines[st.line:]:
        line = strip(raw)
        if line.lower() == "end":
            break
        out.append(line)
    return out


def particles_of(lines, draw, st):
    """ParticleSysBone systems of a state, with the default's (every state starts as its copy)."""
    found = []
    for s in [x for x in draw.states if x.kind == "model" and not x.flags and x is not st] + [st]:
        for line in state_lines(lines, s):
            words = line.replace("=", " ").split()
            if len(words) >= 3 and words[0].lower() == "particlesysbone":
                found.append(words[2])
    return found


def subobjects(lines, st, key):
    names = []
    for line in state_lines(lines, st):
        k, _, v = line.partition("=")
        if k.strip().lower() == key:
            names += v.split()
    return names


def object_blocks(text):
    """{object: [lines]} of each top-level Object/ChildObject block."""
    out, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^(Object|ChildObject|ObjectReskin)\s+(\S+)", line, re.I)
        if m:
            cur = out.setdefault(m.group(2), [])
        if cur is not None:
            cur.append(line)
    return out


def night_names(block_lines):
    names = []
    for line in block_lines:
        k, _, v = strip(line).partition("=")
        if k.strip().lower() in NIGHT_KEYS:
            names += v.split()
    return names


class Rates:
    """Live particles per system at steady state: mean BurstCount / mean BurstDelay x mean Lifetime."""

    def __init__(self, texts, aliases=None):
        self.blocks = {}
        for text in texts:
            for m in re.finditer(r"^[ \t]*(?:FX)?ParticleSystem[ \t]+(\S+)(.*?)^End\b", text, re.M | re.S | re.I):
                self.blocks.setdefault(m.group(1).lower(), m.group(2))
        self.aliases = {k.lower(): v.lower() for k, v in (aliases or {}).items()}

    def live(self, name):
        b = self.blocks.get(name.lower()) or self.blocks.get(self.aliases.get(name.lower(), ""))
        if b is None:
            return 0.0

        def mean(key, default):
            m = re.search(r"^\s*%s\s*=\s*([\d.]+)(?:\s+([\d.]+))?" % key, b, re.M | re.I)
            if not m:
                return default
            return (float(m.group(1)) + float(m.group(2) or m.group(1))) / 2
        if re.search(r"^\s*IsOneShot\s*=\s*Yes", b, re.M | re.I):
            return mean("BurstCount", 1.0)
        return mean("BurstCount", 1.0) / max(1.0, mean("BurstDelay", 1.0)) * mean("Lifetime", 30.0)


class Ini:
    """One INI text, parsed once: its lines, Draw modules by object and object blocks."""

    def __init__(self, text):
        self.lines = text.splitlines()
        self.blocks = object_blocks(text)
        self.parents = parse_objects(text)
        self.draws = {}
        for d in parse_draws(text):
            self.draws.setdefault(d.object, []).append(d)


def drawing(ini, obj, index):
    """(Ini, object) whose Draw modules `obj` draws: its own, else its parent's (a ChildObject or
    ObjectReskin), looked up in index {object: Ini} when defined in another file."""
    for _ in range(8):
        if ini is None or ini.draws.get(obj):
            break
        parent = ini.parents.get(obj)
        if not parent:
            break
        obj, ini = parent, (ini if parent in ini.blocks else index.get(parent))
    return ini, obj


def object_cost(ini, obj, find_model, rates, flags=(), index=None):
    """cost_of() the object's Draw modules in the state `flags` (ini: an Ini; a ChildObject draws its
    parent's, found through index {object: Ini}), or None when it draws nothing."""
    night = [] if "NIGHT" in flags else night_names(ini.blocks.get(obj, []))
    ini, obj = drawing(ini, obj, index or {})
    if ini is None:
        return None
    night += [] if "NIGHT" in flags else night_names(ini.blocks.get(obj, []))
    entries, flags = [], set(flags)
    for d in ini.draws.get(obj, []):
        st = pick(d, flags)
        if st is None or not st.model or st.model.lower() == "none":
            continue
        model = find_model(st.model)
        if model is None:
            continue
        hide = subobjects(ini.lines, st, "hidesubobject")
        show = {n.upper() for n in subobjects(ini.lines, st, "showsubobject")}
        shown = model.shown(night, [h for h in hide if h.upper() not in show])
        shown += [m for m in model.meshes.values() if m.name in show and m.hidden and m.key in model.drawn]
        entries.append((model, shown, [rates.live(p) for p in particles_of(ini.lines, d, st)]))
    return cost_of(entries) if entries else None
