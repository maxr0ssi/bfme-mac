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



def same_body(a, b, tol=0.5, frames=None, tris=True):
    """Whether a state's body is the healthy body, give or take dents: the same triangle count and
    the same bounding box (EA's lightly damaged bodies move a few vertices by up to ~2 units; its
    broken, collapsed and re-framed bodies lose or gain triangles or change their extent).
    frames: the two meshes' model-space frames (sagekit/formats/w3dframes.py), when the bodies
    hang on differently turned bones; tris=False compares place and extent alone."""
    from .formats.w3dframes import IDENTITY, model_box
    fa, fb = frames or (IDENTITY, IDENTITY)
    return (not tris or len(a.tris) == len(b.tris)) and \
        all(abs(x - y) <= tol for x, y in zip(model_box(a, fa), model_box(b, fb)))


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
    own_model = None                # ship the redesign as a new model of this name, leaving EA's
                                    # `source` to the other factions that draw it (sagekit/owncopy.py)
    replaces = ()                   # with own_model: EA's stand-in meshes the target takes over (dropped)

    def shipped_name(self, model):
        """The name EA model `model` (the source or one of its derived models) ships under."""
        from .owncopy import shipped_name
        return shipped_name(self, model)

    @property
    def model_file(self):
        return self.shipped_name(self.source).lower() + ".w3d"

    @property
    def sheet_atlas(self):
        """The Atlas of the sheet this building replaces: the faction atlas, or a plain one for the
        building's own sheet (new geometry is always mapped onto the faction atlas)."""
        master = self.style.atlas
        if not self.sheet or self.sheet.lower() == master.texture.lower():
            return master
        from .atlas import Atlas
        a = Atlas()
        a.ground_sat = master.ground_sat            # the faction's colour rules read its own sheets too
        a.texture = self.sheet
        a.normal = self.sheet[:-4] + "_NRM.tga" if self.sheet_normal == "auto" else self.sheet_normal
        return a

    @property
    def two_sheets(self):
        return self.sheet_atlas is not self.style.atlas

    def texture_names(self):
        """{original texture: own texture} for the target mesh's diffuse (and normal map, if any)."""
        a = self.sheet_atlas
        own = next((v for k, v in self.own_textures.items() if k.lower() == a.texture.lower()), None)
        diffuse = own or own_texture_name(a.texture) + ".tga"          # (a key in any case: gbfortress1.tga)
        out = {a.texture: diffuse}
        if a.normal:                    # (an own_textures pin for a normal map EA named off the
            pin = next((v for k, v in self.own_textures.items() if k.lower() == a.normal.lower()), None)
            out[a.normal] = pin or diffuse[:-4] + "_NRM.tga"           # pattern: Angmar's KBHall_Normal)
        return out

    @property
    def own_diffuse(self):
        return self.texture_names()[self.sheet_atlas.texture]

    @property
    def own_normal(self):
        return self.texture_names().get(self.sheet_atlas.normal) if self.sheet_atlas.normal else None

    base = None                     # id of a Building whose finished model this one redesigns further
                                    # (a second mesh of the same model); built after it, shipped instead
    always_shown = False            # with base: the mesh is drawn at every upgrade level (the green pasture's
                                    # fence), so it may carry cloth and night lights; False keeps a chained
                                    # mesh shown per upgrade level (the Dwarven archery tower's, walls',
                                    # obelisks') from both: they would hang in the air before the upgrade

    @property
    def per_level(self):
        """A chained mesh the game shows per upgrade level (no cloth, no night lights of its own)."""
        return bool(self.base) and not self.always_shown

    also_derived = ()               # models whose target mesh is not EA's healthy body but takes ours
                                    # anyway (EA's placement cursor, a simplified copy; a light-damage body
                                    # with a few faces chipped off): matched on place and extent alone

    def derived_models(self, install):
        """Models besides the source that ship with our body: the construction and lightly damaged
        states whose body is EA's healthy one (derived_bodies). A recipe chained on a `base` rides
        along in its base's models - it splices its mesh into the base's derived files, so the
        chain's last building ships them carrying every link's redesign."""
        if self.base:
            return self.base_building().derived_models(install)
        return list(self.derived_bodies(install))

    def derived_bodies(self, install):
        """{model: its mesh that takes our target's body}: by our target's name, else the one mesh
        there that is our body under another name (EA renames: DBArchRnge_D1.ARCHERY,
        DBFStatus_D1.DBFSTATUS_D1). EA's broken, collapsed or re-framed bodies (really damaged,
        rubble, the forge's construction) are left to EA, recoloured by the faction sheets."""
        out = {}
        for m in self.derived_models(install) if self.base else self.drawn_models(install):
            fits = self.bodies_in(install, m)
            if self.target in fits or len(fits) == 1:
                out[m] = self.target if self.target in fits else next(iter(fits))
            elif m.lower() in {x.lower() for x in self.also_derived}:
                raise ValueError("%s: no one mesh of %s is where %s is (%s)" % (self.id, m, self.target, list(fits)))
        return out

    def bodies_in(self, install, model):
        """{mesh: frame taking our body's mesh-local coordinates into the mesh's} for the meshes of
        `model` that are EA's healthy target (same_body): as they stand (identity; EA's construction
        models animate their bones from a bind pose of their own), else in model space (their bone
        turned: DBArchRnge_D1's body hangs on a bone turned 180 degrees about z)."""
        from .formats.w3d import W3DFile
        from .formats.w3dframes import IDENTITY, compose, inverse, mesh_frames
        read_skl = lambda skl: install.read(install.model_path(skl[:-4]))        # noqa: E731
        data = install.read(install.model_path(self.source))
        healthy, hf = W3DFile(data).meshes[self.target], mesh_frames(data, read_skl)[self.target]
        data = install.read(install.model_path(model))
        frames = mesh_frames(data, read_skl)
        tol, tris = (2.5, False) if model.lower() in {x.lower() for x in self.also_derived} else (0.5, True)
        out = {}
        for n, mesh in W3DFile(data).meshes.items():
            if mesh.skinned:
                continue
            if same_body(mesh, healthy, tol, tris=tris):
                out[n] = IDENTITY
            elif same_body(mesh, healthy, tol, (frames[n], hf), tris):
                out[n] = compose(inverse(frames[n]), hf)
        return out

    def drawn_models(self, install):
        """The models (besides the source) that the Draw modules this building covers show."""
        out = []
        for draws in self.objects(install).values():
            for d in draws:
                if self.covers(d):
                    out += [m for m in self.own_models(d) if m.lower() != self.source.lower()
                            and m.lower() not in map(str.lower, out) and install.has_model(m)]
        return out

    variation = None                # the BUILD_VARIATION_* flag this recipe's body is drawn under (the
                                    # fortress expansions draw two bodies in one Draw module: GBFDOTOWA
                                    # under _ONE, GBFDOTOWB under _TWO, one recipe each); None: the flags
                                    # of the states showing `source` (sagekit/formats/ini.py variation_states)

    def own_states(self, draw):
        """The states of a Draw module that are this recipe's: all of them, but in a Draw showing two
        build variations only its own variation's (so B's models never get A's design)."""
        from .formats.ini import variation_states
        return variation_states(draw, self.source, self.variation)

    def own_models(self, draw):
        """draw.models() in this recipe's own states."""
        return sorted({s.model for s in self.own_states(draw) if s.model and s.model.lower() != "none"}, key=str.lower)

    def house_conditions(self, install):
        """For a Draw showing two build variations: when a house-colour model of our own shows,
        {"default": shown in the default state, "states": [[[flag], shown]] per variation flag}
        (only in this recipe's variation); None for a building without variations."""
        from .formats.ini import VARIATION
        for draws in self.objects(install).values():
            for d in draws:
                flags = sorted({f for s in d.states for f in s.flags if f.startswith(VARIATION)})
                if not flags or not self.covers(d) or not self.is_body(d):
                    continue
                own = self.own_states(d)
                mine = {f for s in own for f in s.flags if f.startswith(VARIATION)}
                default = any(s.kind == "model" and not s.flags for s in own)
                return {"default": default, "states": [[[f], f in mine] for f in flags]}
        return None

    def base_building(self):
        from .registry import load
        return load(self.base) if self.base else None

    def variants(self, install):
        """{EA variant texture: our variant} for every state that swaps the body's sheet for
        another (damaged, snow, stonework): e.g. {"DBFortress1_D.tga": "DBFortressH_D.tga"}."""
        from .formats.textures import sheet_member
        atlas, own = self.sheet_atlas, self.own_diffuse
        out = {}
        for draws in self.objects(install).values():
            for d in draws:
                if not self.covers(d):
                    continue
                for st in self.own_states(d):
                    for old, new in st.textures:
                        if old.lower() != atlas.texture.lower() or new.lower() in {k.lower() for k in out}:
                            continue                        # one variant per sheet, whatever EA's case
                        if not sheet_member(install, new):
                            continue                        # EA's typos (DBFortress_Snow): the swap shows nothing
                        out[new] = own_variant_name(atlas.texture, own, new)
        from .formats.w3d import W3DFile
        for m, mesh in self.derived_bodies(install).items():     # damaged models painted from their own sheet
            for t in W3DFile(install.read(install.model_path(m))).meshes[mesh].textures:
                low = t.lower()
                if "_nrm" not in low and low not in (atlas.texture.lower(), (atlas.normal or "").lower()) \
                        and low not in {k.lower() for k in out}:   # (a normal map named off the pattern: KBHall_Normal)
                    out[t] = own_variant_name(atlas.texture, own, t, same_length=True)
                    if sheet_member(install, out[t]):
                        raise ValueError("%s: %s is one of EA's names; pin one in own_textures" % (t, out[t]))
        return out

    def normal_variants(self, install):
        """{EA state normal map: ours}: a derived body whose state is painted with a normal map of
        its own (NBElvnBarx_D1 draws NBElvnBarx_D_NRM) must read ours, laid out for our UVs, not
        EA's. Ours ships again under a name as long as EA's (W3D patches names in place), e.g.
        nbelvnbarH_D_NRM.tga, a copy of nbelvnbarH_NRM.tga."""
        atlas = self.sheet_atlas
        if not self.own_normal:
            return {}
        from .formats.w3d import W3DFile
        out = {}
        for m, mesh in self.derived_bodies(install).items():
            for t in W3DFile(install.read(install.model_path(m))).meshes[mesh].textures:
                low = t.lower()
                if "_nrm" in low and low != atlas.normal.lower() and low not in {k.lower() for k in out}:
                    out[t] = own_variant_name(atlas.texture, self.own_diffuse, t, same_length=True)
        return out

    def renames(self):
        """w3d fix-up renames: (mesh, old, new)."""
        return [(self.target, old, new) for old, new in self.texture_names().items()]

    def cache_ops(self, variants=None, derived=()):
        """Asset-cache edits the shipped files need: [('model', our model file, EA's it copies) |
        ('texture', new, like, model, object) | ('patch', model file)] - applied to a copy at build
        time and to the game at install."""
        own = self.texture_names()
        atlas = self.sheet_atlas
        container = self.shipped_name(self.source).upper()
        ops = [("texture", own[atlas.texture].lower(), atlas.texture.lower(), self.model_file,
                "%s.%s" % (container, self.target))]
        if atlas.normal:
            ops.append(("texture", own[atlas.normal].lower(), atlas.normal.lower(), None, None))
        ops += [("texture", mine.lower(), ea.lower(), None, None) for ea, mine in sorted((variants or {}).items())]
        from .workspace import Workspace                        # our normal map under state names
        ops += [("texture", mine.lower(), ea.lower(), None, None) for ea, mine in sorted(Workspace(self).normal_variants.items())]
        from .sharedsheets import cache_ops as shared            # the faction's copies of shared EA sheets
        ops += shared(self)
        from .nightlights import cache_ops as night              # the faction's night-light texture
        ops += night(self)
        # models of our own name (own_model: the copy and its derived/lifecycle models) are filed
        # first, as copies of EA's records - the engine draws no model the cache does not file
        own = [("model", self.shipped_name(m).lower() + ".w3d", m.lower() + ".w3d") for m in [self.source] + list(derived)
               if self.shipped_name(m).lower() != m.lower()]
        from .fire import cache_ops as fire                      # the fire rig (a model of our own)
        return own + fire(self) + ops + [("patch", self.model_file)] + [("patch", self.shipped_name(m).lower() + ".w3d") for m in derived]

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
                    ops.append(("lod_off", d.object, d.tag))     # (an inherited module: its parent's)
        if self.own_model:                                  # an own copy: our model in place of EA's
            from .owncopy import ini_ops
            from .workspace import Workspace                 # and the lifecycle step's models
            models = [self.source] + self.derived_models(install) + Workspace(self).lifecycle
            for member, ops in ini_ops(self, install, models).items():
                out.setdefault(member, []).extend(ops)
        from .sharedsheets import ini_ops as shared         # state swaps of the shared sheets' copies
        for member, ops in shared(self).items():
            out.setdefault(member, []).extend(ops)
        from .fire import ini_ops as fire                   # our fire's Draw modules, EA's untouched
        for member, ops in fire(self, install).items():
            out.setdefault(member, []).extend(ops)
        return out

    # ------------------------------------------------------------------ lifecycle (from the game)
    parts = ()                      # the Draw modules (tags) this building redesigns; () = the body's

    def objects(self, install):
        """{object name: [Draw]} for every object that draws this building's model family (the
        source model and its <source>_* variants) - the building and its construction site - in the
        style's INI folders (Style.ini_dirs: Arnor's too for the Men). A ChildObject's list holds the
        Draw modules it inherits (GondorFarm: FarmInterface's), whose d.object is the parent's."""
        fam = self.source.lower()
        by = install.object_draws(self.style.ini_dirs())
        return {n: by[n] for n in sorted(by)
                if any(m.lower() == fam or m.lower().startswith(fam + "_") for d in by[n] for m in d.models())}

    footprint_margin = 0.0          # how far new geometry may pass the original's footprint (units): for
                                    # pieces whose faces lie on its edge (collision comes from the INI)
    world_space = False             # True: design(), bakes, texel weights and checks work in world axes
                                    # (for a target hung on a rotated bone, e.g. a wall end lying on its side)
    facet_islands = False           # True: every original face of the target is a UV island of its own (as new
                                    # faces are): organic bodies - a trunk, a horn of rock - whose smooth shells
                                    # unwrap onto themselves; a number (degrees): seams at EA's own island
                                    # borders and where faces turn more than that (sagekit/blender/layout.py)
    house_tags = ("cloth",)         # faces of these atlas regions leave the body for the house-colour
                                    # model shown with it, which the game tints in the player's colour

    def house_model(self, install):
        """The house-colour model drawn with this building's object(s) - a model with an `HC_` mesh
        in a Draw module that allows model colour: {"model", "mesh", "draws": [[ini file, object,
        draw tag]]}, or None (the cloth then stays in the body, in the palette's colour). An add-on
        gets a model of its own, shown under its upgrade flags only (addon_conditions): the object's
        model is drawn before the upgrade is bought, and the add-on's banners would hang in the air."""
        from .formats.w3d import W3DFile
        addon = self.addon_conditions(install)
        if addon:
            return self.new_house_model(install, addon)
        found = None
        for obj, draws in self.objects(install).items():
            for d in draws:
                if self.covers(d) or d.fields.get("OkToChangeModelColor", "").lower() != "yes":
                    continue
                for m in d.models():
                    if found and m.lower() != found["model"].lower() or not install.has_model(m):
                        continue
                    if found is None:
                        from .housemesh import house_meshes     # HC_ meshes, or by their house-colour texture
                        hc = house_meshes(W3DFile(install.read(install.model_path(m))))
                        if not hc:
                            continue
                        found = {"model": m, "mesh": hc[0], "draws": []}
                    found["draws"].append([d.file, d.object, d.tag])
        if found and self.house_shared(install, found["model"]):
            return self.own_house_copy(install, found)
        return found or self.new_house_model(install)

    def house_shared(self, install, model):
        """Whether another faction's objects draw EA's house-colour model `model` too (Arnor's Elven
        barracks and mallorn draw NBHCElvnBarx and EBHCMalTree; sagekit/ownership.py)."""
        from .ownership import load
        return bool(load(install).other_model(model, self.faction))

    def own_house_copy(self, install, found):
        """A shared house-colour model as a model of our own (the own_model pattern,
        sagekit/owncopy.py): EA's file renamed, its flag replaced by our cloth, shown in place of
        EA's by this faction's Draw modules only (found["draws"]: the objects of the style's INI
        folder), so the other factions keep EA's flag. Named with the faction's house prefix
        (the style's house_template: EBHC) and EA's stem, EBHCElvnBarx for NBHCElvnBarx; with our
        shipped model's stem when EA's already carries the prefix (EBHCMalTree2 for EBMalTree2)."""
        template = getattr(self.style, "house_template", None) or found["model"]
        name = template[:2].upper() + "HC" + found["model"][4:]
        if name.lower() == found["model"].lower():
            stem = self.shipped_name(self.source)
            stem = stem[:-4] if stem.lower().endswith("_skn") else stem
            name = template[:2].upper() + "HC" + stem[2:]
        if name[:15].lower() == found["model"].lower():     # Mordor's prefix is EA's (MBHCOrcpit): MBHCOrcpit2
            name = name[:14] + "2"
        name = name[:15]
        if install.has_model(name) or any(c.has_model(name.lower() + ".w3d") for c in install.asset_caches().values()):
            raise ValueError("%s: own copy %s of house-colour model %s is a name EA's files use" % (self.id, name, found["model"]))
        return dict(found, model=name, copy_of=found["model"])

    HOUSE_DRAW = None               # the Draw tag of a house-colour model of our own (None: one per
                                    # model, so an object showing two of them keeps both)

    def addon_conditions(self, install):
        """For an add-on - `parts` shown only once an upgrade is bought (the Elven citadel's
        ModuleTag_DrawEnchantedAnvil: nothing by default, EBFAnvil under FORTRESS_IMPROVEMENT_3) -
        where its house-colour model shows: {object: {"default": False, "states": [[flags, shown]]}},
        house_conditions' form: the add-on Draw's condition states in its order, shown where they draw
        a model, so the engine picks the banner's state whenever it picks the add-on's. None when a
        Draw it covers shows a model without an upgrade flag (a body, a part always shown)."""
        if not self.parts:
            return None
        from .taxonomy import upgrades_of
        out = {}
        for draws in self.objects(install).values():
            for d in draws:
                for s in self.own_states(d) if self.covers(d) else ():
                    if s.kind != "model":
                        continue
                    shown = bool(s.model) and s.model.lower() != "none"
                    if shown and not upgrades_of(s.flags):
                        return None
                    states = out.setdefault(d.object, {"default": False, "states": []})["states"]
                    if s.flags and [sorted(s.flags), shown] not in states:
                        states.append([sorted(s.flags), shown])
        return out if any(shown for c in out.values() for _, shown in c["states"]) else None

    def new_house_model(self, install, conditions=None):
        """For an object without a house-colour model: one of our own, copied from the style's
        `house_template` (EA's model's names changed; its flag replaced by our cloth) and shown by a
        Draw module added to every object drawing the body. None if the style has no template.
        conditions: an add-on's (addon_conditions), recorded as "conditions" for sagekit/house.py."""
        template = getattr(self.style, "house_template", None)
        if not template:
            return None
        # the faction's prefix, from its template: DBHC (DBHCArchRnge), EBHC (EBHCBbattleTwr)
        name = (template[:2].upper() + "HC" + self.shipped_name(self.source)[2:])[:15]
        if install.has_model(name) or any(c.has_model(name.lower() + ".w3d") for c in install.asset_caches().values()):
            raise ValueError("%s: own house-colour model %s is a name EA's files use" % (self.id, name))
        draws = sorted({(d.file, d.object) for ds in self.objects(install).values() for d in ds if self.is_body(d)})
        tag = self.HOUSE_DRAW or "ModuleTag_Draw_" + name
        from .formats.w3d import W3DFile
        from .housemesh import house_meshes         # the template's own cloth mesh (GBHCBtlTwrM: HC_BANNER01)
        hc = house_meshes(W3DFile(install.read(install.model_path(template))))
        out = {"model": name, "mesh": hc[0] if hc else "HC_BANNER", "template": template,
               "draws": [[f, obj, tag] for f, obj in draws]}
        if conditions:                              # an add-on: shown with it only
            out["conditions"] = conditions
            return out
        cond = self.house_conditions(install)       # two build variations: shown in this one's states only
        if cond:
            out["variation"] = cond
        return out

    def is_body(self, draw):
        fam = self.source.lower()
        return any(m.lower() == fam or m.lower().startswith(fam + "_") for m in draw.models())

    def covers(self, draw):
        """Does this building's recipe redesign that Draw module?"""
        return draw.tag in self.parts if self.parts else self.is_body(draw)

    # ------------------------------------------------------------------ design hooks (Blender side)
    clear = ()                      # EA's faces of the target removed before design() (a rebuilt body):
                                    # [sagekit.clear spec]: Box, Piece, Where or a predicate on the face
                                    # centre (target coordinates); ALL clears the whole mesh

    def design(self, kit):
        """-> [Solid]: every new solid, in the target mesh's local coordinates."""
        raise NotImplementedError

    def emphasis(self, center, normal):
        """Texel-density weight of a face (1 = average); the RTS camera's favourites get more."""
        return 1.0

    def decals(self):
        """Building-specific paint layers added on top of the style's (e.g. sigils at set spots)."""
        return []

    night_surfaces = ()             # meshes besides the target the night lights may lie on (EA's rock)
    fire_points = ()                # [(x, y, z, kind)] in the healthy model's space: the game's own fire,
                                    # smoke and embers there (sagekit/fire.py; kinds: fire.KINDS)

    def night_lights(self, kit):
        """-> [sagekit.nightlights.Light]: the design's real windows and doors, lit at night in
        the style's NightLook (design coordinates, like design()). None declared: the building's
        night meshes show nothing (unless a base link lights them)."""
        return []
