"""Build one building from the installed game, step by step (host side; Blender runs the heavy
steps through sagekit/blender/run.py). Each step is a small class; `Pipeline.run(first, last)`
runs a slice, so iterating on a design is `--from geometry --to render`.

    extract    the originals from the game's archives (never from ours) + the atlas's 4x upscale
    geometry   design() merged into the target mesh, its own UV layout          (Blender)
    bake       G-buffers into that layout                                       (Blender)
    paint      the style's layer stack -> diffuse DDS + normal TGA              (Blender)
    export     the scene as W3D                                                 (Blender)
    night      the recipe's windows and doors cast onto our body as night lights (nightlights.py)
    fixup      repair the export, point the target at its own textures, splice it into EA's file
    derive     EA's damaged-but-standing models with our body in the state texture spliced in
    lifecycle  EA's construction / really damaged / rubble models with our body in EA's pieces (Blender)
    ship       the files that ship, at their archive paths, under out/
    shared     shared EA sheets in those files -> the faction's recoloured copies (sharedsheets.py)
    fire       the recipe's fire_points as bones of a meshless rig for EA's particle systems (fire.py)
    ini        the faction INIs with our texture swaps next to EA's, LOD swapping off, fire Draws
    cache      a pristine asset.dat copy with the building's cache ops, verified
    checks     the standard check suite                                         (Blender)
    render     original vs new at the building's views, side by side            (Blender)
"""
import contextlib
import fcntl
import json
import os
import re
import shutil
import subprocess
import time

from . import paths
from .formats.assetcache import AssetCache
from .formats.ini import apply_ops
from .formats.textures import compiled_path, dds_to_tga24, normal_member, sheet_member, tga_to_dds
from .formats.w3d import W3DFile, fix, splice_mesh
from .formats.w3dframes import moved
from .game import Install
from .workspace import Workspace

RUN_PY = os.path.join(paths.REPO, "sagekit", "blender", "run.py")
REALESRGAN = os.path.join(paths.REPO, "downloads", "realesrgan", "realesrgan-ncnn-vulkan")


BLENDER_SLOTS = int(os.environ.get("SAGEKIT_BLENDER_SLOTS", "4"))


class StepFailed(Exception):
    pass


@contextlib.contextmanager
def blender_slot():
    """At most BLENDER_SLOTS Blender processes across every build on this Mac (parallel builds
    share one GPU and the CPU cores); waits for a free slot."""
    os.makedirs(paths.BUILD, exist_ok=True)
    while True:
        for i in range(BLENDER_SLOTS):
            fh = open(os.path.join(paths.BUILD, ".blender-slot-%d" % i), "w")
            try:
                fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                fh.close()
                continue
            try:
                yield
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)
                fh.close()
            return
        time.sleep(2)


class Step:
    name = None

    def __init__(self, pipeline):
        self.p = pipeline
        self.b, self.ws = pipeline.building, pipeline.ws

    def run(self):
        raise NotImplementedError

    def blender(self, job, blend=None, log_as=None, **opts):
        cmd = [paths.BLENDER, "-b"] + ([blend] if blend else []) + ["--python", RUN_PY, "--", job, self.b.id]
        cmd += ["%s=%s" % kv for kv in opts.items()]
        while game_running() and not self.p.force:
            time.sleep(10)                      # a match is on: wait rather than take its CPU
        with blender_slot():
            r = subprocess.run(cmd, capture_output=True, text=True)
        log = os.path.join(self.ws.logs, "%s.log" % (log_as or job))
        with open(log, "w") as fh:
            fh.write(r.stdout + r.stderr)
        if "JOB OK" not in r.stdout or "Traceback" in r.stdout + r.stderr:
            raise StepFailed("%s failed - see %s\n%s" % (job, log, (r.stdout + r.stderr)[-3000:]))
        return r.stdout

    def tool(self, cmd):
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            raise StepFailed("%s\n%s" % (" ".join(cmd), r.stderr[-2000:]))
        return r.stdout


