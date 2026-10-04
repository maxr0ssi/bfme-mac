"""Gamling for the Men: EA's RohanGamling (gamling.ini, Side = Obsolete) finished from EA's own parts.

EA left him half-built in 2.02: no portrait or hero icon (both commented out), Boromir's voice and
revive button, HwaldarAxe as a placeholder weapon ("to make room for line limit in weapon.ini"),
no powers but a hidden leadership stub, no stances, no capture. His Draw already carries
Boromir's power animations (the horn, SPECIAL_POWER_1; the captain's call, PACKING_TYPE_2), so
his powers are Boromir's modules, renamed for Rohan:

  L1  Leadership                 the hero aura (Boromir's GenericHeroLeadership module)
  L3  Horn of Helm Hammerhand    Boromir's Horn of Gondor (enemies debuffed, stunned from level 5)
  L6  Captain of the Guard       Boromir's Captain of Gondor (experience to targeted troops), no voice line

Also: his model is EA's unused, more detailed RUGamlingCH_SKN with the sword and shield of the
model EA drew (gamling_model.py); Boromir's sword (tier 2, like Boromir: 1400, 2400 health), the Create-a-Hero captain's
voice (HeroWestMale), our portrait and icon (HPGamling, HIGamling, HIGamling_res), stances,
capture, tier-2 command points, Men as his side, his ten levels granting 1, 3 and 6.
"""
import re

from . import ea
from .powers import GENERIC_HERO_COMMANDS, Module, Power
from .text import module_span, object_span, set_field

NAME = "RohanGamling"
MEMBER = ea.I + "object\\goodfaction\\units\\rohan\\gamling.ini"
COMMAND_SET = "SagekitGamlingCommandSet"
PORTRAIT, BUTTON = "HPGamling", "HIGamling"
LEVELS = (1, 3, 6)
VOICE = {"VoiceAttack": "HeroWestMaleVoiceAttack", "VoiceAttackCharge": "HeroWestMaleVoiceAttackCharge",
         "VoiceAttackMachine": "HeroWestMaleVoiceAttack", "VoiceAttackStructure": "HeroWestMaleVoiceAttackBuilding",
         "VoiceFear": "HeroWestMaleVoiceHelpMe", "VoiceMove": "HeroWestMaleVoiceMove", "VoiceMoveToCamp": "HeroWestMaleVoiceMoveCamp",
         "VoiceMoveWhileAttacking": "HeroWestMaleVoiceDisengage", "VoiceRetreatToCastle": "HeroWestMaleVoiceRetreat",
         "VoiceSelect": "HeroWestMaleVoiceSelectMS", "VoiceSelectBattle": "HeroWestMaleVoiceSelectBattle",
         "VoiceGuard": "HeroWestMaleVoiceMove", "VoiceGarrison": "HeroWestMaleVoiceMoveGarrison"}
S = "CONTROLBAR:SagekitGamling"
B = "obj:GondorBoromir"
POWERS = [
    Power(2, 1, "Command_SpecialAbilityTheodenLeadership", "Command_SKH_GamlingLeadership",
          [Module(B, "ModuleTag_BoromirLeadership", {"TriggeredBy": "Upgrade_ObjectLevel1"})],
          (S + "LeadershipTip", "Modifier Type: Leadership \\n Allies near Gamling gain +25% Damage, +25% Armor, and earn "
                                "Experience 50% faster \\n Stacks with Buffs and Spells \\n Radius: 200 \\n Passive ability"),
          template="SpecialAbilityFakeLeadership"),
    Power(3, 3, "Command_SpecialAbilityHornOfGondor", "Command_SKH_GamlingHorn",
          [Module(B, "ModuleTag_HornStarter"), Module(B, "ModuleTag_HornUpdate"), Module(B, "ModuleTag_ElendilAutoAbility")],
          (S + "HornTip", "Requires Level 3 \\n Gamling sounds the Horn of Helm Hammerhand \\n Enemy units within a large radius "
                          "suffer -20% Damage and -20% Armor, and are briefly stunned from Level 5 \\n Debuff Radius: 350 \\n "
                          "Debuff Duration: 20s \\n Recharge Time: {recharge} \\n Left click to activate"),
          label=(S + "Horn", "Horn of Helm Hamme&rhand"), ai="AI_SPELLBOOK_ARMY_BREAKER", ai_radius=225.0),
    Power(4, 6, "Command_SpecialAbilityCaptainOfGondorBoromir", "Command_SKH_GamlingCaptain",
          [Module(B, "ModuleTag_KingsFavorSpecialPowerModule", {"InitiateSound": None}), Module(B, "ModuleTag_KingsFavor"),
           Module(B, "ModuleTag_KingsFavorAutoAbility")],
          (S + "CaptainTip", "Requires Level 6 \\n The captain of Theoden's guard drills targeted units: they gain good "
                             "Experience \\n Experience Yield: 90 XP \\n Target Radius: 150 \\n Target Range: 200 \\n "
                             "Recharge Time: {recharge} \\n Left click icon then left click on target units"),
          label=(S + "Captain", "Captain of the &Guard"), ai="AI_SPECIAL_POWER_GIVEXP_AOE", ai_radius=150.0),
]
STRINGS = [
    ("CONTROLBAR:RohanGamlingHotkey", "&Gamling"),                       # EA's label, missing from 2.02's table
    ("CONTROLBAR:RohanGamlingRevive", "Revive the fallen Hero, Gamling"),  # EA's reads "Revive Gaming"
    ("CONTROLBAR:RohanGamlingRecruit", "Recruit the captain of Theoden's Royal Guard \\n \\n Unit Type: Tier 2 Hero \\n "
                                       "Recruit Time: 40s \\n Health Regeneration: 30/s"),
    ("TOOLTIP:SagekitGamling", "Damage Type: Hero \\n Melee Attack Speed: 1.5s \\n Movement Speed: 50 \\n Vision Range: 300"),
]
EXTRA = (Module(B, "ModuleTag_StancesBehavior"), Module(B, "GondorFighterHordeStanceBattle"),
         Module(B, "GondorFighterHordeStanceAggressive"), Module(B, "GondorFighterHordeHoldGround"))


