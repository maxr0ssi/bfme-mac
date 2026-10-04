"""One palantir frame per faction (docs/HUD.md, "One palantir per faction").

FACTIONS is stdlib (sagekit/hud reads it): per look, its side (the EA frame it is drawn over: the
Good or the Evil page, same layout and alpha) and the PlayerTemplate `Side` strings the game passes
to the palantir's SetPlayerFaction that get it. Any other side (Observer, Civilian, a mod's side)
keeps the Good/Evil frame. The looks themselves (numpy) are the modules beside this one.
"""

FACTIONS = {
    "dwarves": dict(side="good", sides=["Dwarves"], what="Erebor gold, blue enamel, chevrons, runes"),
    "elves": dict(side="good", sides=["Elves"], what="moonsilver, leaf-and-vine filigree"),
    "men": dict(side="good", sides=["Men", "Arnor"], what="Gondor silver and white stone, sable stars, the White Tree"),
    "isengard": dict(side="evil", sides=["Isengard"], what="black iron, bright silver, cogs, the White Hand"),
    "mordor": dict(side="evil", sides=["Mordor"], what="black iron and ash, fire seams, Morgul green, steel blades"),
    "goblins": dict(side="evil", sides=["Wild"], what="crude bronze, fangs, skulls, lashings"),
    "angmar": dict(side="evil", sides=["Angmar"], what="frost-rimed iron, ice crystals, glints"),
}


def look(name):
    """The faction's look (numpy; Blender's Python)."""
    import importlib
    mod = importlib.import_module("assets.hud.factions." + name)
    return mod.LOOK()
