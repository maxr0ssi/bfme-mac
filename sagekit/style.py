"""A faction's look: one palette, one set of materials, one shape vocabulary, one paint stack.

Every building of a faction imports the same Style, so a gold is the same gold everywhere. The
class is declarative and importable anywhere; its Blender-side parts (shapes, paint layers) are
built on demand inside Blender through `shapes()` and `layers()`.
"""
import os


class Palette:
    """Luminance ramps per material and a few accent colours, all in sRGB 0..1.
    ramps: {material: [(luminance, (r, g, b)), ...]}; accents: {name: (r, g, b)};
    tints: {name: (r, g, b) multipliers}."""

    def __init__(self, name, ramps, accents, tints=None):
        self.name = name
        self.ramps = ramps
        self.accents = accents
        self.tints = tints or {}

    def __getitem__(self, key):
        for d in (self.ramps, self.accents, self.tints):
            if key in d:
                return d[key]
        raise KeyError(key)


class Style:
    faction = None
    name = None
    palette = None                  # Palette
    atlas = None                    # the faction's shared Atlas (instance)
    ini_dir = None                  # the faction's structure INIs, e.g. data\\ini\\object\\...\\dwarven
    budget_mb = 256                 # own textures of every building of the faction, in memory

    sheet_dir = None                # the faction's building sheets, e.g. art\\compiledtextures\\db
    sheet_skip = ("_nrm", "_nmr", "_hf")        # normal maps and height fields are not recoloured

    def sheets(self, install):
        """Archive paths of every sheet of the faction to recolour."""
        return [m for m in install.members(self.sheet_dir)
                if m.endswith(".dds") and not any(k in os.path.basename(m) for k in self.sheet_skip)]

    def sheet_size(self, name):
        """Shipped size of a recoloured sheet (memory budget: most at 1024, the shared sheets 2048)."""
        return 1024

    def sheet_atlas(self, name):
        """The Atlas whose mask hints apply to a sheet (the faction atlas for its own sheet family)."""
        from .atlas import Atlas
        return self.atlas if name.lower().startswith(self.atlas.stem.lower()) else Atlas()

    def sheet_layers(self):
        """The colour layers for flat sheets (no geometry): [sagekit.paint.layers.Layer]."""
        raise NotImplementedError

    master_variants = {}            # {"damaged": "DBFortress1_D.tga", ...} the faction atlas's variants

    def master_variant(self, variant):
        """The faction atlas's sheet for the state an EA variant belongs to (new geometry's damage,
        snow and stonework painting); the atlas itself when it has none."""
        from .taxonomy import variant_class
        return self.master_variants.get(variant_class(variant), self.atlas.texture)

    def shapes(self):
        """The faction's shape library (Blender side). Subclasses return their Shapes instance."""
        raise NotImplementedError

    def layers(self, building):
        """The paint stack, bottom to top (Blender side): [sagekit.paint.layers.Layer]."""
        raise NotImplementedError
