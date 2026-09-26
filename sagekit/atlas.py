"""A faction's shared source texture sheet ("atlas"): where its materials and motifs are painted.

Two uses, both declared here and implemented where they run:
  - mapping new geometry onto the ORIGINAL sheet (sagekit/blender/mapping.py): Regions say which
    rectangle holds plain stone, a frieze, a relief, and how it tiles;
  - material masks for the painter (sagekit/paint/masks.py): colour rules plus hint rectangles
    where colour alone is ambiguous.
Coordinates: Region rects in the original sheet's pixels (x right, y down); mask hints in the
2048 upscale's pixels (same orientation).
"""


class Region:
    TILE, BAND, STRETCH = "tile", "band", "stretch"

    def __init__(self, rect, kind=TILE, su=None, period=None):
        self.rect = rect            # (x0, y0, x1, y1)
        self.kind = kind            # TILE: repeat at the atlas density; BAND: a frieze along one axis;
        self.su = su                # STRETCH: one motif fitted to the face. BAND: horizontal px/unit
        self.period = period        # (None = square pixels); pattern repeat in px (whole repeats only)

    @property
    def size(self):
        x0, y0, x1, y1 = self.rect
        return x1 - x0, y1 - y0


class Atlas:
    texture = None                  # "DBFortress1.tga": the sheet the game's models reference
    normal = None                   # "DBFortress1_NRM.tga"
    size = 512                      # original resolution
    upscale = 4                     # the painter works from an AI upscale of the sheet
    density = 3.0                   # atlas px per world unit on plain stone (as the game's walls)
    max_shrink = 1.45               # a face this much bigger than a tile is shrunk into one
    regions = {}                    # name -> Region
    painted = ()                    # regions whose new faces are a material of their own (repainted by
                                    # a TagRamp, e.g. banner cloth): never stone, no masonry or moss
    mask_hints = {}                 # mask name -> [(x0, y0, x1, y1)] in upscale pixels
    ground_sat = (0.08, 0.2)        # saturation ramp over which teal-blue texels outside the band hints
                                    # read as band ground (enamel): a faction whose plain stone and bark
                                    # are themselves blue-grey raises it (sagekit/paint/masks.py)
    keep = {}                       # name -> [(x0, y0, x1, y1)] original px: EA's painted motifs the flat
                                    # sheet recolour leaves as painted where they are not stone (the Elven
                                    # eagle; sagekit/paint/sheets.py)

    @classmethod
    def region_names(cls):
        return list(cls.regions)

    @property
    def stem(self):
        return self.texture[:-4]
