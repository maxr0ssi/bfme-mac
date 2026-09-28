"""Installed Elven troop visuals; offline checks: python3 -m assets.elves.troops.catalog."""
import re
from assets.dwarves.troops.catalog import state, texture_swaps, variant

UNIT_DIR = 'data\\ini\\object\\goodfaction\\units\\elven\\'
ENT_INI = 'data\\ini\\object\\goodfaction\\units\\ents\\entsinfantry.ini'
ENT_ANIMS = 'data\\ini\\object\\goodfaction\\units\\ents\\genericentanims.inc'
MITH_ANIMS = 'data\\ini\\object\\mithlondsentrymordoreasterlinganims.inc'
INI_MEMBERS = [UNIT_DIR + n + '.ini' for n in (
    'elvenlorienwarrior', 'elvenlorienarcher', 'elvenmithlondsentry', 'elvenmirkwoodarcher',
    'elvenrivendelllancer', 'elvenrivendellarcher', 'noldorwarrior', 'elvenbanner',
    'elvenmirkwoodarcherbanner', 'elvenrivendelllancerbanner', 'gwaihir')] + [ENT_INI]
EXTRA_TEXTURES = ['eumirkarchha.tga', 'gugwaihir_white.tga']
SOURCE_MEMBERS = INI_MEMBERS + [ENT_ANIMS, MITH_ANIMS, 'data\\scripts\\scripts.lua',
    'data\\scripts\\scriptevents.xml', 'data\\ini\\object\\goodfaction\\hordes\\elven\\elvenhordes.ini',
    'data\\ini\\commandset.ini', 'data\\ini\\commandbutton.ini']


def entry(key, title, model, skeleton, prefix, clips, source, hidden=(), **kwargs):
    return dict(key=key, title=title, model=model, skeleton=skeleton,
                animations={pose: prefix + '_' + clip for pose, clip in clips.items()},
                source=source if '\\' in source else UNIT_DIR + source + '.ini', hidden=list(hidden),
                variants=[variant('base', 'Base')],
                conditions=dict(idle='IDLE', move='MOVING', attack='FIRING_OR_PREATTACK_A',
                                death='DYING', preattack='PREATTACK_A'), **kwargs)


def equipment(armor, weapon='forged'):
    sub = 'FORGED_BLADE' if weapon == 'forged' else 'FIREAROWTIP'
    title = 'Forged blades' if weapon == 'forged' else 'Silverthorn arrows'
    return [variant('base', 'Base'),
            dict(key=weapon, title=title, show=[sub], hide=[], textures={}),
            dict(key='armor', title='Heavy armor', show=[], hide=[], textures=armor,
                 exclude_subobjects=['FORGED_BLADE']),
            dict(key=weapon + '_armor', title=title + ' + heavy armor', show=[sub], hide=[],
                 textures=armor, exclude_subobjects=['FORGED_BLADE'])]


