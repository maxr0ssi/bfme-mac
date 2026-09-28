"""Explicit installed Dwarven art states; read-only validation: python3 -m assets.dwarves.troops.catalog.

Names are archive asset names without extensions. Texture dictionaries are old -> new.
`pose_overrides` replaces model/skeleton/show/hide for the named animation only.
`passengers` pairs roster keys with wagon attachment bones; never inherit wagon armour.
"""
from copy import deepcopy
import re

UNIT_DIR = 'data\\ini\\object\\goodfaction\\units\\dwarven\\'
INI_MEMBERS = [UNIT_DIR + n + '.ini' for n in (
    'dwarvenguardian', 'dwarvenphalanx', 'dwarvenaxethrower', 'dwarvenmenofdale',
    'dwarvenzerker', 'dwarvenbattlewagon', 'dwarvenram', 'catapult', 'dwarvenbanner',
    'dwarvenbattlewagonaxethrower', 'dwarvenbattlewagonmenofdale', 'dwarvenbattlewagonphalanx')]
SOURCE_MEMBERS = INI_MEMBERS + ['data\\scripts\\scripts.lua', 'data\\scripts\\scriptevents.xml',
    'data\\ini\\object\\goodfaction\\hordes\\dwarven\\dwarvenhordes.ini',
    'data\\ini\\commandset.ini', 'data\\ini\\commandbutton.ini']


def variant(key, title, **kwargs):
    return dict(key=key, title=title, show=[], hide=[], textures={}, **kwargs)


def equipment(armor, weapon='forged', exclude='FORGED_BLADE'):
    """Four legal combinations, with armour texture exclusions kept explicit."""
    return [variant('base', 'Base'),
            dict(key=weapon, title='Forged blades' if weapon == 'forged' else 'Fire arrows',
                 show=[exclude], hide=[], textures={}),
            dict(key='armor', title='Mithril Mail', show=[], hide=[], textures=armor,
                 exclude_subobjects=[exclude]),
            dict(key=weapon + '_armor', title=('Forged blades' if weapon == 'forged' else 'Fire arrows')
                 + ' + Mithril Mail', show=[exclude], hide=[], textures=armor,
                 exclude_subobjects=[exclude])]


def entry(key, title, model, skeleton, prefix, clips, source, hidden=(), **kwargs):
    return dict(key=key, title=title, model=model, skeleton=skeleton,
                animations={pose: prefix + '_' + clip for pose, clip in clips.items()},
                source=UNIT_DIR + source + '.ini', hidden=list(hidden),
                variants=[variant('base', 'Base')], **kwargs)