class Extract(Step):
    name = "extract"

    def source(self):
        """The model this building redesigns: EA's, or its base building's finished one."""
        if self.b.base:
            from .registry import load
            path = Workspace(load(self.b.base)).shipped_model
            if not os.path.exists(path):
                raise StepFailed("build %s first: %s redesigns its finished model" % (self.b.base, self.b.id))
            return open(path, "rb").read()
        return self.p.install.read(self.p.install.model_path(self.b.source))

    def run(self):
        g, b = self.p.install, self.b
        a, master = b.sheet_atlas, b.style.atlas
        model = self.source()
        if b.own_model and not b.base:          # an own copy (sagekit/owncopy.py); EA's stays for the before render
            from .owncopy import check_free, prepare
            with open(self.ws.reference_model, "wb") as fh:
                fh.write(model)
            try:
                check_free(b, g, [b.source] + b.derived_models(g))
                model = prepare(b, b.source, model)
            except ValueError as e:
                raise StepFailed(str(e))
        with open(self.ws.source_model, "wb") as fh:
            fh.write(model)
        body = W3DFile(model).meshes.get(b.target)
        if body is None:
            raise StepFailed("%s has no mesh %s" % (b.source, b.target))
        if a.texture.lower() not in [t.lower() for t in body.textures]:
            raise StepFailed("%s is painted from %s, not %s - set `sheet`" % (b.target, body.textures, a.texture))
        if a.normal and a.normal.lower() not in [t.lower() for t in body.textures]:
            raise StepFailed("%s has no normal map %s - set `sheet_normal = None`" % (b.target, a.normal))
        variants = b.variants(g)
        with open(self.ws.path("work", "variants.json"), "w") as fh:
            json.dump(variants, fh, indent=1)
        normals = b.normal_variants(g)                  # our normal map under the states' names
        with open(self.ws.path("work", "normal_variants.json"), "w") as fh:
            json.dump(normals, fh, indent=1)
        # a `base` building redesigns a mesh the game may show per upgrade level, but the house-colour
        # model is always drawn: its cloth stays on the mesh, unless the mesh is always shown too
        house = b.house_model(g) if b.house_tags and not b.per_level else None
        if house:
            with open(self.ws.path("work", "house.json"), "w") as fh:
                json.dump(house, fh, indent=1)
        elif os.path.exists(self.ws.path("work", "house.json")):
            os.remove(self.ws.path("work", "house.json"))
        bodies = b.derived_bodies(g)
        with open(self.ws.path("work", "derived.json"), "w") as fh:
            json.dump({m: bodies.get(m) for m in b.derived_models(g)}, fh, indent=1)
        members = [(sheet_member(g, a.texture) or compiled_path(a.texture, ".dds"), self.ws.atlas_dds)]
        skl = W3DFile(model).skeleton()
        if skl:                                 # a skinned model: its skeleton is a file of its own
            members.append((g.model_path(skl[:-4]), os.path.join(self.ws.src, skl)))
        if a.normal:
            members.append((normal_member(g, a.normal), self.ws.atlas_normal))
        if b.two_sheets:
            members.append((normal_member(g, master.normal), self.ws.master_normal))
        for member, dest in members:
            if member.endswith(".tga") and dest.endswith(".dds"):     # a TGA-only sheet: kept as a DDS
                tga_to_dds(g.read(member), dest)
            elif member.endswith(".dds") and dest.endswith(".tga"):   # a DDS-only normal map: kept as a TGA
                dds_to_tga24(g.read(member), dest)
            else:
                with open(dest, "wb") as fh:
                    fh.write(g.read(member))
            print("  %-48s <- %s" % (os.path.relpath(dest, self.ws.root), os.path.basename(g.owner(member).path)))
        sheets = [a.texture] + list(variants)
        if b.two_sheets:
            sheets += [master.texture] + [b.style.master_variant(v) for v in variants]
        for t in dict.fromkeys(sheets):
            self.upscale(sheet_member(g, t) or compiled_path(t, ".dds"), self.ws.upscale_of(t))
        print("  sheet %s%s; variants: %s" % (a.texture, " (+ %s for new faces)" % master.texture if b.two_sheets else "",
                                              ", ".join("%s -> %s" % kv for kv in variants.items()) or "none"))

    def upscale(self, member, out_png):
        """The sheet decoded and upscaled 4x (kept: slow-ish and deterministic); its cut-out alpha
        beside it when it has any (sagekit/alpha.py: Real-ESRGAN sees the colour only)."""
        from .alpha import upscale as upscale_alpha
        ext = os.path.splitext(member)[1].lower()                      # .dds, or a TGA-only sheet's .tga
        upscale_alpha(self.p.install.read(member), out_png, self.b.style.atlas.upscale, ext)
        if os.path.exists(out_png):
            return
        if not os.path.exists(REALESRGAN):
            raise StepFailed("Real-ESRGAN not found at %s (see assets/README.md)" % REALESRGAN)
        dds, png = out_png[:-7] + ext, out_png[:-7] + ".png"
        with open(dds, "wb") as fh:
            fh.write(self.p.install.read(member))
        self.tool(["magick", dds + "[0]", "-alpha", "off", png])
        self.tool([REALESRGAN, "-i", png, "-o", out_png, "-n", "realesrgan-x4plus",
                   "-m", os.path.join(os.path.dirname(REALESRGAN), "models")])
        print("  upscaled", os.path.relpath(out_png, self.ws.root))


