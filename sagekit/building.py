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
from .taxonomy import State, Tier, own_texture_name


class Building:
    style = None                    # a Style instance (shared by the faction)
    source = None                   # healthy model name, e.g. "DBFortress"
    target = None                   # mesh name inside it that is redesigned, e.g. "DBFORTRESS"
    tier = Tier.STANDARD
    code = None                     # short code for derived names (default: the building id)
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

    def texture_names(self):
        """{original texture: own texture} for the target mesh's diffuse and normal map."""
        atlas = self.style.atlas
        diffuse = self.own_textures.get(atlas.texture) or \
            own_texture_name(atlas.texture, self.code or self.name) + ".tga"
        normal = diffuse[:-4] + "_NRM.tga"
        return {atlas.texture: diffuse, atlas.normal: normal}

    def renames(self):
        """w3d fix-up renames: (mesh, old, new)."""
        return [(self.target, old, new) for old, new in self.texture_names().items()]

    def cache_ops(self):
        """Asset-cache edits the shipped files need: [('texture', new, like, model, object) |
        ('patch', model file)] - applied to a copy at build time and to the game at install."""
        own = self.texture_names()
        atlas = self.style.atlas
        container = self.source.upper()
        return [
            ("texture", own[atlas.texture].lower(), atlas.texture.lower(), self.model_file,
             "%s.%s" % (container, self.target)),
            ("texture", own[atlas.normal].lower(), atlas.normal.lower(), None, None),
            ("patch", self.model_file),
        ]

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