ROSTER = [
    entry('guardian', 'Guardian', 'eudwarfgua_skn', 'eudwarfgua_skl', 'eudwarfgua',
          dict(idle='idla', move='runa', attack='atka', death='diea', charge='spca'),
          'dwarvenguardian', ('FORGED_BLADE', 'HAMMER1'), creation='DwarvenGuardianFunctions'),
    entry('phalanx', 'Phalanx', 'duphalanx_skn', 'duphalanx_skl', 'duphalanx',
          dict(idle='idla', move='runa', attack='atka', death='diea', formation='pltb'),
          'dwarvenphalanx', ('FORGED_BLADE', 'HAMMER1', 'GLOW', 'GLOW1'),
          creation='GondorFighterFunctions'),
    entry('axe_thrower', 'Axe Thrower', 'eudwarfaxe_skn', 'eudwarfaxe_skl', 'eudwarfaxe',
          dict(idle='idlb', move='runa', attack='atka', death='diea', melee='atkb'),
          'dwarvenaxethrower', ('FORGED_BLADE', 'HAMMER1', 'GLOW', 'GLOW1'),
          creation='AxeThrowerFunctions'),
    entry('men_of_dale', 'Men of Dale', 'ruarcher_skn', 'guarcher_skl', 'guarcher',
          dict(idle='idla', move='runa', attack='atkf2', death='diea', preattack='atkf1', melee='atkd'),
          'dwarvenmenofdale', ('FIREAROWTIP',), creation='RohanArcherFunctions',
          draw_textures={'dumendale.tga': 'ruarcher.tga'}),
    entry('zealot', 'Zealot — halberd source', 'rudwrfhlbd_skn', 'rugimli_skl', 'rugimli',
          dict(idle='idlb', move='runa', attack='atka', death='diea', axe_throw='spca', secondary='atkd'),
          'dwarvenzerker', ('AXE02', 'FORGED_BLADE', 'HAMMER1'), creation='DwarvenGuardianFunctions',
          pose_overrides={'axe_throw': {'show': ['AXE02']}}, extra_mesh=True),
    entry('zealot_hammer', 'Zealot — hammer source', 'rudwrfhmr_skn', 'rugimli_skl', 'rugimli',
          dict(idle='idlb', move='runa', attack='atka', death='diea', axe_throw='spca', secondary='atkd'),
          'dwarvenzerker', ('AXE02', 'FORGED_BLADE', 'HAMMER1'), creation='DwarvenGuardianFunctions',
          pose_overrides={'axe_throw': {'show': ['AXE02']}}, extra_mesh=True),
    entry('battlewagon', 'Battlewagon', 'dubtlwagon_skn', 'dubtlwagon_skl', 'dubtlwagon',
          dict(idle='idla', move='runa', attack='atka', death='diea', build='blda'),
          'dwarvenbattlewagon', ('DWARFHEARTH', 'DWARFHEARTHFIRE', 'BANNER_L', 'GLOW'),
          creation='DwarvenBattleWagonFunctions',
          pose_overrides={'death': {'model': 'dubtlwagon_diea', 'skeleton': 'dubtlwagon_diea',
                                    'passengers': []}}),
    entry('demolisher', 'Demolisher', 'eudwarfram_skn', 'eudwarfram_skl', 'eudwarfram',
          dict(idle='idla', move='wlka', attack='atka', death='dtha', build='blda',
               deploy='upak', pack='pak', deployed='idld', deployed_attack='atkd'), 'dwarvenram',
          pose_overrides={'death': {'model': 'eudwarfram_dtha', 'skeleton': 'eudwarfram_dtha'}}),
    entry('catapult', 'Catapult', 'ducatapult_skn', 'ducatapult_skl', 'ducatapult',
          dict(idle='idla', move='wlka', attack='atka', death='diea', build='blda'), 'catapult',
          pose_overrides={'death': {'model': 'ducatapult_diea', 'skeleton': 'ducatapult_diea'},
                          'build': {'model': 'ducatapult_a', 'skeleton': 'ducatapult_skl'}}),
]
BY_KEY = {e['key']: e for e in ROSTER}
BY_KEY['guardian']['variants'] = equipment({'eudwarfgua.tga': 'eudwarfgua_ha.tga'}) + [
    dict(key='hammer', title='Siege hammer', show=['HAMMER1'], hide=['AXE', 'SHIELD', 'FORGED_BLADE'],
         textures={}),
    dict(key='hammer_armor', title='Siege hammer + Mithril Mail', show=['HAMMER1'],
         hide=['AXE', 'SHIELD', 'FORGED_BLADE'], textures={'eudwarfgua.tga': 'eudwarfgua_ha.tga'},
         exclude_subobjects=['FORGED_BLADE'])]
BY_KEY['phalanx']['variants'] = equipment({'duphalanx_01.tga': 'duphalanx_01_ha.tga'})
BY_KEY['axe_thrower']['variants'] = equipment({'eudwarfaxe.tga': 'eudwarfaxe_ha.tga'})
BY_KEY['men_of_dale']['variants'] = equipment(
    {'ruarcher.tga': 'ruarcherha.tga', 'ruarcher_m.tga': 'ruarcherha.tga'}, 'fire', 'FIREAROWTIP')
# ARMOR is requested by the INI but absent from the active HD model: record, don't invent geometry.
for v in BY_KEY['men_of_dale']['variants']:
    if 'armor' in v['key']:
        v['show'].append('ARMOR')
