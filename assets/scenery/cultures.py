"""The map scenery's cultures: which culture an EA civilian object belongs to, and whose palette
its sheets take (sagekit/scenery.py).

A culture is a look on the maps (Osgiliath's ruins, the Shire's smials, Erebor's halls), not a
player: its sheets take the palette of the faction it belongs to, graded with that faction's own
flat-sheet layers (`Style.sheet_layers`, the ones `sagekit sheets` runs), or "wilderland", EA's own
colours graded (the neutral capturable buildings' look, assets/neutral/paint.py) where no faction
fits. One culture per sheet: a sheet several cultures draw takes the palette of the one that
places it on the most multiplayer maps.
"""
import re

# key: (label, palette: a faction's style or "wilderland"[, StoneRecolour options: assets/scenery/paint.py])
OSGILIATH = dict(stone_hues=(195, 300), earth_hues=(12, 70))    # lilac and blue bricks; brown earth stays
CULTURES = {
    "gondor": ("Gondor, Osgiliath and Ithilien", "men", OSGILIATH),
    "arnor": ("Arnor's ruins: Fornost, Amon Sul, Weathertop", "men"),
    "rohan": ("Rohan and Helm's Deep", "wilderland"),       # timber and thatch: Gondor's white bleached them
    "elven": ("Elven: Rivendell, Grey Havens, Harlindon, Lorien", "elves"),
    "dwarven": ("Dwarven: Erebor, the Blue Mountains, the Iron Hills", "dwarves"),
    "dale": ("Dale and Lake-town", "wilderland"),
    "shire": ("The Shire, Bree and the villages", "wilderland"),
    "mordor": ("Mordor, Minas Morgul, Dol Guldur, Harad and Rhun", "mordor"),
    "angmar": ("Angmar: Carn Dum, the Ettenmoors, Rhudaur", "angmar"),
    "moria": ("Moria: Khazad-dum's halls and the goblins' props", "dwarves"),   # dwarven stonework; the
    # Goblins' near-black stone turned its halls, bones and buckets to black
    "isengard": ("Isengard", "isengard"),
    "wilderland": ("Common props and Dunland: carts, fences, barrels, rubble, hide huts", "wilderland"),
}

# civilian\<stem>[buildings|modules].ini -> culture
FILES = {"osgiliath": "gondor", "ministirith": "gondor", "minastirithstructureupgrades": "gondor",
         "ithilien": "gondor", "amonsul": "arnor", "fornost": "arnor", "angfornost": "arnor", "weathertop": "arnor",
         "rohan": "rohan", "helmsdeep": "rohan", "rivendell": "elven", "greyhaven": "elven", "harlindon": "elven",
         "erebor": "dwarven", "bluemountains": "dwarven", "dale": "dale", "shire": "shire",
         "minasmorgul": "mordor", "necromancerstatue": "mordor", "carndum": "angmar", "ettenmoors": "angmar",
         "moria": "moria"}
# (object name, culture), first match wins: the mixed files (civilianbuildings, civilianprop, obsolete)
NAMES = [
    (r"rohan|edoras|westfold|helm|goldenhall|refugee|meduseld|emnet|fangorn", "rohan"),
    (r"^LB|lake|esgaroth|dale|towerhills|celduin", "dale"),
    (r"shire|hobbit|bree|bywater|buckland|bagend|bombadil", "shire"),
    (r"erebor|dwar|ironhill|bluemou?n", "dwarven"),
    (r"rivendell|greyhaven|harlindon|lothlorien|lorien|mirkwood|elven|lindon|eregion", "elven"),
    (r"carndum|ettenmoor|angmar|angforn|rhudaur|gundabad", "angmar"),
    (r"moria|goblin|troll", "moria"),
    (r"dunland|wildmen", "wilderland"),             # the Dunlendings' hide huts, not Isengard's iron
    (r"isengard|orthanc", "isengard"),
    (r"mordor|morgul|baraddur|blackgate|harad|easterling|corsair|umbar|rhun|khand|dolgoldur|dogoldur|"
     r"darkfortress|lavabridge|cirithungol", "mordor"),
    (r"amonsul|fornost|arnor|weathertop", "arnor"),
    (r"gondor|minastirith|osgiliath|ithilien|amonhen|cairandros|argonath|anfalas|belfalas|dolamroth|"
     r"pelargir", "gondor"),
]
# a model's two-letter prefix, when nothing else says
PREFIX = {"gb": "gondor", "os": "gondor", "rb": "rohan", "sb": "shire", "db": "dwarven", "lb": "dale", "eb": "elven",
          "kb": "angmar", "wb": "moria", "ib": "isengard", "mb": "mordor"}
# everyday props (civilianprop.ini) are everyone's, whatever map they were made for: the Wilderland grade
PROPS = re.compile(r"suppl|barrel|crate|sack|cart|wagon|boat|fence|hay|log|wood|bucket|basket|tent|well|"
                   r"barric|timber|furniture|debris", re.I)
UNITS = ("civilianunit.ini",)       # townsfolk, animals: units, not scenery
# map props EA filed in a faction's folder, with their culture: placed by maps, built by nobody
ALSO = {"Tower_FromZeroHourThatCanTopple": "gondor"}     # Osgiliath's falling tower (goodfaction\structures)


def culture_of(obj, member, models):
    """The culture of object `obj` defined in INI `member`, drawing `models`."""
    parts = member.lower().split("\\")
    stem = re.sub(r"(buildings|modules)?\.ini$", "", parts[-1])
    if parts[3] == "civilian" and stem in FILES:
        return FILES[stem]
    if parts[-1] == "civilianprop.ini" and PROPS.search(obj):
        return "wilderland"
    if "rohan" in parts[4:-1]:
        return "rohan"
    for rx, c in NAMES:
        if re.search(rx, obj, re.I):
            return c
    for m in models:
        if m[:2].lower() in PREFIX:
            return PREFIX[m[:2].lower()]
    return "wilderland"
