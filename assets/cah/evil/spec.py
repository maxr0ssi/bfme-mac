"""What the three Evil class folders share in their design.py: budgets, the bones each row's parts
may ride (every Evil rig's names), upgrade naming and the anatomy registration.

Upgrades are named per class folder (`Upgrade_SKH_<STEM>_CHH01`, ...; the class's own stem: SOS,
CMEN, OLOG), as one upgrade serves every subclass of its class that lists it (EA's own upgrades
do the same: Upgrade_Uruk_CHH02 is the Orc's and the Uruk's). Weapons take the Evil weapon-set
flags 58-64 (docs/CAH.md) in the order the classes list them.
"""
from . import anatomy

BUDGET = {"CreateAHero_Helmet": (650, 950), "CreateAHero_ShoulderPlates": (700, 1100),
          "CreateAHero_Shield": (600, 900), "CreateAHero_Weapon": (540, 700)}
CAPE = (900, 1350)
HEADS = {"B_HEAD", "BAT_HEAD", "TROLL HEAD", "BIP HEAD"}
ARMS = {"BAT_UARML", "BAT_UARMR", "TROLLLUPPERARM", "TROLLRUPPERARM", "BIP L UPPERARM", "BIP R UPPERARM"}
TRUNK = {"BAT_SPINE2", "BAT_RIBS", "TROLLSPINE1", "BIP SPINE1", "BAT_SPINE1", "B_PELVIS", "B_WAIST", "TROLLPELVIS", "BIP PELVIS"}
FOREARMS = {"B_FARML", "BAT_FARML", "TROLLLFOREARM", "BIP L FOREARM"}
WEAPONS = {"B_HAND_R", "B_HANDR", "FIREPOINT01", "TRUNK01", "WEAPONCOB", "WEAPON", "B_SWORD"}
BONES = {"CreateAHero_Helmet": HEADS, "CreateAHero_ShoulderPlates": ARMS | TRUNK, "CreateAHero_Shield": FOREARMS,
         "CreateAHero_Weapon": WEAPONS}
SUFFIX = {"CreateAHero_Helmet": "CHH", "CreateAHero_ShoulderPlates": "CHSP", "CreateAHero_Shield": "CHS"}


def parts(stem, entries, flags):
    """PARTS from [(sub-object, group, design, name, description, sheet, remap, [subclass indices])]
    in append order: helmets, shoulders and shields numbered per row, weapons on `flags`."""
    count, flags, out = {}, iter(flags), []
    for k, g, d, n, t, sheet, remap, subs in entries:
        if g == "CreateAHero_Weapon":
            up = "Upgrade_SKH_CHW%02d" % next(flags)
        else:
            count[g] = count.get(g, 0) + 1
            up = "Upgrade_SKH_%s_%s%02d" % (stem, SUFFIX[g], count[g])
        out.append((k, g, d, n, t, sheet, remap, up, subs))
    return out


def budget_of(capes):
    def budget(name, group, kind):
        return (CAPE if name in capes else BUDGET[group])[0 if kind in ("u", "m") else 1]
    return budget


def register(spec, refs):
    anatomy.register(spec, {m: refs[m] for m in spec.SKELETONS})
