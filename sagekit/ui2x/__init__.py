"""Retina 2x for the command bar's MappedImages and the tooltip frame (docs/UI2X.md).

A MappedImage draws `Coords` over the size its INI declares (TextureWidth/Height), not over the
loaded page's size: EA's own 2.02 patch ships `ResourceBarIcons` declared 256 x 32 on a 512 x 64
page and it draws whole. So a page twice the size, with the INI untouched, draws every image at
the same place and size with four times the texels. This package doubles:

  1  the pages our building icons sit on (sagekit/icons: our crops from the 4x renders, EA's other
     images on those pages upscaled): built here, shipped in !!!!!!!!!!!!!!sagekit-icons.big
  2  unit and hero portraits, 3  64 px buttons (unit commands, hero abilities, the hero bar, the
     spell book): EA's paintings upscaled (Real-ESRGAN with EA's grain put back, masks redrawn)
  4  the tooltip frame (APT ingamehelpbox / ingamenotificationbox, PalantirExport's helpBox*
     images): repainted in our bronze and gold, 2x, the two movies' matrices doubled

Items 2-4 ship in !!!!!!!!!!!!!!sagekit-ui2x.big; a page the icon archive carries is never in it.
"""
import os

from .. import paths

ARCHIVE = "!!!!!!!!!!!!!!sagekit-ui2x.big"     # fourteen '!': before EA's archives and apt/ folder

# the MappedImage INIs whose pages double (item: what), under data\ini\mappedimages\aptimages
INIS = {
    "unitportraits.ini": "portraits",
    "heroui.ini": "portraits",                # hero portraits and their ability buttons
    "expansion1icons.ini": "portraits",       # RotWK's portraits and buttons
    "unitcommands.ini": "buttons",
    "heroselecticons.ini": "buttons",          # the hero bar
    "spellbook.ini": "buttons",
}


def root(*parts):
    """build/assets/_ui2x: EA's pages, the upscales, our 2x pages, the staged archive."""
    p = os.path.join(paths.BUILD, "_ui2x", *parts)
    os.makedirs(os.path.dirname(p) if parts else p, exist_ok=True)
    return p