BY_KEY['demolisher']['variants'].append(dict(key='armor', title='Mithril Mail', show=[], hide=[],
    textures={'eudwarfram.tga': 'eudwarfram_upgrade.tga', 'eudwarfram_shield.tga': 'eudwarfram_shield_ha.tga'}))
BY_KEY['catapult']['variants'].append(dict(key='fire', title='Flaming Shot', show=[], hide=[], textures={},
    weapon='DwarvenIronHillsCatapultFlamingShot', note='Projectile/FX upgrade; body unchanged.'))

for key, title, model, state in [('guardian_banner', 'Guardian banner', 'duguaban_skn', 'USER_4'),
                                ('phalanx_banner', 'Phalanx banner', 'duphaban_skn', 'USER_6'),
                                ('axe_banner', 'Axe Thrower banner', 'duaxdban_skn', 'USER_5'),
                                ('dale_banner', 'Men of Dale banner', 'ruyeobnr_skn', 'USER_3')]:
    prefix = 'gubanner' if key == 'dale_banner' else 'duaxdban'
    ROSTER.append(entry(key, title, model, prefix + '_skl', prefix,
        dict(idle='idlb', move='runa', attack='atka', death='diea'), 'dwarvenbanner',
        ('FORGED_BLADE', 'HAMMER1', 'GLOW', 'GLOW1'), condition=state, creation='GondorFighterFunctions'))

ROSTER += [
    entry('wagon_axe', 'Battlewagon Axe Thrower', 'eudwarfaxe_skn', 'eudwarfaxe_skl', 'eudwarfaxe',
          dict(idle='bidl', move='bidl', attack='batk', death='diea'), 'dwarvenbattlewagonaxethrower',
          creation='InfantryFunctions', passenger=True),
    entry('wagon_dale', 'Battlewagon Man of Dale', 'ruarcher_skn', 'guarcher_skl', 'guarcher',
          dict(idle='idla', move='idla', attack='atkf2', death='dieb', preattack='atkf1'),
          'dwarvenbattlewagonmenofdale', ('FIREAROWTIP',), creation='RohanArcherFunctions', passenger=True,
          draw_textures={'dumendale.tga': 'ruarcher.tga'}),
]
for side in ('a', 'b'):
    ROSTER.append(entry('wagon_phalanx_' + side, 'Battlewagon Phalanx ' + side.upper(),
        'duphalanx' + side + '_skn', 'duphalanx' + side + '_skl', 'duphalanx' + side,
        dict(idle='idla', move='runa', attack='atka'), 'dwarvenbattlewagonphalanx',
        ('FORGED_BLADE', 'HAMMER1', 'GLOW', 'GLOW1'), creation='GondorFighterFunctions', passenger=True,
        condition='PASSENGER_VARIATION_' + ('1' if side == 'a' else '2'),
        note='Authored ground death clip has incompatible hierarchy; killed with wagon, not ejected.'))
BY_KEY = {e['key']: e for e in ROSTER}
for key, title, show, passengers in [
    ('hearth', 'Hearth', ['DWARFHEARTH', 'DWARFHEARTHFIRE'], []),
    ('banner', 'Banner + Phalanx crew', ['BANNER_L'], [('wagon_phalanx_a', 'PASS01'), ('wagon_phalanx_b', 'PASS02')]),
    ('axes', 'Axe Thrower crew', [], [('wagon_axe', 'PASS01'), ('wagon_axe', 'PASS02')]),
    ('dale', 'Men of Dale crew', [], [('wagon_dale', 'PASS01'), ('wagon_dale', 'PASS02')]),
]:
    for armored in (False, True):
        BY_KEY['battlewagon']['variants'].append(dict(key=key + ('_armor' if armored else ''),
            title=title + (' + Mithril Mail' if armored else ''), show=show, hide=[],
            textures={'dubtlwagon.tga': 'dubtlwagon_ha.tga'} if armored else {}, passengers=passengers))