class Geometry(Step):
    name = "geometry"

    def run(self):
        out = self.blender("geometry")
        print("\n".join("  " + x for x in out.splitlines() if x.startswith(("TRIS", "BBOX", "Z growth", "islands", "loose"))))


class Bake(Step):
    name = "bake"

    def run(self):
        out = self.blender("bake", blend=self.ws.stage("geometry"))
        print("\n".join("  " + x for x in out.splitlines() if x.startswith("baked")))


class Paint(Step):
    name = "paint"

    def run(self):
        out = self.blender("paint", blend=self.ws.stage("geometry"))
        print("\n".join("  " + x for x in out.splitlines() if "wrote" in x))


class Export(Step):
    name = "export"

    def run(self):
        os.makedirs(os.path.dirname(self.ws.export_model), exist_ok=True)
        self.blender("export", blend=self.ws.stage("geometry"))


class Night(Step):
    """Night lights from our design, glowing in the faction's look (sagekit/nightlights.py)."""
    name = "night"

    def run(self):
        from . import nightlights
        nightlights.run(self)


class Fixup(Step):
    """Only the redesigned mesh ships from Blender: the export is repaired against the original
    (w3d.fix), its target mesh re-pointed at our textures, and spliced into EA's own file - every
    other chunk (other meshes, skinned ones included, hierarchy, HLOD) stays EA's bytes."""
    name = "fixup"

    def run(self):
        orig = open(self.ws.source_model, "rb").read()
        fixed, report = fix(orig, open(self.ws.export_model, "rb").read(), self.b.renames())
        print("\n".join("  " + x for x in report if x.startswith(self.b.target)))
        mesh = W3DFile(fixed).meshes[self.b.target].bytes
        out = splice_mesh(orig, self.b.target, mesh, self.ws.container)
        from .nightlights import carry          # night meshes: our lights, in the faction's look
        out = carry(self.b, self.b.source, out, install=self.p.install)
        os.makedirs(os.path.dirname(self.ws.shipped_model), exist_ok=True)
        with open(self.ws.shipped_model, "wb") as fh:
            fh.write(out)


