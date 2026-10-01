"""Men of the West builder: a stub that ships EA's GUPorter_SKN unchanged until its design lands.

The facts are in README.md; the recipe API in docs/UNITS.md; the Dwarven builder
(assets/dwarves/porter/design.py) is the template. python3 -m sagekit unit men/porter --render
"""
from sagekit.units import Unit


class Porter(Unit):
    """Gondor's porter, drawn by MenPorter and ArnorPorter alike: redesigned in place."""
    model, skeleton = "GUPorter_SKN", "GUPorter_SKL"
    anims = ("idla", "idlb", "runa", "wlka", "wrka", "wrkb", "fira", "diea", "dieb")
    expected = {"guporter_skn": "5055def66f8974b886111cf7be4287d0b19537ea38f1f482030524021bbf5710",
                "guporter_skl": "cb8a6fa38469fd95ac1c791843a75c013fdec5684503b4711b0485a4eee5e9ec"}
    archive = "!!!!!!!!!!!!sagekit-men-builder.big"
    smooth = ("GUPORTERLUIGI",)
    labels = ("EA'S MEN OF THE WEST BUILDER", "STUB: EA'S, UNCHANGED")
    # The design adds: textures {EA sheet: private, e.g. "GUPorter.tga": "GUCrafts.tga"}, house,
    # mask ("HC_GUPorter.tga", "HC_GUCrafts.tga"), design(w, sk) and paint(b).