# Conditions are explicit: this is a representative authored route, not a filename guess.
for e in ROSTER:
    e['conditions'] = dict(idle='IDLE', move='MOVING', attack='FIRING_OR_PREATTACK_A', death='DYING',
                          build='JUST_BUILT')
    if e['key'] == 'dale_banner':
        e['conditions'].update(idle='USER_3', move='MOVING USER_3',
                               attack='FIRING_OR_PREATTACK_A USER_3', death='DYING USER_3')
    if e['key'] in ('men_of_dale', 'wagon_dale'):
        e['conditions'].update(attack='FIRING_OR_RELOADING_A', preattack='PREATTACK_A',
                               melee='FIRING_OR_PREATTACK_A WEAPONSTATE_CLOSE_RANGE')
    if e['key'] in ('wagon_dale', 'wagon_axe'):
        e['conditions']['move'] = 'IDLE'  # no ground running state while contained
    if e['key'].startswith('wagon_phalanx_'):
        e['conditions'].update(idle=e['condition'], move='TRANSPORT_MOVING ' + e['condition'],
                               attack='ATTACKING ' + e['condition'])
    if e['key'].startswith('zealot'):
        e['conditions'].update(axe_throw='FIRING_OR_PREATTACK_C', secondary='FIRING_OR_PREATTACK_B')
BY_KEY['guardian']['conditions']['charge'] = 'MOVING USER_1'
BY_KEY['phalanx']['conditions']['formation'] = 'ALTERNATE_FORMATION PORCUPINE'
BY_KEY['axe_thrower']['conditions']['melee'] = 'FIRING_OR_PREATTACK_A WEAPONSTATE_CLOSE_RANGE'
BY_KEY['demolisher']['conditions'].update(deploy='UNPACKING', pack='PACKING', deployed='DEPLOYED',
                                          deployed_attack='DEPLOYED FIRING_OR_PREATTACK_A')
# SiegeHammer is the Guardian PLAYER_UPGRADE weaponset; its idle route changes, attack remains A.
for v in BY_KEY['guardian']['variants']:
    if v['key'].startswith('hammer'):
        v['animations'] = {'idle': 'eudwarfgua_idlb'}
        v['conditions'] = {'idle': 'WEAPONSET_PLAYER_UPGRADE'}
for v in BY_KEY['phalanx']['variants']:
    if v['key'].startswith('forged'):
        v['animations'] = {'idle': 'duphalanx_idlb'}
        v['conditions'] = {'idle': 'WEAPONSET_PLAYER_UPGRADE'}

# Inherited/Summoned objects remain in these same targeted Dwarven INIs. Never globally replace
# shared RUArcher/banner/Gimli assets: own-copy models and edit only these INI references.
MODELS = sorted({e['model'] for e in ROSTER} | {
    o['model'] for e in ROSTER for o in e.get('pose_overrides', {}).values() if 'model' in o})
# StaticModelLODMode appends these suffixes. These are existing archive models, not fabricated
# copies; their HD/original geometry differs and each must retain its own texture dependencies.
LOD_MODELS = {name: [name + suffix for suffix in suffixes] for name, suffixes in {
    'duaxdban_skn': 'ml', 'dubtlwagon_skn': 'ml', 'ducatapult_skn': 'ml',
    'duguaban_skn': 'l', 'duphaban_skn': 'ml', 'duphalanx_skn': 'ml',
    'duphalanxa_skn': 'm', 'duphalanxb_skn': 'm', 'eudwarfaxe_skn': 'ml',
    'eudwarfgua_skn': 'ml', 'eudwarfram_skn': 'ml', 'ruarcher_skn': 'ml', 'ruyeobnr_skn': 'ml',
}.items()}
MODELS = sorted(set(MODELS) | {name for names in LOD_MODELS.values() for name in names})
WARNINGS = [
    'Zealot ExtraMesh runtime selection is unverified; review the two complete sources separately.',
    'Zealot RandomTexture targets Dwarf_A.tga, absent from the active HD meshes.',
    'Men of Dale ARMOR and banner/wagon GLOW requests are absent from active HD meshes.',
    'Passenger Phalanx A/B lack Forged_Blade and have no matching authored death animation.',
    'Wagon armour does not propagate to passenger visuals; passenger Axe keeps its forged mesh.',
    'Catapult Flaming Shot and ranged projectiles require separate FX review; body has no fire skin.',
    'Men of Dale draw swap DUMenDale.tga -> RUArcher.tga is a no-op on active HD RUArcher sheets.',
]


