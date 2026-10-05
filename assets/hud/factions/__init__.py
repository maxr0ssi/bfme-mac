"""One palantir frame per faction (docs/HUD.md, "One palantir per faction").

FACTIONS is stdlib (sagekit/hud reads it): per look, its side (the EA frame it is drawn over: the
Good or the Evil page, same layout and alpha) and the PlayerTemplate `Side` strings the game passes
to the palantir's SetPlayerFaction that get it. Any other side (Observer, Civilian, a mod's side)
keeps the Good/Evil frame. The looks themselves (numpy) are the modules beside this one, each cut
from its citadel: its surfaces are swatches of the citadel's sheets (swatches.py).
"""

FACTIONS = {
    "dwarves": dict(side="good", sides=["Dwarves"], what="Erebor granite, gold coping, the rune and triangle friezes, chevron shields"),
    "elves": dict(side="good", sides=["Elves"], what="ivory ashlar, teal lancet windows, slate scales, mallorn gold"),
    "men": dict(side="good", sides=["Men", "Arnor"], what="white ashlar, corbelled battlement, the sable band of stars, the White Tree"),
    "isengard": dict(side="evil", sides=["Isengard"], what="black fluted walls, silver lancet panels and spikes, the White Hand"),
    "mordor": dict(side="evil", sides=["Mordor"], what="black fluted iron, fire-rimmed crown windows, lava, the crown of blades"),
    "goblins": dict(side="evil", sides=["Wild"], what="blood-red horn plates, black iron bands, bone tusks, skulls"),
    "angmar": dict(side="evil", sides=["Angmar"], what="timber walk, blue-black stone, steel scales, horn tines with frost"),
}


def look(name):
    """The faction's look (numpy; Blender's Python)."""
    import importlib
    mod = importlib.import_module("assets.hud.factions." + name)
    return mod.LOOK()
