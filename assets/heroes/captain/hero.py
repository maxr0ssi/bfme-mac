"""The Captain of Erebor: a new Dwarven hero on King Dain's rig, his object written from Dain's at
build time (the player's own 2.02 files; no EA text in git).

Dain's body, animations and Draw states; our model (SKEreborCpt_SKN: Dain with the Erebor kit);
the Create-a-Hero dwarf's voice (a captain, not the king); Gloin's tier (cost, weapon, bounty, auto-
resolve); and powers recombined from EA's modules:

  L1  Leadership           Dain's aura (GenericHeroLeadership), kept as Dain has it
  L3  Charge               the Create-a-Hero dwarf's charge (+100% armour, +50% damage, crushes)
  L5  Toughness            the Create-a-Hero dwarf's passive health bonus
  L7  Train Allies         the Create-a-Hero level grant (XP to troops)
  L10 Summon Royal Guard   Dain's summon on our own copy of its power (no Dain voice line)

Balance: 1500 (Gloin 1600, Captain of Dale 1200, Dain 2000), 2700 health (Gloin and Dain 3000),
Gloin's axe and command points; Dain's summon only at level 10 (Dain: level 8).
"""
import re

from .. import ea
from ..powers import GENERIC_HERO_COMMANDS, Module, Power
from ..text import module_span, object_span, set_field

NAME, DONOR = "DwarvenEreborCaptain", "DwarvenDain"
MODEL, DONOR_MODEL = "SKEreborCpt_SKN", "DUDain_SKN"
COMMAND_SET = "SagekitEreborCaptainCommandSet"
COST, HEALTH = 1500, 2700
PORTRAIT, BUTTON = "HPEreborCaptain", "HIEreborCaptain"
CAH_POWERS = "data\\ini\\object\\createahero\\createaheropowers.inc"
VOICE = {"VoiceAttack": "HeroDwarfVoiceAttack", "VoiceAttackCharge": "HeroDwarfVoiceAttack",
         "VoiceAttackMachine": "HeroDwarfVoiceAttack", "VoiceAttackStructure": "HeroDwarfVoiceAttack",
         "VoiceFear": "HeroDwarfVoiceHelpMe", "VoiceGuard": "HeroDwarfVoiceMove", "VoiceMove": "HeroDwarfVoiceMove",
         "VoiceMoveToCamp": "HeroDwarfVoiceMove", "VoiceMoveWhileAttacking": "HeroDwarfVoiceMove",
         "VoiceRetreatToCastle": "HeroDwarfVoiceMove", "VoiceSelect": "HeroDwarfVoiceSelectMS",
         "VoiceSelectBattle": "HeroDwarfVoiceSelectBattle", "VoiceGarrison": "HeroDwarfVoiceMove",
         "VoiceEnterUnitElvenTransportShip": "HeroDwarfVoiceMove", "VoiceInitiateCaptureBuilding": "HeroDwarfVoiceCaptureBuilding"}
# Dain's own modules the Captain does not carry (his Stubborn Pride, Mighty Rage, Royal Guard at 8,
# their AI, and the emotion loops in Dain's voice); his leadership modules stay as Dain has them
DROP = ["ModuleTag_foo", "ModuleTag_StubbornPrideUnpause", "ModuleTag_StubbornPrideSpecialPower", "ModuleTag_StubbornPrideUpdate",
        "ModuleTag_MightyRageStarter", "ModuleTag_DainMightyRageDummy", "ModuleTag_CloseTheGap", "ModuleTag_MightyRageBuff",
        "ModuleTag_MightyRageDebuff", "ModuleTag_StarlightAutoAbilityBehavior", "ModuleTag_DainSummonEnabler",
        "ModuleTag_OCLSpecialPower", "ModuleTag_AotDAutoAbility", "RoyalGuardAI", "MightyRageAI"]

