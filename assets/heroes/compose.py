"""The heroes pack's INI: EA's effective 2.02 files with our heroes added, composed in one place.

  playertemplate.ini            Men recruit Gamling, Damrod and Earnur; Dwarves the Captain of Erebor
  commandset.ini                every Men and Dwarven hero building gets a revive slot per hero; the
                                Captain's and Gamling's command sets
  commandbutton.ini             the hero submenus count the new slots; our power buttons (copies of EA's)
  default\\skirmishaidata.ini    the AI recruits the new heroes late in a game, after its own
  experiencelevels.ini          the Captain's levels (Gloin's), Earnur's (Aragorn's), Gamling's grant 1, 3, 6
  specialpower.ini              one power of our own (the Captain's Royal Guard: Dain's, no Dain voice)
  object\\...\\rohan\\gamling.ini  Gamling finished (assets/heroes/gamling.py)
  object\\...\\men\\earnur.ini     Earnur's own recruit text
  object\\...\\men\\aragorn.ini    our model for Aragorn, his level-8 armour shown by a SubObjectsUpgrade
  object\\...\\dwarven\\sagekitereborcaptain.ini   the Captain (new file)
  mappedimages\\aptimages\\heroui.ini, heroselecticons.ini   our portraits and icons
No Upgrade is added (the engine holds 1152; sagekit/upgrades.py): every level gate is EA's
Upgrade_ObjectLevelN. Strings: assets/heroes/strings.py.
"""
import re

from . import ea, gamling, levels, portraits, powers, roster
from .captain import hero as captain
from .text import NL, append, lf_to, module_span, object_span, set_field

I = ea.I
O = I + "object\\goodfaction\\units\\"
FILES = {"playertemplate": I + "playertemplate.ini", "commandset": I + "commandset.ini", "commandbutton": I + "commandbutton.ini",
         "skirmishai": I + "default\\skirmishaidata.ini", "levels": I + "experiencelevels.ini", "specialpower": I + "specialpower.ini",
         "gamling": O + "rohan\\gamling.ini", "earnur": O + "men\\earnur.ini", "aragorn": O + "men\\aragorn.ini",
         "heroui": I + "mappedimages\\aptimages\\heroui.ini", "heroselecticons": I + "mappedimages\\aptimages\\heroselecticons.ini"}
NEW_FILES = {"captain": O + "dwarven\\sagekitereborcaptain.ini"}
ROSTER = {"Men": [("RohanGamling", "RohanEowyn"), ("GondorDamrod", "RohanGamling"), ("GondorEarnur", "GondorDamrod")],
          "Dwarves": [("DwarvenEreborCaptain", "DwarvenCaptainofDale")]}
AI_SHARE = 7.5                                  # PercentageOfArmyPhase3, as EA's late heroes
EARNUR_RECRUIT = ("CONTROLBAR:SagekitEarnurRecruit", "Recruit Earnur, the last King of Gondor \\n \\n Unit Type: Tier 4 Hero \\n "
                  "Recruit Time: 50s \\n Health Regeneration: 30/s")
ARAGORN = dict(model=("GUAragorn_SKN", "SKAragorn_SKN"), tag="SKH_AragornKingsArmour", show="SKAR_KINGSARM SKAR_KINGTRIM",
               trigger="Upgrade_ObjectLevel8")


def read_all():
    return {k: ea.text(m) for k, m in FILES.items()}


def all_powers():
    return [("EreborCpt", captain.POWERS), ("Gamling", gamling.POWERS)]


def strings():
    """Every label the pack adds or corrects, with its text."""
    out = list(captain.STRINGS) + list(gamling.STRINGS) + [EARNUR_RECRUIT]
    for _, ps in all_powers():
        for p in ps:
            out.append((p.tooltip[0], p.tooltip[1].format(recharge=powers.recharge(p))))
            if p.label:
                out.append(p.label)
    labels = [k.lower() for k, _ in out]
    dup = {k for k in labels if labels.count(k) > 1}
    if dup:
        raise SystemExit("heroes: labels given twice: %s" % sorted(dup))
    return out