ROSTER = [
    entry('lorien_warrior', 'Lórien Warrior', 'eulorwar_skn', 'eulorwar_skl', 'eulorwar',
          dict(idle='idlb', move='runa', attack='atka', death='diea'), 'elvenlorienwarrior',
          ('FORGED_BLADE', 'FIREAROWTIP', 'ARROW', 'ARROWNOCK'), creation='RohanElvenWarriorFunctions'),
    entry('lorien_archer', 'Lórien Archer', 'eulorarch_skn', 'ruelfwar_skl', 'ruelfwar',
          dict(idle='idld', move='runb', attack='atka2', preattack='atka1', death='dieb'),
          'elvenlorienarcher', ('FORGED_BLADE', 'FIREAROWTIP', 'ARROW'),
          creation='RohanElvenWarriorFunctions'),
    entry('mithlond_sentry', 'Mithlond Sentry', 'eumthlnd_skn', 'eumthlnd_skl', 'eumthlnd',
          dict(idle='idlb', move='runa', attack='atka', death='diea', formation='pltb'),
          'elvenmithlondsentry', ('FORGED_BLADE', 'GLOW'), creation='IsengardFighterFunctions'),
    entry('mithlond_sentry_b', 'Mithlond Sentry — alternate', 'eumthlnd_sknb', 'eumthlnd_skl', 'eumthlnd',
          dict(idle='idlb', move='runa', attack='atka', death='diea', formation='pltb'),
          'elvenmithlondsentry', ('FORGED_BLADE', 'GLOW'), condition='USER_4',
          creation='IsengardFighterFunctions'),
    entry('mirkwood_archer', 'Mirkwood Archer', 'eumirkarch_skn', 'guarcher_skl', 'guarcher',
          dict(idle='idla', move='runa', attack='atkf2', preattack='atkf1', death='dieb'),
          'elvenmirkwoodarcher', ('FIREAROWTIP',), creation='RohanArcherFunctions'),
    entry('rivendell_lancer', 'Rivendell Lancer', 'eurivenlan_skn', 'rurohrm_skl', 'rurohrm',
          dict(idle='idlb', move='runa', attack='atka', death='diea'), 'elvenrivendelllancer',
          ('FORGED_BLADE', 'SHIELD', 'FIREAROWTIP'), creation='RohirrimFunctions'),
    entry('rivendell_archer', 'Lindon Horse Archer', 'eurivenarch_skn', 'rurhrmarch_skl', 'rurhrmarch',
          dict(idle='idlb', move='runa', attack='atkb', death='diea'), 'elvenrivendellarcher',
          ('FORGED_BLADE', 'SHIELD', 'FIREAROWTIP'), creation='RohirrimFunctions'),
    entry('noldor', 'Noldor Warrior', 'rulaelfwar_skn', 'ruelfwar_skl', 'ruelfwar',
          dict(idle='idld', move='runb', attack='atka2', preattack='atka1', death='dieb',
               sword_idle='idlg', sword_move='runs', sword_attack='atks'), 'noldorwarrior',
          creation='GenericArcherMemberFunctions',
          pose_overrides={p: {'hide': ['ARROW', 'ARROWNOCK']} for p in
                          ('sword_idle', 'sword_move', 'sword_attack')}),
]
BY_KEY = {e['key']: e for e in ROSTER}
BY_KEY['lorien_warrior']['variants'] = equipment({'eulorienwarrior.tga': 'eulorwarha.tga'})
BY_KEY['lorien_archer']['variants'] = equipment({'eulorarch.tga': 'eulorarch_ha.tga'}, 'silverthorn')
for v in BY_KEY['lorien_archer']['variants']:
    v.pop('exclude_subobjects', None)
for key in ('mithlond_sentry', 'mithlond_sentry_b'):
    BY_KEY[key]['variants'] = equipment({'eumthlnd.tga': 'eumthlnd_ha.tga',
        'eumthlnd_c.tga': 'eumthlnd_ha.tga', 'eumthlndb_c.tga': 'eumthlndb_ha.tga'})
    BY_KEY[key]['conditions']['formation'] = 'ALTERNATE_FORMATION PORCUPINE'
# Mirkwood's heavy-armour visual handler exists, but its recruitable horde cannot purchase it.
BY_KEY['mirkwood_archer']['variants'].append(dict(key='silverthorn', title='Silverthorn arrows',
    show=['FIREAROWTIP', 'ARROWNOCK'], hide=['ARROW'], textures={}))
BY_KEY['rivendell_lancer']['variants'] = equipment({'eurivenlan01.tga': 'eurivenlan01ha.tga',
    'eurivenlan_c.tga': 'eurivenlan01ha.tga', 'elderhorse.tga': 'elderhorse_ha.tga'})
BY_KEY['rivendell_archer']['variants'] = equipment({'eurivenlan_c.tga': 'eurivenlan01ha.tga',
    'euhorse.tga': 'euhorse_ha.tga'}, 'silverthorn')
for v in BY_KEY['rivendell_archer']['variants']:
    if 'armor' in v['key']:
        v['show'].append('SHIELD')
for key in ('lorien_warrior', 'lorien_archer', 'rivendell_lancer'):
    BY_KEY[key]['conditions']['death'] = 'DYING DEATH_1'
for key in ('lorien_archer', 'mirkwood_archer', 'noldor'):
    BY_KEY[key]['conditions']['attack'] = 'FIRING_OR_RELOADING_A'