S = "CONTROLBAR:SagekitEreborCaptain"
POWERS = [
    Power(2, 1, "Command_SpecialAbilityDainLeadership", "Command_SKH_EreborCptLeadership", [],
          (S + "LeadershipTip", "Modifier Type: Leadership \\n Allies near the Captain of Erebor gain +25% Damage, +25% Armor, "
                                "and earn Experience 50% faster \\n Stacks with Buffs and Spells \\n Radius: 200 \\n Passive ability"),
          unpause=False),
    Power(3, 3, "Command_CreateAHero_Charge_Level1", "Command_SKH_EreborCptCharge",
          [Module(CAH_POWERS, "ModuleTag_CreateAHeroChargeStarter_Level1"), Module(CAH_POWERS, "ModuleTag_CreateAHeroChargeUpdate_Level1")],
          (S + "ChargeTip", "Requires Level 3 \\n The Captain charges, crushing enemies in his path \\n Gains +100% Armor and +50% "
                            "Damage for 20s \\n Recharge Time: {recharge} \\n Left click to activate"),
          ai="AI_SPECIAL_POWER_CHARGE"),
    Power(4, 5, "Command_CreateAHero_Toughness", "Command_SKH_EreborCptToughness",
          [Module(CAH_POWERS, "ModuleTag_CreateAHeroToughnessStarter"),
           Module(CAH_POWERS, "ModuleTag_DwarfToughness", {"TriggeredBy": "Upgrade_ObjectLevel5", "RequiresAllTriggers": None})],
          (S + "ToughnessTip", "Requires Level 5 \\n Mithril under the coat: the Captain gains a permanent boost to his Health "
                               "\\n Passive ability")),
    Power(5, 7, "Command_CreateAHero_SpecialAbilityCreateAHeroTrainAllies_Level_1", "Command_SKH_EreborCptTrainAllies",
          [Module(CAH_POWERS, "ModuleTag_TrainAlliesSpecialPowerModule_Level_1"), Module(CAH_POWERS, "ModuleTag_TrainAllies_Level_1")],
          (S + "TrainTip", "Requires Level 7 \\n The Captain drills nearby troops: they gain moderate Experience \\n "
                           "Recharge Time: {recharge} \\n Left click icon then left click on target units"),
          ai="AI_SPECIAL_POWER_GIVEXP_AOE", ai_radius=100.0),
    Power(6, 10, "Command_SpecialAbilityDainSummonRoyalGuard", "Command_SKH_EreborCptRoyalGuard",
          [Module("obj:DwarvenDain", "ModuleTag_OCLSpecialPower"), Module("obj:DwarvenDain", "ModuleTag_AotDAutoAbility")],
          (S + "GuardTip", "Requires Level 10 \\n The Captain calls the Royal Guard of Erebor: several battalions of dwarves "
                           "come to his side \\n Duration: 1m 15s \\n Target Range: 200 \\n Recharge Time: {recharge} \\n "
                           "Left click icon then left click on pathable location"),
          ai="AI_SPELLBOOK_ASSIST_BATTLE_BUFF", ai_radius=150.0,
          template_copy=("SpecialAbilityDainSummonRoyalGuard", "SagekitEreborCaptainRoyalGuard",
                         {"InitiateAtLocationSound": None, "ReloadTime": "240000"})),
]
STRINGS = [
    ("OBJECT:SagekitEreborCaptain", "Captain of Erebor"),
    (S + "Recruit", "Recruit a Captain of the Royal Guard of Erebor \\n \\n Unit Type: Tier 2 Hero \\n Recruit Time: 40s \\n "
                    "Health Regeneration: 30/s \\n Levels 2-10: Gloin's health and damage bonuses"),
    (S + "Revive", "Revive the fallen Hero, the Captain of Erebor"),
    (S + "Hotkey", "Captain of &Erebor"),
    ("TOOLTIP:SagekitEreborCaptain", "Damage Type: Hero \\n Melee Attack Speed: 1.03s \\n Movement Speed: 45 \\n Vision Range: 300"),
]


