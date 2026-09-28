"""Paint layers the Men production recipes add through Building.decals() (built on first use:
sagekit.paint needs numpy, on Blender's Python; this module must import anywhere).

    Slate   EA's blue-green slate tiles on a building's own sheet (domes, roofs) painted with the
            style's charcoal slate ramp ("tiles"), as the citadel's domes are. The faction recolour
            reads a building sheet's slate as stone and turns it pale; the atlas's mask hints only
            cover the master sheet. Selected by EA's colour (blue-green, a little saturated), the
            height and optionally a box, on EA's faces only (new faces keep their own tags).

    Keep    EA's own colour back on its saturated texels of a hue (the archer range's red targets,
            which the faction recolour greys out), on EA's faces only.

    Slate(z0=65.4)                              everything slate-coloured above z 65.4
    Slate(z0=29.5, box=(x0, x1, y0, y1))        ... inside a box (design coordinates)
"""


def Slate(*a, **kw):
    from ..paint import keep_layers         # the layers live in the style's paint module (men/paint.py)
    return keep_layers()["Slate"](*a, **kw)


def Keep(*a, **kw):
    from ..paint import keep_layers
    return keep_layers()["Keep"](*a, **kw)