def state(entry, upgrade='base', pose='idle'):
    """Resolve a representative state, including creation hides and per-pose model changes."""
    e = deepcopy(entry)
    v = next(v for v in e['variants'] if v['key'] == upgrade)
    o = {**v, **e.get('pose_overrides', {}).get(pose, {})}
    e.update({k: value for k, value in o.items() if k not in ('key', 'title', 'show', 'hide')})
    e['hidden'] = sorted((set(e['hidden']) | set(v.get('hide', [])) | set(o.get('hide', [])))
                         - set(v.get('show', [])) - set(o.get('show', [])))
    e['animation'] = v.get('animations', {}).get(pose, entry['animations'][pose])
    e['condition'] = v.get('conditions', {}).get(pose, entry['conditions'][pose])
    return e


def texture_swaps(entry, mesh_name):
    """Apply draw then upgrade swaps; excluded meshes retain their draw-level textures."""
    swaps = dict(entry.get('draw_textures', {}))
    if mesh_name.upper() not in {s.upper() for s in entry.get('exclude_subobjects', [])}:
        swaps.update(entry.get('textures', {}))
    return swaps


def animation_inventory(game):
    """All uncommented animation references, including authored missing/mismatched legacy states.

    Return actual files separately from missing names; don't invent replacement motion.
    Catapult auxiliary fortress/wall draws in its source INI are included for provenance.
    """
    files, missing = {}, {}
    for member in INI_MEMBERS:
        text = '\n'.join(line.split(';')[0].split('//')[0]
                         for line in game.read(member).decode('latin-1').splitlines())
        for name in re.findall(r'^\s*AnimationName\s*=\s*(\S+)', text, re.I | re.M):
            name = name.rsplit('.', 1)[-1].lower()
            target = files if game.has_model(name) else missing
            target.setdefault(name, []).append(member)
    return dict(files={k: sorted(set(v)) for k, v in sorted(files.items())},
                missing={k: sorted(set(v)) for k, v in sorted(missing.items())})


def validate(game=None):
    """Check actual source models, animation headers, hierarchy names and upgrade sheets."""
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
        source = '\n'.join(line.split(';')[0].split('//')[0]
                           for line in game.read(e['source']).decode('latin-1').splitlines()).lower()
        blocks = re.split(r'^\s*(?:animationstate\s*=?\s*([^\n]*)|idleanimationstate\s*([^\n]*))$',
                          source, flags=re.M)
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
                if model.skeleton():
                    assert model.skeleton().lower() == s['skeleton'] + '.w3d', (s['model'], s['skeleton'])
                data = game.read(game.model_path(s['animation']))
                headers = [data[p+8:p+8+n] for t, off, size, _ in chunks(data, 0, len(data))
                           if t in (0x200, 0x280) for tag, p, n, _ in chunks(data, off+8, off+8+size)
                           if tag in (0x201, 0x281)]
                assert headers and _cstr(headers[0][20:36]).upper() == skel.name.upper(), (e['key'], pose)
                for texture in s.get('textures', {}).values():
                    assert any(game.owner(compiled_path(texture, ext)) for ext in ('.dds', '.tga')), texture
    # Resolving a hammer must never reveal axe/shield; fire armour must preserve flame texture.
    assert {'AXE', 'SHIELD', 'FORGED_BLADE'} <= set(state(BY_KEY['guardian'], 'hammer_armor')['hidden'])
    assert texture_swaps(state(BY_KEY['men_of_dale'], 'fire_armor'), 'FIREAROWTIP') == {'dumendale.tga': 'ruarcher.tga'}
    print('Catalog source, model, animation hierarchy and texture checks passed.')
    for warning in WARNINGS:
        print('NOTE:', warning)


if __name__ == '__main__':
    validate()