def object_text():
    """Dain's object rewritten as the Captain's (Windows line ends as EA's)."""
    o = ea.objects()[DONOR]
    src = ea.text(o["member"])
    s, e = object_span(src, DONOR)
    t = src[s:e]
    s0, e0 = 0, len(t)
    t = re.sub(r"^Object[ \t]+%s\b" % DONOR, "Object %s\t; sagekit heroes: King Dain's object, rewritten" % NAME, t, count=1, flags=re.M)
    for tag in DROP:
        a, b = module_span(t, tag)
        t = t[:a] + t[b:]
    first = lambda key, value, comment=None: _first(t, key, value, comment)
    t = first("SelectPortrait", PORTRAIT)
    t = re.sub(r"^([ \t]*ButtonImage[ \t]*=[ \t]*)HIKingDain_res\b", r"\g<1>%s_res" % BUTTON, t, count=1, flags=re.M)
    t = re.sub(r"^([ \t]*ButtonImage[ \t]*=[ \t]*)HIKingDain\b", r"\g<1>%s" % BUTTON, t, count=1, flags=re.M)
    t = set_field(t, "Model", MODEL, count=2, comment="Dain with the Erebor kit")
    t = set_field(t, "StaticModelLODMode", "No", comment="our model has no M/L copies")
    t = set_field(t, "BuildCost", str(COST), comment="Gloin 1600, Captain of Dale 1200")
    t = set_field(t, "BuildTime", "HERO_BUILDTIME_TIER_2")
    t = set_field(t, "DisplayMeleeDamage", "GLOIN_DAMAGE")
    t = set_field(t, "Description", "TOOLTIP:SagekitEreborCaptain")
    t = set_field(t, "DescriptionStrategic", "CONTROLBAR:LW_ToolTip_Gloin")
    t = re.sub(r"^([ \t]*Weapon[ \t]*=[ \t]*PRIMARY[ \t]+)DwarvenDainAxe\b", r"\g<1>GloinAxe", t, count=1, flags=re.M)
    t = set_field(t, "BountyValue", "DWARVEN_GLOIN_BOUNTY_VALUE")
    t = set_field(t, "DisplayName", "OBJECT:SagekitEreborCaptain")
    t = set_field(t, "RecruitText", S + "Recruit")
    t = set_field(t, "ReviveText", S + "Revive")
    t = set_field(t, "Hotkey", S + "Hotkey")
    t = set_field(t, "CommandSet", COMMAND_SET)
    t = set_field(t, "CommandPoints", "HERO_COMMAND_POINTS_TIER_2")
    t = re.sub(r"CORRODE_ALLEGIANCE_CP_HACK_TIER_3\.inc", "CORRODE_ALLEGIANCE_CP_HACK_TIER_2.inc", t, count=1)
    t = set_field(t, "AutoResolveBody", "AutoResolve_GloinBody")
    t = re.sub(r"(=[ \t]*)AutoResolve_DainArmor\b", r"\g<1>AutoResolve_GloinArmor", t, count=1)
    t = re.sub(r"(=[ \t]*)AutoResolve_DainWeapon\b", r"\g<1>AutoResolve_GloinWeapon", t, count=1)
    t = _drop_line(t, "AutoResolveLeadership")
    t = _drop_line(t, "EvaEventDieOwner")
    t = re.sub(r"^[ \t]*VoiceEnterState\w+[ \t]*=[^\r\n]*\r?\n", "", t, flags=re.M)
    for key, event in VOICE.items():
        t = set_field(t, key, event)
    t = set_field(t, "MaxHealth", str(HEALTH), comment="Gloin and Dain 3000")
    t = set_field(t, "DeathFX", "FX_HeroDieToRespawn")
    t = set_field(t, "InitialSpawnFX", "FX_HeroInitialSpawn")
    t = set_field(t, "RespawnFX", "FX_HeroRespawn")
    t = re.sub(r"INITIAL[ \t]+DainVoiceDie", "INITIAL HeroDwarfVoiceDie", t, count=1)
    t = t.replace("DAIN_BUILDCOST", str(COST))
    t = re.sub(r"HERO_RESPAWNTIME_TIER_3", "HERO_RESPAWNTIME_TIER_2", t)
    if re.search(r"\bDain\w*Voice|\bDainVoice|EmotionDain", t):
        raise SystemExit("heroes: a Dain voice line is left in the Captain: %s" % re.findall(r"\w*Dain\w*Voice\w*", t)[:3])
    from ..powers import modules_text
    mods = modules_text("EreborCpt", POWERS).replace("\n", "\r\n")
    end = t.rstrip().rfind("\nEnd")
    return t[:end + 1] + mods + "\r\n" + t[end + 1:]


def _first(t, key, value, comment=None):
    return set_field(t, key, value, count=1, comment=comment)


def _drop_line(t, key):
    new, n = re.subn(r"^[ \t]*%s[ \t]*=[^\r\n]*\r?\n" % key, "", t, count=1, flags=re.M)
    if n != 1:
        raise SystemExit("heroes: Dain has no %s line" % key)
    return new


def experience_levels():
    """The Captain's ten levels: Gloin's curve and bonuses (his tier), and every level grants its
    Upgrade_ObjectLevelN (the powers wait for 1, 3, 5, 7 and 10)."""
    from ..levels import copy_levels
    return copy_levels("DwarvenGloin", NAME, grant_all=True)
