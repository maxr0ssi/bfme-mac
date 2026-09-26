"""The on-disk layout of one building's build. Host and Blender both ask this module.

    build/assets/<faction>/<building>/
      src/     the game's originals: <model>.w3d, the atlas (.dds + its 4x upscale .png), its normal map
      work/    stage_*.blend, bake/*.npy, tex/, export/, ref/, logs/
      cache/   <game>/asset.dat: pristine copies of the caches its ops touch, ops applied (and verified)
      out/     exactly what ships, as archive paths: art/w3d/..., art/compiledtextures/...
      renders/ comparison images
"""
import json
import os

from . import paths
from .formats.textures import compiled_path
from .formats.w3d import W3DFile


class Workspace:
    def __init__(self, building):
        self.b = building
        self.root = paths.work_dir(building.id)
        for d in ("src", "work", "cache", "out", "renders", self.bake_dir, self.tex_dir, self.logs):
            os.makedirs(os.path.join(self.root, d), exist_ok=True)

    def path(self, *p):
        return os.path.join(self.root, *p)

    # ------------------------------------------------------------------ sources
    @property
    def src(self):
        """The game's originals (a skinned model's separate skeleton is here too)."""
        return self.path("src")

    @property
    def source_model(self):
        return self.path("src", self.b.model_file)

    def upscale_of(self, texture):
        """The 4x upscale of any sheet (by texture name) in src/."""
        return self.path("src", "%s_x%d.png" % (texture[:-4].lower(), self.b.style.atlas.upscale))

    @property
    def atlas_dds(self):
        """The sheet the target mesh was painted from (EA's DDS)."""
        return self.path("src", self.b.sheet_atlas.texture[:-4].lower() + ".dds")

    @property
    def atlas_upscale(self):
        return self.upscale_of(self.b.sheet_atlas.texture)

    @property
    def atlas_normal(self):
        n = self.b.sheet_atlas.normal
        return self.path("src", n.lower()) if n else None

    @property
    def master_upscale(self):
        """The faction atlas's upscale: where new geometry is mapped (the same sheet for buildings
        painted from the faction atlas)."""
        return self.upscale_of(self.b.style.atlas.texture)

    @property
    def master_normal(self):
        return self.path("src", self.b.style.atlas.normal.lower())

    @property
    def variants(self):
        """{EA variant texture: our variant} as the extract step recorded it."""
        p = self.path("work", "variants.json")
        return json.load(open(p)) if os.path.exists(p) else {}

    @property
    def derived(self):
        """Models rebuilt from our body (EA's damaged-but-standing ones), as extract recorded them."""
        p = self.path("work", "derived.json")
        return json.load(open(p)) if os.path.exists(p) else []

    @property
    def house(self):
        """The house-colour model this building's cloth goes to (Building.house_model), as extract
        recorded it, or None."""
        p = self.path("work", "house.json")
        return json.load(open(p)) if os.path.exists(p) else None

    @property
    def house_cloth(self):
        """The cloth faces the geometry step took out of the body: [[[x, y, z], ...]] in world space."""
        return self.path("work", "house_cloth.json")

    def variant_upscale(self, ea_texture):
        return self.upscale_of(ea_texture)

    @property
    def container(self):
        """The model's container name (the exporter names it after the FILE, so exports use it)."""
        return next(iter(W3DFile(self.source_model).meshes.values())).container

    # ------------------------------------------------------------------ work
    @property
    def bake_dir(self):
        return self.path("work", "bake")

    @property
    def tex_dir(self):
        return self.path("work", "tex")

    @property
    def logs(self):
        return self.path("work", "logs")

    def stage(self, name):
        return self.path("work", "stage_%s.blend" % name)

    def tex(self, name):
        return os.path.join(self.tex_dir, name)

    @property
    def export_model(self):
        return self.path("work", "export", self.container + ".w3d")

    def cache_copy(self, live):
        """The build's copy of one of the game's asset.dat files: cache/<game folder>/asset.dat."""
        return self.path("cache", os.path.basename(os.path.dirname(live)), "asset.dat")

    def caches(self, game="rotwk"):
        """The build's asset.dat copies (one per cache its ops touch) in the game's search order:
        a model filed in both (RotWK re-files some BFME2 models) is read from the first."""
        live = [os.path.join(paths.GAMEDIRS[g], "asset.dat") for g in paths.SEARCH_ORDER[game]]
        return [c for c in map(self.cache_copy, live) if os.path.exists(c)]

    # ------------------------------------------------------------------ what ships
    def out(self, archive_path):
        return self.path("out", *archive_path.split("\\"))

    @property
    def shipped_model(self):
        return self.out("art\\w3d\\%s\\%s" % (self.b.model_file[:2], self.b.model_file))

    def shipped_texture(self, name, ext):
        return self.out(compiled_path(name, ext))

    def texture_map(self):
        """{lower-case texture name a model references: file} for rendering the shipped model."""
        a = self.b.sheet_atlas
        out = {self.b.own_diffuse.lower(): self.shipped_texture(self.b.own_diffuse, ".dds"),
               a.texture.lower(): self.atlas_dds}
        if a.normal:
            out[self.b.own_normal.lower()] = self.shipped_texture(self.b.own_normal, ".tga")
            out[a.normal.lower()] = self.atlas_normal
        return out