class Derive(Step):
    """The damaged-but-standing models (EA's D1): our new body in the matching state texture,
    spliced into EA's file in place of their body mesh (under EA's name for it, in its bone's
    frame); their debris and animation untouched. A chained recipe splices into its base's
    derived file, and passes on the ones whose mesh is not its body there as the base made them."""
    name = "derive"

    def run(self):
        names = self.ws.own_names                       # diffuse, normal, state variants, state normals
        export = open(self.ws.export_model, "rb").read()
        keep = {self.p.install.model_path(self.b.shipped_name(m)).lower()
                for m in [self.b.source] + list(self.ws.derived) + self.ws.lifecycle}
        from .fire import members as fire               # the fire rig (the fire step writes it)
        keep |= fire(self.b)
        models = self.ws.path("out", "art", "w3d")
        for root, _, files in os.walk(models):          # models an earlier run derived and this one does not
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), self.ws.path("out")).replace(os.sep, "\\").lower()
                if rel not in keep:
                    os.remove(os.path.join(root, f))
                    print("  removed %s (no longer derived)" % rel)
        for model, mesh in self.ws.derived_bodies.items():
            member = self.p.install.model_path(self.b.shipped_name(model))
            orig = self.start(model)
            if self.b.own_model and not self.b.base:
                from .owncopy import prepare
                orig = prepare(self.b, model, orig)
            with open(self.ws.path("src", model.lower() + ".w3d"), "wb") as fh:
                fh.write(orig)
            dest = self.ws.out(member)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            if mesh is None:
                with open(dest, "wb") as fh:
                    fh.write(orig)
                print("  %s: as %s derived it" % (member, self.b.base))
                continue
            ea = W3DFile(orig).meshes[mesh]
            renames = [(mesh, t, names[t.lower()]) for t in ea.textures if t.lower() in names]
            body = moved(export, self.b.target, mesh, self.b.bodies_in(self.p.install, model)[mesh])
            fixed, _ = fix(orig, body, renames)
            out = splice_mesh(orig, mesh, W3DFile(fixed).meshes[mesh].bytes, ea.container)
            from .nightlights import carry      # night meshes: our lights through the body's frame
            out = carry(self.b, model, out, install=self.p.install)
            with open(dest, "wb") as fh:
                fh.write(out)
            print("  %s: %s%s -> %s" % (member, "" if mesh == self.b.target else mesh + ": ", ", ".join(ea.textures),
                                        ", ".join(r[2] for r in renames)))

    def start(self, model):
        """The file our body goes into: the base's derived one for a chained recipe, else EA's."""
        if self.b.base:
            base = Workspace(self.b.base_building())
            if model in base.derived:
                path = base.out(self.p.install.model_path(model))
                if not os.path.exists(path):
                    raise StepFailed("build %s first: %s splices into its %s" % (self.b.base, self.b.id, model))
                return open(path, "rb").read()
        return self.p.install.read(self.p.install.model_path(model))


class Lifecycle(Step):
    """EA's construction, really damaged and rubble models rebuilt around our body, following EA's
    pieces, cuts and animations (sagekit/lifecycle.py)."""
    name = "lifecycle"

    def run(self):
        from . import lifecycle
        lifecycle.run(self)


class Ship(Step):
    name = "ship"

    def run(self):
        from . import capture                   # a capturable building's dress: a model of its own
        capture.write_house(self.b, self.p.install, self.ws)
        files = [(self.b.own_diffuse, ".dds")] + ([(self.b.own_normal, ".tga")] if self.b.own_normal else [])
        files += [(v, ".dds") for v in self.ws.variants.values()]
        files += [(v, ".tga") for v in self.ws.normal_variants.values()]
        from .nightlights import ship as night          # the faction's night-light texture
        files += night(self.ws)
        keep = {os.path.normcase(self.ws.shipped_texture(name, ext)) for name, ext in files}
        for root, _, names in os.walk(self.ws.path("out", "art", "compiledtextures")):
            for f in names:                         # textures an earlier run shipped and this one does not
                if os.path.normcase(os.path.join(root, f)) not in keep:
                    os.remove(os.path.join(root, f))
                    print("  removed %s (no longer shipped)" % f)
        copies = {v.lower(): self.b.own_normal for v in self.ws.normal_variants.values()}
        for name, ext in files:                         # a state normal: a copy of ours
            src = self.ws.tex(copies.get(name.lower(), name)[:-4].lower() + ext)
            dest = self.ws.shipped_texture(name, ext)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src, dest)
        for root, _, files in os.walk(self.ws.path("out")):
            for f in sorted(files):
                p = os.path.join(root, f)
                print("  %-60s %10d" % (os.path.relpath(p, self.ws.path("out")), os.path.getsize(p)))


class Shared(Step):
    """Meshes we ship painted from a sheet other factions draw too get the faction's own
    recoloured copy of it (sagekit/sharedsheets.py); after ship, which clears textures it does not know."""
    name = "shared"

    def run(self):
        from . import sharedsheets
        sharedsheets.run(self)


class Fire(Step):
    """The recipe's fire_points: a meshless rig model whose bones carry EA's particle systems
    (sagekit/fire.py); the Draw modules that show them come with the ini step."""
    name = "fire"

    def run(self):
        from . import fire
        fire.run(self)