def aragorn(src):
    """aragorn.ini: GondorAragorn's Draw (which GondorAragornMP inherits) draws our model, LOD off,
    and the King's armour waits for level 8."""
    s, e = object_span(src, "GondorAragorn")
    t = src[s:e]
    a, b = module_span(t, "ModuleTag_DRAW")
    draw = t[a:b]
    old, new = ARAGORN["model"]
    draw = set_field(draw, "Model", new, comment="EA's %s with the level-8 armour, hidden until then" % old)
    draw = set_field(draw, "StaticModelLODMode", "No", comment="our model has no M/L copies")
    t = t[:a] + draw + t[b:]
    block = ("\tBehavior = SubObjectsUpgrade %s\t; sagekit heroes: the King's armour at level 8\r\n"
             "\t\tTriggeredBy\t\t= %s\r\n\t\tShowSubObjects\t= %s\r\n\tEnd\r\n\r\n" % (ARAGORN["tag"], ARAGORN["trigger"], ARAGORN["show"]))
    end = t.rstrip().rfind("\nEnd")
    t = t[:end + 1] + block + t[end + 1:]
    return src[:s] + t + src[e:]


def earnur(src):
    s, e = object_span(src, "GondorEarnur")
    t = set_field(src[s:e], "RecruitText", EARNUR_RECRUIT[0], comment="EA's pointed at Boromir's")
    return src[:s] + t + src[e:]


def compose(ea_files=None):
    """{key: composed text} for every file of FILES and NEW_FILES; and the report."""
    f = dict(ea_files or read_all())
    report = {"roster": {}, "slots": []}
    for faction, heroes in ROSTER.items():
        for hero, after in heroes:
            f["playertemplate"] = roster.append_roster(f["playertemplate"], faction, hero)
            f["skirmishai"] = roster.append_ai(f["skirmishai"], after, hero, AI_SHARE)
        f["commandset"], f["commandbutton"], done = roster.ensure_slots(f["commandset"], f["commandbutton"], f["playertemplate"], faction)
        report["slots"] += done
        report["roster"][faction] = roster.rosters(f["playertemplate"])[faction]
    sets = [powers.command_set(captain.COMMAND_SET, captain.POWERS, powers.GENERIC_HERO_COMMANDS),
            powers.command_set(gamling.COMMAND_SET, gamling.POWERS, powers.GENERIC_HERO_COMMANDS)]
    f["commandset"] = append(f["commandset"], "\n".join(sets), "the Captain of Erebor's and Gamling's command sets")
    buttons = [powers.button_text(p) for _, ps in all_powers() for p in ps]
    f["commandbutton"] = append(f["commandbutton"], "\n".join(buttons), "hero power buttons, copies of EA's with our tooltips")
    templates = [powers.template_text(p) for _, ps in all_powers() for p in ps if p.template_copy]
    f["specialpower"] = append(f["specialpower"], "\n".join(templates), "powers of our own (EA's, with a field changed)")
    lv = captain.experience_levels() + levels.copy_levels("GondorAragornMP", "GondorEarnur")
    f["levels"] = levels.add_grants(f["levels"], "RohanGamling", gamling.LEVELS)
    f["levels"] = append(f["levels"], lv, "the Captain of Erebor's levels (Gloin's) and Earnur's (Aragorn's)")
    f["gamling"] = gamling.object_file(f["gamling"])
    f["earnur"] = earnur(f["earnur"])
    f["aragorn"] = aragorn(f["aragorn"])
    images = portraits.mapped_images()
    f["heroui"] = append(f["heroui"], images["heroui"], "hero portraits")
    f["heroselecticons"] = append(f["heroselecticons"], images["heroselecticons"], "hero icons")
    f["captain"] = lf_to(NL, ";------------------------------------------------------------------------------\r\n"
                             "; The Captain of Erebor: sagekit heroes pack (assets/heroes/captain), written from\r\n"
                             "; King Dain's object in the player's own 2.02 files at build time\r\n"
                             ";------------------------------------------------------------------------------\r\n\r\n") + \
        captain.object_text() + NL
    return f, report


def members(f):
    """{archive member: bytes} of a composition (EA's line ends and latin-1 kept)."""
    keys = dict(FILES, **NEW_FILES)
    return {keys[k]: v.encode("latin-1") for k, v in f.items()}


def changed_lines(ea_files, f):
    import difflib
    out = {}
    for k, m in dict(FILES, **NEW_FILES).items():
        a = ea_files.get(k, "").splitlines()
        out[m] = sum(1 for l in difflib.unified_diff(a, f[k].splitlines(), lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---"))
    return out
