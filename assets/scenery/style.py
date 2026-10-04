"""Map scenery: EA's civilian buildings, ruins and set pieces (sagekit/scenery.py). Not a faction:
each culture's sheets take the palette of the faction it belongs to (cultures.py), through that
faction's own flat-sheet layers. This style is the "wilderland" one, for the cultures no faction
fits (the Shire, Bree, Dale, the common props): the neutral buildings' palette and grade, EA's
own colours with a little more contrast and colour, so a hobbit hole beside a captured Inn reads
as the same country."""
from assets.neutral.style import NeutralStyle


class SceneryStyle(NeutralStyle):
    faction = "scenery"
    ini_dir = "data\\ini\\object\\civilian\\"
    sheet_dir = None                    # the sheets come from the audit (sagekit/scenery.py), not a folder
    budget_mb = 160                     # recoloured EA sheets at EA's sizes: memory as EA's

    def sheet_layers(self):
        from .paint import SheetGrade
        return [SheetGrade()]