def object_file(src):
    """gamling.ini with Gamling finished (every other line EA's)."""
    s, e = object_span(src, NAME)
    t = src[s:e]
    for key, img in (("SelectPortrait", PORTRAIT), ("ButtonImage", BUTTON)):
        t, n = re.subn(r"^[ \t]*;[ \t]*%s[ \t]*=[ \t]*\S+[^\r\n]*" % key, "\t%s = %s\t; sagekit heroes: EA's line was commented out" % (key, img),
                       t, count=1, flags=re.M)
        if n != 1:
            raise SystemExit("heroes: gamling.ini: no commented %s" % key)
    t = set_field(t, "Model", "SKGamling_SKN", comment="EA's unused RUGamlingCH_SKN with EA's sword and shield")
    t = set_field(t, "StaticModelLODMode", "No", comment="our model has no M/L copies")
    t = set_field(t, "Side", "Men", comment="was Obsolete")
    t = set_field(t, "BuildTime", "HERO_BUILDTIME_TIER_2")
    t = re.sub(r"^([ \t]*Weapon[ \t]*=[ \t]*PRIMARY[ \t]+)HwaldarAxe\b[^\r\n]*", r"\g<1>BoromirSword\t; sagekit heroes: was EA's placeholder",
               t, count=1, flags=re.M)
    t = set_field(t, "CommandSet", COMMAND_SET)
    t = set_field(t, "CommandPoints", "HERO_COMMAND_POINTS_TIER_2")
    t = re.sub(r"(^[ \t]*CommandPoints[ \t]*=[^\r\n]*\r?\n)", r'\g<1>    #include "..\\..\\..\\CORRODE_ALLEGIANCE_CP_HACK_TIER_2.inc"\t; sagekit heroes\r\n',
               t, count=1, flags=re.M)
    t = re.sub(r"(^[ \t]*DisplayName[ \t]*=[^\r\n]*\r?\n)", r"\g<1>\tDescription = TOOLTIP:SagekitGamling\t; sagekit heroes\r\n", t, count=1, flags=re.M)
    for key, event in VOICE.items():
        t = set_field(t, key, event)
    t = re.sub(r"^[ \t]*EvaEventDieOwner[ \t]*=[ \t]*BoromirDie[^\r\n]*\r?\n", "", t, count=1, flags=re.M)
    t = re.sub(r"INITIAL[ \t]+BoromirVoiceDie", "INITIAL HeroWestMaleVoiceDie", t, count=1)
    t = set_field(t, "DeathFX", "FX_HeroDieToRespawn")
    t = set_field(t, "InitialSpawnFX", "FX_HeroInitialSpawn")
    t = set_field(t, "RespawnFX", "FX_HeroRespawn")
    t = re.sub(r"^([ \t]*ButtonImage[ \t]*=[ \t]*)HIBorimir\b", r"\g<1>%s_res" % BUTTON, t, count=1, flags=re.M)
    if re.search(r"BoromirVoice|HIBorimir|HwaldarAxe", "\n".join(re.split(r";", l)[0] for l in t.splitlines())):
        raise SystemExit("heroes: Boromir's or Hwaldar's data is left in Gamling")
    from .powers import modules_text
    extra = "".join(m.text("SKH_Gamling_X%d" % k) for k, m in enumerate(EXTRA, 1))
    extra += '\t#include "..\\..\\..\\includes\\CaptureBuilding.inc"\t; sagekit heroes\r\n'
    mods = (extra + modules_text("Gamling", POWERS)).replace("\r\n", "\n").replace("\n", "\r\n")
    end = t.rstrip().rfind("\nEnd")
    t = t[:end + 1] + mods + "\r\n" + t[end + 1:]
    return src[:s] + t + src[e:]