class Ini(Step):
    name = "ini"

    def run(self):
        g = self.p.install
        for member, ops in self.b.ini_ops(g, self.ws.variants).items():
            text = apply_ops(g.read(member).decode("latin-1"), ops)
            dest = self.ws.out(member)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w", encoding="latin-1", newline="") as fh:
                fh.write(text)
            print("  %s (%d edits)" % (member, len(ops)))


class Cache(Step):
    name = "cache"

    def run(self):
        shutil.rmtree(self.ws.path("cache"), ignore_errors=True)
        routed = self.p.install.route_cache_ops(self.b.cache_ops(self.ws.variants, self.ws.derived + self.ws.lifecycle))
        for live, ops in routed.items():
            cache = AssetCache(self.p.install.asset_caches()[live].path)
            cache.path = self.ws.cache_copy(live)
            print("  %s:" % os.path.relpath(live, paths.GAMEDIRS["bfme2"] + "/.."))
            for line in apply_cache_ops(cache, ops, self.shipped):
                print("    " + line)
            for op in ops:
                if op[0] in ("patch", "model") and cache.stale_entries(self.shipped(op[1]), op[1]):
                    raise StepFailed("cache record of %s still stale after patching" % op[1])
            os.makedirs(os.path.dirname(cache.path), exist_ok=True)
            cache.save(backup=False)
        print("  records match the files")

    def shipped(self, model_file):
        return self.ws.out(self.p.install.model_path(model_file[:-4]))


def apply_cache_ops(cache, ops, model_path):
    """model_path(model file name) -> the file whose layout the record must match."""
    lines = []
    for op in ops:
        if op[0] == "model":
            lines += cache.add_model(op[1], op[2], model_path(op[1]))
        elif op[0] == "texture":
            lines += cache.add_texture(*op[1:])
        elif op[0] == "patch":
            lines += cache.patch_model(model_path(op[1]), op[1])
    return lines


class Checks(Step):
    name = "checks"

    def run(self):
        ok = self.ws.path("work", "checks.ok")
        if os.path.exists(ok):
            os.remove(ok)
        out = self.blender("checks")
        open(ok, "w").write(out.split("checks passed")[0].splitlines()[-1] + " checks passed\n")
        print("\n".join("  " + x for x in out.splitlines() if x.startswith(("FAIL", "INFO")) or "checks passed" in x))


