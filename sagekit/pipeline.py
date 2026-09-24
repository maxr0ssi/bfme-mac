"""Build one building from the installed game, step by step (host side; Blender runs the heavy
steps through sagekit/blender/run.py). Each step is a small class; `Pipeline.run(first, last)`
runs a slice, so iterating on a design is `--from geometry --to render`.

    extract    the originals from the game's archives (never from ours) + the atlas's 4x upscale
    geometry   design() merged into the target mesh, its own UV layout          (Blender)
    bake       G-buffers into that layout                                       (Blender)
    paint      the style's layer stack -> diffuse DDS + normal TGA              (Blender)
    export     the scene as W3D; the untouched original through the same export (Blender)
    fixup      restore what the exporter drops, point the target at its own textures
    ship       the files that ship, at their archive paths, under out/
    cache      a pristine asset.dat copy with the building's cache ops, verified
    checks     the standard check suite                                         (Blender)
    render     original vs new at the building's views, side by side            (Blender)
"""
import os
import shutil
import subprocess
import time

from . import paths
from .formats.assetcache import AssetCache
from .formats.textures import compiled_path
from .formats.w3d import fix
from .game import Install
from .workspace import Workspace

RUN_PY = os.path.join(paths.REPO, "sagekit", "blender", "run.py")
REALESRGAN = os.path.join(paths.REPO, "downloads", "realesrgan", "realesrgan-ncnn-vulkan")


class StepFailed(Exception):
    pass


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

    def run(self):
        g, a = self.p.install, self.b.style.atlas
        for member, dest in ((g.model_path(self.b.source), self.ws.source_model),
                             (compiled_path(a.texture, ".dds"), self.ws.atlas_dds),
                             (compiled_path(a.normal, ".tga"), self.ws.atlas_normal)):
            with open(dest, "wb") as fh:
                fh.write(g.read(member))
            print("  %-48s <- %s" % (os.path.relpath(dest, self.ws.root), os.path.basename(g.owner(member).path)))
        if not os.path.exists(self.ws.atlas_upscale):     # the upscale is slow-ish and deterministic: keep it
            png = self.ws.path("src", a.stem.lower() + ".png")
            self.tool(["magick", self.ws.atlas_dds, png])
            if not os.path.exists(REALESRGAN):
                raise StepFailed("Real-ESRGAN not found at %s (see assets/README.md)" % REALESRGAN)
            self.tool([REALESRGAN, "-i", png, "-o", self.ws.atlas_upscale, "-n", "realesrgan-x4plus",
                       "-m", os.path.join(os.path.dirname(REALESRGAN), "models")])
        print("  atlas upscale:", os.path.relpath(self.ws.atlas_upscale, self.ws.root))


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
        os.makedirs(os.path.dirname(self.ws.reference_export), exist_ok=True)
        self.blender("export", blend=self.ws.stage("geometry"))
        self.blender("reference")


class Fixup(Step):
    name = "fixup"

    def run(self):
        orig = open(self.ws.source_model, "rb").read()
        for src, dest, renames in ((self.ws.export_model, self.ws.shipped_model, self.b.renames()),
                                   (self.ws.reference_export, self.ws.reference_fixed, ())):
            fixed, report = fix(orig, open(src, "rb").read(), renames)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as fh:
                fh.write(fixed)
            if renames:
                print("\n".join("  " + x for x in report))


class Ship(Step):
    name = "ship"

    def run(self):
        a, own = self.b.style.atlas, self.b.texture_names()
        for name, ext in ((own[a.texture], ".dds"), (own[a.normal], ".tga")):
            src, dest = self.ws.tex(name[:-4].lower() + ext), self.ws.shipped_texture(name, ext)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src, dest)
        for root, _, files in os.walk(self.ws.path("out")):
            for f in sorted(files):
                p = os.path.join(root, f)
                print("  %-60s %10d" % (os.path.relpath(p, self.ws.path("out")), os.path.getsize(p)))


class Cache(Step):
    name = "cache"

    def run(self):
        live = self.p.install.asset_cache(self.b.model_file)
        pristine = live + ".orig" if os.path.exists(live + ".orig") else live
        cache = AssetCache(pristine)
        cache.path = self.ws.cache
        for line in apply_cache_ops(cache, self.b.cache_ops(), self.ws.shipped_model):
            print("  " + line)
        if cache.stale_entries(self.ws.shipped_model, self.b.model_file):
            raise StepFailed("cache record still stale after patching")
        cache.save(backup=False)
        print("  record matches the file")


def apply_cache_ops(cache, ops, model_path):
    lines = []
    for op in ops:
        if op[0] == "texture":
            lines += cache.add_texture(*op[1:])
        elif op[0] == "patch":
            lines += cache.patch_model(model_path, op[1])
    return lines


class Checks(Step):
    name = "checks"

    def run(self):
        out = self.blender("checks")
        print("\n".join("  " + x for x in out.splitlines() if x.startswith(("FAIL", "INFO")) or "checks passed" in x))


class Render(Step):
    name = "render"
    FONT = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

    def run(self, views="rts,close,ingame", res="1600x1100", spp="64"):
        r = self.ws.path("renders")
        for who, model in (("orig", self.ws.source_model), ("new", self.ws.shipped_model)):
            self.blender("render", log_as="render_" + who, w3d=model, prefix=os.path.join(r, who + "_"),
                         views=views, res=res, spp=spp)
        for v in views.split(","):
            labelled = []
            for who, text in (("orig", "original"), ("new", "%s (%s)" % (self.b.id, self.b.style.palette.name))):
                p = os.path.join(r, "_%s_%s.png" % (who, v))
                self.tool(["magick", os.path.join(r, "%s_%s.png" % (who, v)), "-font", self.FONT, "-gravity", "NorthWest",
                           "-fill", "#f2ead8", "-undercolor", "#0008", "-pointsize", "34", "-annotate", "+18+14", " %s " % text, p])
                labelled.append(p)
            out = os.path.join(r, "compare_%s.png" % v)
            self.tool(["magick", labelled[0], "-size", "10x%s" % res.split("x")[1], "xc:#141414", labelled[1], "+append", out])
            print("  " + os.path.relpath(out, paths.REPO))


STEPS = [Extract, Geometry, Bake, Paint, Export, Fixup, Ship, Cache, Checks, Render]


def game_running():
    """Blender uses every core; a build during a match drops the game's frame rate."""
    r = subprocess.run(["pgrep", "-if", r"lotrbfme2|game\.dat"], capture_output=True, text=True)
    return bool(r.stdout.strip())


class Pipeline:
    def __init__(self, building, force=False):
        self.building = building
        self.ws = Workspace(building)
        self.install = Install()
        self.force = force

    def run(self, first=None, last=None):
        if game_running() and not self.force:
            raise StepFailed("the game is running - a build would take its CPU. Close it, or pass --force")
        names = [s.name for s in STEPS]
        i0 = names.index(first) if first else 0
        i1 = names.index(last) if last else len(names) - 1
        for cls in STEPS[i0:i1 + 1]:
            t = time.time()
            print("[%s] %s" % (self.building.id, cls.name), flush=True)
            cls(self).run()
            print("  (%.0fs)" % (time.time() - t), flush=True)
