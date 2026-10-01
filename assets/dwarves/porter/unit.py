"""The troop scripts' import of the builder's mesh primitives (assets/*/troops). The builder is now
a unit recipe (design.py): python3 -m sagekit unit dwarves/porter (docs/UNITS.md)."""
from sagekit.units.mesh import Mesh as _Mesh, uv_for  # noqa: F401

from .design import Porter


class Mesh(_Mesh):
    """sagekit.units.mesh.Mesh with the Dwarven builder's texture names, as the troops built on it."""

    def __init__(self, original, skeleton, keep=False):
        super().__init__(original, skeleton, keep, names=Porter.textures)
