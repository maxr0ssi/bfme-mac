"""Mordor builder: a stub that ships EA's WUPorter_SKN unchanged, as MUBuilder_SKN, until its design lands.

The facts are in README.md; the recipe API in docs/UNITS.md; the Dwarven builder
(assets/dwarves/porter/design.py) is the template. python3 -m sagekit unit mordor/porter --render
"""
from sagekit.units import DEFAULT_VIEWS, Unit


class Porter(Unit):
    """EA's orc porter, which Isengard, Mordor, the Goblins and Angmar all draw: ours ships under a
    name of its own and only MordorPorter's Draw is repointed to it (Angmar keeps EA's)."""
    model, skeleton = "WUPorter_SKN", "MUOrcPrtr_SKL"
    own_model = "MUBuilder_SKN"
    objects = {"MordorPorter": ("data\\ini\\object\\evilfaction\\units\\mordor\\porter.ini", "ModuleTag_01")}
    anims = ("idla", "idlb", "runa", "wlka", "fira", "diea", "dieb")
    expected = {"wuporter_skn": "0f3aa90adf5415d9242ba1c7cf33807ce3d6bd2774b73e6bd195ca31cae8e47f",
                "muorcprtr_skl": "7d4d2bd88941d3c41bef5f778a9fa47f0967f10067220a2a97aa404d149766df"}
    archive = "!!!!!!!!!!!!sagekit-mordor-builder.big"
    smooth = ("ORCPORTER",)
    views = {k: v for k, v in DEFAULT_VIEWS.items() if k != "work"}     # EA's orc porter never builds
    labels = ("EA'S ORC PORTER (MORDOR)", "STUB: EA'S, UNCHANGED")
    # The design adds: textures {EA sheet: private}, house, mask (EA's HC_MUPortCart.tga is the
    # cart's, 64 px; the orc's sheet has no mask), design(w, sk) and paint(b).