BY_KEY['noldor']['conditions'].update(sword_idle='WEAPONSET_TOGGLE_1',
    sword_move='MOVING WEAPONSET_TOGGLE_1', sword_attack='FIRING_OR_PREATTACK_A WEAPONSET_TOGGLE_1')

for key, title, model, source, condition in [
    ('warrior_banner', 'Lórien Warrior banner', 'eulorbnr_skn', 'elvenbanner', 'USER_6'),
    ('archer_banner', 'Lórien Archer banner', 'euarchbnr_skn', 'elvenbanner', 'USER_4'),
    ('sentry_banner', 'Mithlond Sentry banner', 'eumthbnr_skn', 'elvenbanner', 'USER_5'),
    ('mirkwood_banner', 'Mirkwood Archer banner', 'eumirkbnr_skn', 'elvenmirkwoodarcherbanner', ''),
    ('lancer_banner', 'Rivendell/Lindon cavalry banner', 'eurvnbnr_skn', 'elvenrivendelllancerbanner', ''),
]:
    prefix = 'rurrmbnr' if key == 'lancer_banner' else 'gubanner'
    ROSTER.append(entry(key, title, model, prefix + '_skl', prefix,
        dict(idle='idlb', move='runa', attack='atka', death='diea'), source, ('GLOW',),
        condition=condition, creation='CavalryFunctions' if key == 'lancer_banner' else 'InfantryBannerFunctions'))

for species in ('fir', 'birch', 'oak', 'ash'):
    prefix = 'ruentash' if species == 'ash' else 'rutreeberd'
    e = entry('ent_' + species, 'Ent — ' + ('Ash melee' if species == 'ash' else species.title()),
        'ruent' + species + '_skn', prefix + '_skl', prefix,
        dict(idle='idla', move='wlka' if species == 'ash' else 'wlkc', attack='atka', death='diea',
             build='mota' if species == 'ash' else 'motc'), ENT_INI, ('ROCK',), creation='EntFunctions')
    e['variants'].append(dict(key='burnt', title='Burnt damage state', show=[], hide=[], textures={},
        model='ruent' + species + 'd_skn'))
    e['conditions']['build'] = 'JUST_BUILT'
    if species != 'ash':
        e['animations'].update(throw=prefix + '_thrb', ranged_idle=prefix + '_idlb', ranged_move=prefix + '_wlke')
        e['conditions'].update(throw='FIRING_OR_PREATTACK_A WEAPONSET_TOGGLE_1',
            ranged_idle='WEAPONSET_TOGGLE_1', ranged_move='MOVING WEAPONSET_TOGGLE_1')
        e['pose_overrides'] = {p: {'show': ['ROCK']} for p in ('throw', 'ranged_idle', 'ranged_move')}
    ROSTER.append(e)
ROSTER.append(entry('eagle', 'Fortress Eagle', 'gugwaihir_skn', 'gugwaihir_skl', 'gugwaihir',
    dict(idle='hvra', move='flya', attack='atkb', death='diee', dive='diva'), 'gwaihir',
    object='ElvenFortressEagle'))
ROSTER[-1]['conditions'].update(attack='ABOUT_TO_HIT', death='DYING DEATH_1', dive='DIVING')
BY_KEY = {e['key']: e for e in ROSTER}
BY_KEY['mirkwood_banner']['creation'] = 'GondorFighterFunctions'
BY_KEY['mirkwood_banner']['hidden'] = ['FORGED_BLADE', 'HAMMER1', 'GLOW', 'GLOW1']
BY_KEY['mirkwood_banner']['variants'].append(dict(key='ce', title='CE banner glow',
    show=['GLOW'], hide=[], textures={}))
