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
    ini_dir = None                  # the faction's structure INIs, e.g. data\\ini\\object\\...\\dwarven; or a
                                    # list of folders and files (every one is the faction's)
    budget_mb = 512                 # own textures of every building of the faction, in memory: RotWK has 4 GB
                                    # (docs/MEMORY-4GB.md); 1.03 bytes of it per texture byte (MEMORY-2GB.md)

    sheet_dir = None                # the faction's building sheets, e.g. art\\compiledtextures\\db
    sheet_skip = ("_nrm", "_nmr", "_hf")        # normal maps and height fields are not recoloured
    shared_sheets = {}              # {EA sheet other factions draw too: the faction's recoloured copy},
                                    # same length, e.g. {"EBForge.tga": "DBAnvil.tga"} (sagekit/sharedsheets.py)

    def ini_dirs(self):
        """Every INI folder (or file) whose objects draw the faction's buildings: `ini_dir`, and the
        structure folder of each group that reuses the faction's models one for one and counts as
        its own (sagekit/ownership.py FOLLOWS: Arnor's structures\\arnor for the Men), so the
        redesign's INI work (swaps, own models, house draws, hidden banners) reaches it too."""
        from .ownership import FOLLOWS
        dirs = [self.ini_dir] if isinstance(self.ini_dir, str) else list(self.ini_dir or ())
        for group in sorted(g for g, f in FOLLOWS.items() if f == self.faction):
            for d in list(dirs):
                parts = d.rstrip("\\").split("\\")
                if parts[-2:-1] == ["structures"]:
                    sib = "\\".join(parts[:-1] + [group]) + "\\"
                    if sib.lower() not in {x.lower().rstrip("\\") + "\\" for x in dirs}:
                        dirs.append(sib)
        return dirs

    def sheets(self, install):
        """Archive paths of every sheet of the faction to recolour: its DDS sheets, and the few EA
        shipped only as TGA (the Isengard tavern's ibwildbuilding family; no other faction's folder
        has one). ownership.faction_sheets drops a TGA no model draws (the tavern's button image)."""
        members = install.members(self.sheet_dir)
        dds = {m[:-4] for m in members if m.endswith(".dds")}
        return [m for m in members if (m.endswith(".dds") or m.endswith(".tga") and m[:-4] not in dds)
                and not any(k in os.path.basename(m) for k in self.sheet_skip)]

    def sheet_size(self, name):
        """Shipped size of a recoloured sheet (memory budget: most at 1024, the shared sheets 2048)."""
        return 1024

    def sheet_atlas(self, name):
        """The Atlas whose mask hints apply to a sheet (the faction atlas for its own sheet family)."""
        from .atlas import Atlas
        if name.lower().startswith(self.atlas.stem.lower()):
            return self.atlas
        a = Atlas()
        a.ground_sat = self.atlas.ground_sat        # the faction's colour rules read its other sheets too
        return a

    def sheet_layers(self):
        """The colour layers for flat sheets (no geometry): [sagekit.paint.layers.Layer]."""
        raise NotImplementedError

    # palette options for the owner's pick (`sagekit palettes <faction>`, sagekit/palettes.py): the
    # choices, a line on each, the recipe whose EA model shows them, its views, and the swatches
    # under each column as (label, ramp, position)
    palettes = {}                   # {"A": Palette, ...}
    palette_notes = {}              # {"A": "near-black stone, ..."}
    palette_ea_note = ""            # a line on EA's own column
    palette_building = 'fortress'
    palette_views = ('rts', 'close')
    swatches = ()

    night = None                    # NightLook: the faction's night lights (sagekit/nightlights.py);
                                    # None keeps EA's night meshes
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
