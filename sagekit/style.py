"""A faction's look: one palette, one set of materials, one shape vocabulary, one paint stack.

Every building of a faction imports the same Style, so a gold is the same gold everywhere. The
class is declarative and importable anywhere; its Blender-side parts (shapes, paint layers) are
built on demand inside Blender through `shapes()` and `layers()`.
"""


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

    def shapes(self):
        """The faction's shape library (Blender side). Subclasses return their Shapes instance."""
        raise NotImplementedError

    def layers(self, building):
        """The paint stack, bottom to top (Blender side): [sagekit.paint.layers.Layer]."""
        raise NotImplementedError