MODELS = sorted({e['model'] for e in ROSTER} | {v['model'] for e in ROSTER for v in e['variants'] if 'model' in v})
LOD_MODELS = {name: [name + suffix for suffix in suffixes] for name, suffixes in {
    'eulorwar_skn': 'ml', 'eulorarch_skn': 'ml', 'eumthlnd_skn': 'ml', 'eumirkarch_skn': 'ml',
    'eurivenlan_skn': 'ml', 'rulaelfwar_skn': 'l', 'euarchbnr_skn': 'ml', 'eumthbnr_skn': 'ml',
    'eulorbnr_skn': 'ml', 'eumirkbnr_skn': 'ml', 'eurvnbnr_skn': 'ml',
    'ruentfir_skn': 'ml', 'ruentbirch_skn': 'ml', 'ruentoak_skn': 'm', 'ruentoakd_skn': 'm',
    'ruentash_skn': 'ml', 'gugwaihir_skn': 'ml',
}.items()}
MODELS = sorted(set(MODELS) | {n for names in LOD_MODELS.values() for n in names})
POSTER_KEYS = ('lorien_warrior','lorien_archer','mithlond_sentry','mirkwood_archer',
               'rivendell_lancer','rivendell_archer','noldor','ent_fir','eagle')
WARNINGS = [
    'Mithlond USER_4 alternate is retained; player-side CE setting selection is not simulated.',
    'Mirkwood heavy-armour handler is inherited but unavailable in its recruitable horde command set.',
    'Noldor has inherent forged-blade visuals and bow/sword toggle; no purchasable armour/blade skin.',
    'Rivendell Archer SHIELD request is absent from its installed mesh; never fabricate geometry.',
    'Silverthorn projectile trails/FX are unchanged and need player review outside the body preview.',
    'Generic Ent recruits Fir/Birch/Oak only; unused AshBT and Treebeard hero placeholder are excluded.',
    'Eagle draw is copied only into ElvenFortressEagle; Gwaihir and summoned hero parent remain intact.',
    'Eagle USER_3 white draw is retained privately; fortress CE handler replaces it with USER_4.',
    'Banner default/factory fallback RUYeoBnr is shared and intentionally untouched.',
]


def clean(text):
    return '\n'.join(line.split(';')[0].split('//')[0] for line in text.splitlines())


def animation_inventory(game):
    files, missing = {}, {}
    for member in INI_MEMBERS + [ENT_ANIMS, MITH_ANIMS]:
        for name in re.findall(r'^\s*AnimationName\s*=\s*(\S+)', clean(game.read(member).decode('latin-1')), re.I | re.M):
            name = name.rsplit('.', 1)[-1].lower()
            target = files if game.has_model(name) else missing
            target.setdefault(name, []).append(member)
    return dict(files={k: sorted(set(v)) for k, v in sorted(files.items())},
                missing={k: sorted(set(v)) for k, v in sorted(missing.items())})


def scoped_ini(member, text, replacements):
    """Replace visual fields; Eagle's inherited draw is overridden only in the troop child."""
    def replace(block):
        return re.sub(r'(?im)^\s*(?:Model\s*=|Texture\s*=|UpgradeTexture\s*=|RandomTexture\s*=)[^\r\n]*',
            lambda line: re.sub(r'[\w.]+', lambda m: replacements.get(m[0].lower(), m[0]), line[0]), block)
    if member == ENT_INI:
        blocks = re.split(r'(?m)(?=^(?:Object|ChildObject)\s+)', text)
        base = next(b for b in blocks if b.startswith('Object RohanEntBase'))
        draw = re.search(r'(?ms)^\tDraw\s*=\s*W3DScriptedModelDraw[^\r\n]*.*?^\tEnd[ \t]*\r?$', base)
        assert draw, 'Ent base draw boundary changed'
        for i, block in enumerate(blocks):
            header = re.match(r'(?:Object|ChildObject)\s+(\w+)[^\r\n]*', block)
            if not header:
                continue
            if header[1] == 'RohanEntFir':
                blocks[i] = block[:header.end()] + '\n' + replace(draw[0]) + '\n' + block[header.end():]
            elif header[1] in ('RohanEntBirch', 'RohanEntOak', 'RohanEntAshMelee'):
                blocks[i] = replace(block)
        return ''.join(blocks)
    if member != UNIT_DIR + 'gwaihir.ini':
        return replace(text)
    # The original parent draw ends at its first column-one-tab End, before design fields.
    draw = re.search(r'(?ms)^\tDraw\s*=\s*W3DScriptedModelDraw[^\r\n]*.*?^\tEnd\s*$', text)
    assert draw, 'Gwaihir parent draw boundary changed'
    child = re.search(r'(?m)^ChildObject ElvenFortressEagle GondorGwaihir[^\r\n]*', text)
    assert child, 'Fortress Eagle child missing'
    return text[:child.end()] + '\n' + replace(draw[0]) + '\n' + text[child.end():]


