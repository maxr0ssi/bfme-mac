"""The fixed vocabulary every asset uses: factions, lifecycle states, texture tiers and names, and
the memory budget. A building folder that breaks these rules fails `python3 -m sagekit validate`.

    assets/<faction>/                 faction id from FACTIONS
        style.py                      one Style subclass: palette, materials, shapes, paint layers
        atlas.py                      the faction's shared source texture sheet(s) (Atlas subclasses)
        <building>/                   snake_case building id
            building.py               one Building subclass
            README.md                 what changed and why, status per lifecycle state
"""
import enum
import re

from .formats.textures import dxt1_size, full_chain, tga24_size

FACTIONS = ("men", "elves", "dwarves", "isengard", "mordor", "goblins", "angmar")
ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
MB = 1 << 20


class State(enum.Enum):
    """What a building looks like when. The INI flags that select each are in FLAG_STATES."""
    HEALTHY = "healthy"
    CONSTRUCTION = "construction"
    DAMAGED = "damaged"
    REALLY_DAMAGED = "really_damaged"
    RUBBLE = "rubble"
    SNOW = "snow"
    STONEWORK = "stonework"          # the Numenor stonework upgrade
    PLACEMENT = "placement"          # the ghost while choosing where to build
    EDITOR = "editor"                # WorldBuilder only
    LOD_MEDIUM = "lod_medium"        # StaticModelLODMode: <model>M
    LOD_LOW = "lod_low"              # StaticModelLODMode: <model>L


FLAG_STATES = {
    "DAMAGED": State.DAMAGED, "REALLYDAMAGED": State.REALLY_DAMAGED, "RUBBLE": State.RUBBLE,
    "SNOW": State.SNOW, "UPGRADE_NUMENOR_STONEWORK": State.STONEWORK,
    "ACTIVELY_BEING_CONSTRUCTED": State.CONSTRUCTION, "PARTIALLY_CONSTRUCTED": State.CONSTRUCTION,
    "AWAITING_CONSTRUCTION": State.CONSTRUCTION,
    "PHANTOM_STRUCTURE": State.PLACEMENT, "BUILD_PLACEMENT_CURSOR": State.PLACEMENT,
    "WORLD_BUILDER": State.EDITOR,
}


UPGRADE_RE = re.compile(r"^UPGRADE_|_IMPROVEMENT_\d+$")


def states_of(flags):
    """frozenset of States for an INI flag set (empty flags: HEALTHY); unknown flags are ignored."""
    s = frozenset(FLAG_STATES[f] for f in flags if f in FLAG_STATES)
    return s or frozenset([State.HEALTHY])


def upgrades_of(flags):
    """The purchase flags that switch a state on (FORTRESS_IMPROVEMENT_1, UPGRADE_FORTRESS_MONUMENT...)
    - upgrades and add-ons a player buys - apart from those the States already name."""
    return tuple(sorted(f for f in flags if UPGRADE_RE.search(f) and f not in FLAG_STATES))


class Tier(enum.Enum):
    """Texture sizes. HERO for the building a faction is recognised by, STANDARD for the rest:
    at RTS distance 2048 is indistinguishable and a 32-bit game has little memory to spare."""
    HERO = (4096, 2048)
    STANDARD = (2048, 1024)

    @property
    def diffuse(self):
        return self.value[0]

    @property
    def normal(self):
        return self.value[1]

    def bytes(self, variants=0):
        """Memory one building's own textures take: DXT1 diffuse with mips, uncompressed TGA normal,
        and its state variants (damaged, snow, stonework) at half the diffuse size."""
        d, v = self.diffuse, self.diffuse // 2
        return dxt1_size(d, d, full_chain(d)) + tga24_size(self.normal, self.normal) + variants * dxt1_size(v, v, full_chain(v))


def own_texture_name(original, taken=()):
    """A building's own texture name for the sheet it was painted from, of the SAME length (W3D
    texture names are patched in place): the stem's last letter becomes H (X if it already is H):
    DBFortress1 -> DBFortressH, DBBunker -> DBBunkeH. Buildings sharing a sheet pin their own."""
    stem = original[:-4] if original.lower().endswith(".tga") else original
    name = stem[:-1] + ("X" if stem[-1].lower() == "h" else "H")
    if name.lower() in {t.lower() for t in taken}:
        raise ValueError("texture name %s is taken; pin one in the Building" % name)
    return name


def variant_class(texture):
    """damaged / snow / stonework, from EA's variant suffix (_D, _D1, _Snow, _S, _U)."""
    tail = texture[:-4].rsplit("_", 1)[-1].lower()
    return {"d": "damaged", "d1": "damaged", "d2": "damaged", "snow": "snow", "s": "snow", "u": "stonework"}.get(tail)


def own_variant_name(atlas_texture, own_texture, variant_texture):
    """A state variant of a building's own texture, named like EA named theirs:
    (DBFortress1.tga, DBFortressH.tga, DBFortress1_D.tga) -> DBFortressH_D.tga,
    (DBFortress1.tga, DBFortressH.tga, DBFortress_U.tga)  -> DBFortressH_U.tga."""
    a, v = atlas_texture[:-4], variant_texture[:-4]
    n = 0
    while n < min(len(a), len(v)) and a[n].lower() == v[n].lower():
        n += 1
    return own_texture[:-4] + v[n:] + ".tga"


def check_id(kind, value):
    if not ID_RE.match(value):
        raise ValueError("%s id %r: lower-case snake_case only" % (kind, value))
    if kind == "faction" and value not in FACTIONS:
        raise ValueError("faction %r: one of %s" % (value, ", ".join(FACTIONS)))
