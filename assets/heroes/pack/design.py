"""The heroes pack's recipe for the shared house-colour archive (sagekit/units/install.py): one Unit
whose archive is the pack's and whose house lines are our hero sheets' masks. The pack is built by
python3 -m assets.heroes.build and staged, installed and reverted by python3 -m sagekit.units.heroes,
never by `sagekit unit`."""
from sagekit.units import Unit

ARCHIVE = "!!!!!!!!!!!sagekit-heroes.big"


class HeroesPack(Unit):
    """The heroes pack's archive and house-colour lines."""
    model, skeleton = "DUDain_SKN", "DUDain_SKL"
    house = {"skcapg.tga": "hc_skcapg.tga", "skcapc.tga": "hc_skcapc.tga", "skaragornl8.tga": "hc_skaragornl8.tga",
             "skaragorn_kng.tga": "hc_skaragorn_kng.tga"}
    textures = {t: t for t in house}
    archive = ARCHIVE

    def design(self, w, sk):
        raise SystemExit("heroes/pack is the heroes pack: python3 -m assets.heroes.build, then "
                         "python3 -m sagekit.units.heroes --stage | --install | --revert")
