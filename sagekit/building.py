"""One building: what it replaces, its limits, and its design. Subclass in
assets/<faction>/<building>/building.py; everything not declared is inherited or derived.

    class Fortress(Building):
        style = DwarvenStyle()
        source = "DBFortress"            # the model the game draws when healthy
        target = "DBFORTRESS"            # its mesh that gets the new shape and its own texture
        tier = Tier.HERO
        def design(self, kit): ...       # -> [Solid], with the faction's shape kit

The pipeline reads the rest from the game: the source model's meshes and bones, its lifecycle
(INI draw states), the textures its target mesh uses, the asset cache that files it.
"""
from .taxonomy import State, Tier, own_texture_name, own_variant_name



def same_body(a, b, tol=0.5):
    """Whether a state's body is the healthy body, give or take dents: the same triangle count and
    the same bounding box (EA's lightly damaged bodies move a few vertices by up to ~2 units; its
    broken, collapsed and re-framed bodies lose or gain triangles or change their extent)."""
    def box(m):
        return [f(p[i] for p in m.verts) for f in (min, max) for i in range(3)]
    return len(a.tris) == len(b.tris) and all(abs(x - y) <= tol for x, y in zip(box(a), box(b)))

class Building:
    style = None                    # a Style instance (shared by the faction)
    source = None                   # healthy model name, e.g. "DBFortress"
    target = None                   # mesh name inside it that is redesigned, e.g. "DBFORTRESS"
    tier = Tier.STANDARD
    sheet = None                    # the sheet the target mesh is painted from (default: the faction atlas)
    sheet_normal = "auto"           # its normal map: "auto" = <sheet>_NRM.tga, None = the sheet has none
    own_textures = {}               # pin names: {"DBFortress1.tga": "DBFortressH.tga"}
    max_z_growth = 0.20             # height may grow this much; the footprint may not
    tri_budget = 15000              # triangles in the target mesh
    built_states = (State.HEALTHY,)  # states this building's recipe produces so far
    bake_hidden = ()                # meshes left out of the bakes (banners, placement planes)
    views = {}                      # name -> (target, distance, elevation, azimuth, lens)

    # identity, set by sagekit.registry when the class is loaded
    id = None                       # "dwarves/fortress"

    @property
    def faction(self):
        return self.id.split("/")[0]

    @property
    def name(self):
        return self.id.split("/")[1]

    # ------------------------------------------------------------------ derived names
    @property
    def model_file(self):
        return self.source.lower() + ".w3d"

    @property
    def sheet_atlas(self):
        """The Atlas of the sheet this building replaces: the faction atlas, or a plain one for the
        building's own sheet (new geometry is always mapped onto the faction atlas)."""
        master = self.style.atlas
        if not self.sheet or self.sheet.lower() == master.texture.lower():
            return master
        from .atlas import Atlas
        a = Atlas()
        a.texture = self.sheet
        a.normal = self.sheet[:-4] + "_NRM.tga" if self.sheet_normal == "auto" else self.sheet_normal
        return a

    @property
    def two_sheets(self):
        return self.sheet_atlas is not self.style.atlas

    def texture_names(self):
        """{original texture: own texture} for the target mesh's diffuse (and normal map, if any)."""
        a = self.sheet_atlas
        diffuse = self.own_textures.get(a.texture) or own_texture_name(a.texture) + ".tga"
        out = {a.texture: diffuse}
        if a.normal:
            out[a.normal] = diffuse[:-4] + "_NRM.tga"
        return out

    @property
    def own_diffuse(self):
        return self.texture_names()[self.sheet_atlas.texture]

    @property
    def own_normal(self):
        return self.texture_names().get(self.sheet_atlas.normal) if self.sheet_atlas.normal else None

    def derived_models(self, install):
        """Models of the body family (besides the source) whose target mesh is EA's healthy body
        itself (same triangles, same frame): the construction and lightly damaged states, which
        take our body as it is. EA's broken, collapsed or re-framed bodies (really damaged,
        rubble, the forge's construction) are left to EA, recoloured by the faction sheets."""
        from .formats.w3d import W3DFile
        healthy = W3DFile(install.read(install.model_path(self.source))).meshes[self.target]
        out = []
        for draws in self.objects(install).values():
            for d in draws:
                if not self.covers(d):
                    continue
                for m in d.models():
                    if m.lower() == self.source.lower() or m in out or not install.has_model(m):
                        continue
                    mesh = W3DFile(install.read(install.model_path(m))).meshes.get(self.target)
                    if mesh is not None and not mesh.skinned and same_body(mesh, healthy):
                        out.append(m)
        return out

    def variants(self, install):
        """{EA variant texture: our variant} for every state that swaps the body's sheet for
        another (damaged, snow, stonework): e.g. {"DBFortress1_D.tga": "DBFortressH_D.tga"}."""
        atlas, own = self.sheet_atlas, self.own_diffuse
        out = {}
        for draws in self.objects(install).values():
            for d in draws:
                if not self.covers(d):
                    continue
                for st in d.states:
                    for old, new in st.textures:
                        if old.lower() == atlas.texture.lower():
                            out[new] = own_variant_name(atlas.texture, own, new)
        from .formats.w3d import W3DFile
        for m in self.derived_models(install):       # damaged models painted from their own sheet
            for t in W3DFile(install.read(install.model_path(m))).meshes[self.target].textures:
                low = t.lower()
                if "_nrm" not in low and low != atlas.texture.lower() and low not in {k.lower() for k in out}:
                    out[t] = own_variant_name(atlas.texture, own, t)
        return out

    def renames(self):
        """w3d fix-up renames: (mesh, old, new)."""
        return [(self.target, old, new) for old, new in self.texture_names().items()]

    def cache_ops(self, variants=None, derived=()):
        """Asset-cache edits the shipped files need: [('texture', new, like, model, object) |
        ('patch', model file)] - applied to a copy at build time and to the game at install."""
        own = self.texture_names()
        atlas = self.sheet_atlas
        container = self.source.upper()
        ops = [("texture", own[atlas.texture].lower(), atlas.texture.lower(), self.model_file,
                "%s.%s" % (container, self.target))]
        if atlas.normal:
            ops.append(("texture", own[atlas.normal].lower(), atlas.normal.lower(), None, None))
        ops += [("texture", mine.lower(), ea.lower(), None, None) for ea, mine in sorted((variants or {}).items())]
        return ops + [("patch", self.model_file)] + [("patch", m.lower() + ".w3d") for m in derived]

    def ini_ops(self, install, variants):
        """{INI archive path: [op]} (sagekit/formats/ini.py apply_ops): our own texture swaps next to
        EA's, and StaticModelLODMode off on the Draw modules this building covers."""
        atlas = self.sheet_atlas
        own = self.own_diffuse
        swaps = {ea: (own, mine) for ea, mine in variants.items()}
        out = {}
        for obj, draws in self.objects(install).items():
            for d in draws:
                ops = out.setdefault(d.file, [("swaps", atlas.texture, swaps)])
                if self.covers(d) and d.fields.get("StaticModelLODMode", "").lower() == "yes":
                    ops.append(("lod_off", obj, d.tag))
        return out

    # ------------------------------------------------------------------ lifecycle (from the game)
    parts = ()                      # the Draw modules (tags) this building redesigns; () = the body's

    def objects(self, install):
        """{object name: [Draw]} for every object that draws this building's model family (the
        source model and its <source>_* variants) - the building and its construction site."""
        fam = self.source.lower()
        draws = install.draws(self.style.ini_dir)
        names = {d.object for d in draws
                 if any(m.lower() == fam or m.lower().startswith(fam + "_") for m in d.models())}
        return {n: [d for d in draws if d.object == n] for n in sorted(names)}

    def is_body(self, draw):
        fam = self.source.lower()
        return any(m.lower() == fam or m.lower().startswith(fam + "_") for m in draw.models())

    def covers(self, draw):
        """Does this building's recipe redesign that Draw module?"""
        return draw.tag in self.parts if self.parts else self.is_body(draw)

    # ------------------------------------------------------------------ design hooks (Blender side)
    def design(self, kit):
        """-> [Solid]: every new solid, in the target mesh's local coordinates."""
        raise NotImplementedError

    def emphasis(self, center, normal):
        """Texel-density weight of a face (1 = average); the RTS camera's favourites get more."""
        return 1.0

    def decals(self):
        """Building-specific paint layers added on top of the style's (e.g. sigils at set spots)."""
        return []