def validate(game=None):
    from sagekit.game import Install
    from sagekit.formats.w3d import W3DFile, chunks, _cstr
    from sagekit.formats.w3dpose import Skeleton
    from sagekit.formats.textures import compiled_path
    game = game or Install(pristine=False)
    for member in SOURCE_MEMBERS:
        assert game.owner(member), member
    assert len(BY_KEY) == len(ROSTER)
    for model in MODELS:
        assert game.has_model(model), model
    for e in ROSTER:
        source = clean(game.read(e['source']).decode('latin-1')).lower()
        if e['key'].startswith('mithlond'):
            source += '\n' + clean(game.read(MITH_ANIMS).decode('latin-1')).lower()
        if e['key'].startswith('ent_') and e['key'] != 'ent_ash':
            source += '\n' + clean(game.read(ENT_ANIMS).decode('latin-1')).lower()
        blocks = re.split(r'^\s*(?:animationstate\s*=?\s*([^\n]*)|idleanimationstate\s*([^\n]*))$', source, flags=re.M)
        routes = {}
        for i in range(1, len(blocks), 3):
            condition = ' '.join(blocks[i].upper().split()) if blocks[i] is not None else 'IDLE'
            routes.setdefault(condition, []).extend(re.findall(r'animationname\s*=\s*(\S+)', blocks[i+2]))
        for v in e['variants']:
            for pose in e['animations']:
                s = state(e, v['key'], pose)
                assert any(a.rsplit('.', 1)[-1] == s['animation'] for a in routes.get(s['condition'], [])), (e['key'], pose, s['condition'], s['animation'])
                model = W3DFile(game.read(game.model_path(s['model'])))
                skel = Skeleton(game.read(game.model_path(s['skeleton'])))
                assert model.skeleton().lower() == s['skeleton'] + '.w3d', (s['model'], s['skeleton'])
                data = game.read(game.model_path(s['animation']))
                headers = [data[p+8:p+8+n] for t, off, size, _ in chunks(data, 0, len(data))
                           if t in (0x200, 0x280) for tag, p, n, _ in chunks(data, off+8, off+8+size)
                           if tag in (0x201, 0x281)]
                assert headers and _cstr(headers[0][20:36]).upper() == skel.name.upper(), (e['key'], pose)
                for texture in s.get('textures', {}).values():
                    assert any(game.owner(compiled_path(texture, ext)) for ext in ('.dds', '.tga')), texture
    ent_source = game.read(ENT_INI).decode('latin-1')
    ent_result = scoped_ini(ENT_INI, ent_source, {'ruentfir_skn': 'test_fir', 'ruentbirch_skn': 'test_birch'})
    original_blocks = re.split(r'(?m)(?=^(?:Object|ChildObject)\s+)', ent_source)
    changed_blocks = re.split(r'(?m)(?=^(?:Object|ChildObject)\s+)', ent_result)
    for original, result in zip(original_blocks, changed_blocks):
        header = re.match(r'(?:Object|ChildObject)\s+(\w+)', original)
        if not header or header[1] not in ('RohanEntFir', 'RohanEntBirch', 'RohanEntOak', 'RohanEntAshMelee'):
            assert original == result, header[1] if header else 'preamble'
    original = game.read(UNIT_DIR + 'gwaihir.ini').decode('latin-1')
    patched = scoped_ini(UNIT_DIR + 'gwaihir.ini', original, {'gugwaihir_skn': 'test_eagle'})
    child = 'ChildObject ElvenFortressEagle GondorGwaihir'
    assert patched.split(child)[0] == original.split(child)[0]
    assert 'test_eagle' in patched.split(child)[1]
    assert 'ARROWNOCK' in state(BY_KEY['noldor'], pose='sword_attack')['hidden']
    print('Elven catalog source, routes, animation hierarchies, upgrades and Eagle isolation passed.')
    for warning in WARNINGS:
        print('NOTE:', warning)


if __name__ == '__main__':
    validate()