class Render(Step):
    name = "render"
    FONT = paths.FONT                   # (the Mac's Arial Bold; DejaVu on Linux)

    def run(self, views=None, res="1600x1100", spp="64"):
        """The healthy model, then every derived model that carries this building's body (EA's
        original of it against ours: renders/compare_<model>_<view>.png)."""
        views = views or ",".join(self.b.views or ("rts", "close", "ingame"))
        r = self.ws.path("renders")
        pairs = [("", self.ws.reference_model, self.ws.shipped_model, self.b.target)]
        for model, body in self.ws.derived_bodies.items():
            if body:
                member = self.p.install.model_path(model)
                ea = self.ws.path("work", "ref", model.lower() + ".w3d")
                os.makedirs(os.path.dirname(ea), exist_ok=True)
                with open(ea, "wb") as fh:
                    fh.write(self.p.install.read(member))
                pairs.append((model.lower() + "_", ea, self.ws.out(self.p.install.model_path(self.b.shipped_name(model))), body))
        for tag, orig, new, body in pairs:
            for who, model in (("orig", orig), ("new", new)):
                self.blender("render", log_as="render_%s%s" % (tag, who), w3d=model, prefix=os.path.join(r, who + "_" + tag),
                             views=views, res=res, spp=spp, frame=body, **self.references(model, recoloured=who == "new"))
            self.labelled(r, views, res, tag)
        from . import fire, lifecycle, nightlights
        lifecycle.render(self)                  # the construction / damaged / rubble models
        nightlights.render(self)                # night views: EA's night meshes against ours
        fire.render(self)                       # the fire points marked over the render

    def references(self, model, recoloured=False):
        """{texture: file} for the textures of the model's other meshes (props, ground patches,
        the fortress sheet on shared meshes), taken from the game into work/ref/ for rendering.
        recoloured: EA's sheets as the faction's recoloured versions (`sagekit sheets`), which is how
        the game draws the untouched meshes once the faction is installed."""
        have, out = self.ws.texture_map(), {}
        ref = self.ws.path("work", "ref")
        sheets = os.path.join(paths.BUILD, self.b.style.faction, "_sheets", "out")
        os.makedirs(ref, exist_ok=True)
        bases, b = [], self.b                       # textures a base building shipped (its own sheet)
        while b.base:
            from .registry import load
            b = load(b.base)
            bases.append(Workspace(b))
        for mesh in W3DFile(model).meshes.values():
            for t in mesh.textures:
                shipped = [p for ws in bases for p in (ws.shipped_texture(t, ".dds"), ws.shipped_texture(t, ".tga"))
                           if os.path.exists(p)]
                if shipped and t.lower() not in have:
                    out[t.lower()] = shipped[0]
                    continue
                mine = [p for p in (os.path.join(sheets, *compiled_path(t, e).split("\\")) for e in (".dds", ".tga"))
                        if os.path.exists(p)]           # .tga: a TGA-only sheet, recoloured as one
                if recoloured and mine:
                    out[t.lower()] = mine[0]
                    continue
                if t.lower() in have or t.lower() in out:
                    continue
                exts = (".tga", ".dds") if "_nrm" in t.lower() else (".dds", ".tga")
                ext = next((e for e in exts if self.p.install.owner(compiled_path(t, e))), None)
                if ext is None:
                    continue                    # not in the game's archives: the render leaves it plain
                member = compiled_path(t, ext)
                dest = os.path.join(ref, t[:-4].lower() + ext)
                if not os.path.exists(dest):
                    with open(dest, "wb") as fh:
                        fh.write(self.p.install.read(member))
                out[t.lower()] = dest
        return out

    def labelled(self, r, views, res, tag=""):
        for v in views.split(","):
            labelled = []
            for who, text in (("orig", "original"), ("new", "%s (%s)" % (self.b.id, self.b.style.palette.name))):
                p = os.path.join(r, "_%s_%s%s.png" % (who, tag, v))
                text += " - " + tag[:-1] if tag else ""
                self.tool(["magick", os.path.join(r, "%s_%s%s.png" % (who, tag, v)), "-font", self.FONT, "-gravity", "NorthWest",
                           "-fill", "#f2ead8", "-undercolor", "#0008", "-pointsize", "34", "-annotate", "+18+14", " %s " % text, p])
                labelled.append(p)
            out = os.path.join(r, "compare_%s%s.png" % (tag, v))
            self.tool(["magick", labelled[0], "-size", "10x%s" % res.split("x")[1], "xc:#141414", labelled[1], "+append", out])
            print("  " + os.path.relpath(out, paths.REPO))


STEPS = [Extract, Geometry, Bake, Paint, Export, Night, Fixup, Derive, Lifecycle, Ship, Shared, Fire, Ini, Cache, Checks, Render]


GAME_RE = re.compile(r"lotrbfme2|game\.dat", re.I)
NOT_GAME = ("zsh", "bash", "sh", "python", "pgrep", "grep", "claude", "node")


def game_running():
    """Blender uses every core; a build during a match drops the game's frame rate. Matches the
    game's own processes, not shells or tools whose command line merely mentions it."""
    r = subprocess.run(["ps", "-axo", "comm=,args="], capture_output=True, text=True)
    for line in r.stdout.splitlines():
        comm = os.path.basename(line.split(" ", 1)[0]).lower()
        if GAME_RE.search(line) and not comm.startswith(NOT_GAME):
            return True
    return False


class Pipeline:
    def __init__(self, building, force=False):
        self.building = building
        self.ws = Workspace(building)
        self.install = Install()
        self.force = force

    def run(self, first=None, last=None):
        if game_running() and not self.force:
            print("the game is running - Blender steps wait until it closes (--force to run anyway)", flush=True)
        names = [s.name for s in STEPS]
        i0 = names.index(first) if first else 0
        i1 = names.index(last) if last else len(names) - 1
        for cls in STEPS[i0:i1 + 1]:
            t = time.time()
            print("[%s] %s" % (self.building.id, cls.name), flush=True)
            cls(self).run()
            print("  (%.0fs)" % (time.time() - t), flush=True)
