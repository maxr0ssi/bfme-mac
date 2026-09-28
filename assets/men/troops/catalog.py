"""Live Men of the West troop visuals; offline check: python3 -m assets.men.troops.catalog."""
from copy import deepcopy
import re
from assets.dwarves.troops.catalog import state, texture_swaps, variant
from assets.elves.troops.catalog import clean, equipment

UNIT_DIR = 'data\\ini\\object\\goodfaction\\units\\men\\'
RANGER_ANIMS = UNIT_DIR + 'gondorrangeranims.inc'
INI_MEMBERS = [UNIT_DIR + n + '.ini' for n in (
    'gondorfighter', 'rohanspearmen', 'gondortowershieldguard', 'gondorarcher',
    'gondorranger', 'gondorcavalry', 'rohanrohirrim', 'knightsofdolamroth', 'trebuchet',
    'gondorinfantrybanner', 'gondorcavalrybanner', 'rohanbanner')]
SOURCE_MEMBERS = INI_MEMBERS + [RANGER_ANIMS, 'data\\scripts\\scripts.lua',
    'data\\scripts\\scriptevents.xml', 'data\\ini\\commandset.ini', 'data\\ini\\commandbutton.ini',
    'data\\ini\\object\\goodfaction\\hordes\\men\\menhordes.ini']
SHARED_HOUSE_TEXTURES = {'hc_gubanner.tga'}
SOURCE_MEMBERS += ['art\\compiledtextures\\hc\\hc_gubanner.jpg',
                   'art\\compiledtextures\\hc\\hc_gubanner.png']
EXTRA_TEXTURES = ['cuhorse_bna.tga', 'cuhorse_wtbka.tga', 'ruyeobannerb.tga'] + [
    stem + str(i).zfill(2) + suffix + '.tga' for stem in ('rurohrm', 'ruhorse')
    for i in range(1, 5) for suffix in ('', 'ha')]


def entry(key, title, model, skeleton, prefix, clips, source, hidden=(), **kwargs):
    return dict(key=key, title=title, model=model, skeleton=skeleton,
        animations={p: prefix + '_' + c for p, c in clips.items()}, source=UNIT_DIR + source + '.ini',
        hidden=list(hidden), variants=[variant('base', 'Base')],
        conditions=dict(idle='IDLE', move='MOVING', attack='FIRING_OR_PREATTACK_A', death='DYING'), **kwargs)


ROSTER = [
    entry('fighter', 'Gondor Soldier', 'gumaarms_skn', 'gumaarms_skl', 'gumaarms',
          dict(idle='idli', move='runa', attack='atka', death='diea'), 'gondorfighter',
          ('FORGED_BLADE', 'HAMMER1', 'GLOW', 'GLOW1'), creation='GondorFighterFunctions'),
    entry('spearman', 'Rohan Spearman', 'ruspear_skn', 'kurhdrspr_skl', 'kurhdrspr',
          dict(idle='idld', move='runa', attack='atka', death='diea'), 'rohanspearmen',
          ('FORGED_BLADE', 'HAMMER1', 'GLOW', 'GLOW1'), creation='GondorFighterFunctions'),
    entry('tower_guard', 'Tower Guard', 'gutwrgrd_skn', 'gutwrgrd_skl', 'gutwrgrd',
          dict(idle='idlb', move='runa', attack='atka', death='diea', formation='pltb'),
          'gondortowershieldguard', ('FORGED_BLADE', 'HAMMER1', 'GLOW', 'GLOW1'),
          creation='GondorFighterFunctions'),
    entry('archer', 'Gondor Archer', 'guarcher_skn', 'guarcher_skl', 'guarcher',
          dict(idle='idla', move='runa', attack='atkf2', preattack='atkf1', death='diea'),
          'gondorarcher', ('FIREAROWTIP',), creation='GondorArcherFunctions'),
    entry('ranger', 'Ithilien Ranger', 'guranger_skn', 'guranger_skl', 'guranger',
          dict(idle='idlc', move='runa', attack='atkd2', preattack='atkd1', death='diea'),
          'gondorranger', ('FIREAROWTIP',), creation='RangerFunctions'),
    entry('knight', 'Gondor Knight', 'gucavalry_skn', 'gucavalry_skl', 'gucavalry',
          dict(idle='idla', move='runa', attack='atka', death='diea'), 'gondorcavalry',
          ('FORGED_BLADE', 'SSHIELD'), creation='GondorCavalryFunctions'),
    entry('rohirrim', 'Rohirrim', 'rurohrm_skn', 'rurohrm_skl', 'rurohrm',
          dict(idle='idlb', move='runa', attack='atka', death='diea'), 'rohanrohirrim',
          ('FORGED_BLADE', 'SHIELD', 'FIREAROWTIP'), creation='RohirrimFunctions'),
    entry('rohirrim_bow', 'Rohirrim — bow', 'rurhrmarch_skn', 'rurhrmarch_skl', 'rurhrmarch',
          dict(idle='idlb', move='runa', attack='atkb', death='diea'), 'rohanrohirrim',
          ('FORGED_BLADE', 'SHIELD', 'FIREAROWTIP'), creation='RohirrimFunctions', condition='WEAPONSET_TOGGLE_1'),
    entry('dol_amroth', 'Knights of Dol Amroth', 'gudolamrth_skn', 'rurohrm_skl', 'rurohrm',
          dict(idle='idlb', move='runa', attack='atka', death='diea'), 'knightsofdolamroth',
          ('FORGED_BLADE', 'SHIELD', 'FIREAROWTIP'), creation='RohirrimFunctions'),
    entry('trebuchet', 'Trebuchet', 'gusiegtreb_skn', 'gusiegtreb_skl', 'gusiegtreb',
          dict(idle='idla', move='wlka', attack='atak', death='diea', build='blda'), 'trebuchet',
          ('FIREPLANE',), creation='TrebuchetFunctions',
          pose_overrides={'death': {'model': 'gusiegtreb_diea', 'skeleton': 'gusiegtreb_diea'},
                          'build': {'model': 'guseigtreb_a', 'skeleton': 'guseigtreb_a'}}),
]
BY_KEY = {e['key']: e for e in ROSTER}
BY_KEY['fighter']['animations']['move'] = 'gumanmocap_runb'
BY_KEY['fighter']['variants'] = equipment({'gumanatarms.tga': 'gumanatarms_ha.tga'})
BY_KEY['spearman']['variants'] = equipment({'rupeasant02.tga': 'rupeasant02_ha.tga', 'rupeasantwep.tga': 'rupeasantwep_ha.tga'})
BY_KEY['tower_guard']['variants'] = equipment({'gutowrgrd.tga': 'gutowrgrd_ha.tga', 'gutowrgrd_l.tga': 'gutowrgrd_ha.tga'})
BY_KEY['tower_guard']['conditions']['formation'] = 'ALTERNATE_FORMATION PORCUPINE'
BY_KEY['archer']['variants'] = equipment({'guarcher.tga': 'guarcher_ha.tga'}, 'fire')
for v in BY_KEY['archer']['variants']:
    v['title'] = v['title'].replace('Silverthorn', 'Fire')
BY_KEY['ranger']['variants'].append(dict(key='fire', title='Fire arrows', show=['FIREAROWTIP', 'ARROWNOCK'], hide=['ARROW'], textures={}))
BY_KEY['knight']['variants'] = equipment({'gumanatarms.tga': 'gumanatarms_ha.tga'})
for v in BY_KEY['knight']['variants']:
    if 'armor' in v['key']: v['show'].append('SSHIELD')
armor = {stem + str(i).zfill(2) + '.tga': stem + str(i).zfill(2) + 'ha.tga'
         for stem in ('rurohrm', 'ruhorse') for i in range(1, 5)}
for key in ('rohirrim', 'rohirrim_bow'):
    BY_KEY[key]['variants'] = equipment(armor, 'fire' if key.endswith('bow') else 'forged')
    for v in BY_KEY[key]['variants']:
        v['title'] = v['title'].replace('Silverthorn', 'Fire')
        if 'armor' in v['key']: v['show'].append('SHIELD')
for key in ('rohirrim', 'dol_amroth'):
    BY_KEY[key]['conditions']['death'] = 'DYING DEATH_1'
BY_KEY['rohirrim_bow']['conditions'] = dict(idle='WEAPONSET_TOGGLE_1', move='MOVING WEAPONSET_TOGGLE_1',
    attack='FIRING_OR_PREATTACK_B WEAPONSET_TOGGLE_1', death='DYING WEAPONSET_TOGGLE_1')
for key in ('archer', 'ranger'):
    BY_KEY[key]['conditions'].update(attack='FIRING_OR_RELOADING_A', preattack='PREATTACK_A')
BY_KEY['trebuchet']['conditions']['build'] = 'JUST_BUILT'
BY_KEY['trebuchet']['animations']['build'] = 'guseigtreb_a'
BY_KEY['trebuchet']['variants'].append(dict(key='fire', title='Fire stones', show=['FIREPLANE'], hide=[], textures={}))
for base, key, title, model, condition in [
    ('fighter', 'fighter_ce', 'Gondor Soldier — CE', 'gunumnrean_skn', 'USER_4'),
    ('archer', 'archer_ce', 'Gondor Archer — CE', 'gunumnarch_skn', 'USER_4'),
]:
    e = deepcopy(BY_KEY[base]); e.update(key=key, title=title, model=model, condition=condition); ROSTER.append(e)
e = deepcopy(BY_KEY['tower_guard'])
e.update(key='tower_guard_ce', title='Tower Guard — CE', model='gutowergrd_skn', skeleton='gutowergrd_skl', condition='WEAPONSET_TOGGLE_2')
e['animations'] = {p: a.replace('gutwrgrd', 'gutowergrd') for p, a in e['animations'].items()}
e['animations']['idle'] = 'gutowergrd_idla'; e['animations']['formation'] = 'gutowergrd_idlb'
e['conditions'] = dict(idle='WEAPONSET_TOGGLE_2', move='MOVING WEAPONSET_TOGGLE_2', attack='FIRING_OR_PREATTACK_A WEAPONSET_TOGGLE_2', death='DYING WEAPONSET_TOGGLE_2', formation='ALTERNATE_FORMATION WEAPONSET_TOGGLE_2 PORCUPINE')
ROSTER.append(e)
for key, title, model, source, mounted, condition in [
    ('infantry_banner', 'Gondor infantry banner', 'gubanner_skn', 'gondorinfantrybanner', False, ''),
    ('ranger_banner', 'Ranger banner', 'gurngrbnr_skn', 'gondorinfantrybanner', False, 'USER_2'),
    ('spearman_banner', 'Rohan Spearman banner', 'ruyeobnr_skn', 'rohanbanner', False, ''),
    ('knight_banner', 'Gondor Knight banner', 'gubnrcav_skn', 'gondorcavalrybanner', True, 'USER_3'),
    ('rohirrim_banner', 'Rohirrim banner', 'rurrmbnr_skn', 'rohanbanner', True, 'USER_3'),
]:
    prefix = 'rurrmbnr' if mounted else 'gubanner'
    e = entry(key, title, model, prefix + '_skl', prefix, dict(idle='idlb', move='runa', attack='atka', death='diea'),
              source, ('GLOW', 'GLOW1'), condition=condition,
              creation='CavalryFunctions' if mounted or key=='spearman_banner' else 'GondorFighterFunctions')
    if mounted: e['conditions'] = dict(idle='USER_3', move='MOVING USER_3', attack='FIRING_OR_PREATTACK_A USER_3', death='DYING USER_3')
    ROSTER.append(e)
BY_KEY = {e['key']: e for e in ROSTER}
MODELS = sorted({e['model'] for e in ROSTER} | {'gusiegtreb_diea', 'guseigtreb_a'})
LOD_MODELS = {name: [name + suffix for suffix in suffixes] for name, suffixes in {
    'guarcher_skn': 'ml', 'gubanner_skn': 'ml', 'gubnrcav_skn': 'ml', 'gucavalry_skn': 'ml',
    'gumaarms_skn': 'ml', 'gunumnarch_skn': 'l', 'gunumnrean_skn': 'l', 'guranger_skn': 'ml',
    'gurngrbnr_skn': 'ml', 'gusiegtreb_skn': 'ml', 'gutowergrd_skn': 'ml', 'gutwrgrd_skn': 'ml',
    'rurhrmarch_skn': 'ml', 'rurohrm_skn': 'ml', 'rurrmbnr_skn': 'ml', 'ruspear_skn': 'ml',
    'ruyeobnr_skn': 'ml',
}.items()}
MODELS = sorted(set(MODELS) | {m for names in LOD_MODELS.values() for m in names})
POSTER_KEYS = ('fighter', 'spearman', 'tower_guard', 'archer', 'ranger', 'knight', 'rohirrim', 'dol_amroth', 'trebuchet')
WARNINGS = [
    'Rohirrim retain both spear and bow models and all random rider/horse textures.',
    'Ranger has fire arrows, no purchasable armor; Dol Amroth has no purchased equipment skin.',
    'HD Rohirrim bow mesh has no SHIELD; HD Trebuchet has no FIREPLANE; preserve original requests.',
    'CE Soldier and Archer meshes lack their standard armor texture and upgrade subobjects; do not invent them.',
    'Summoned/campaign descendants inherit troop art unless they have an original draw override; heroes are untouched.',
]


def animation_inventory(game):
    files, missing = {}, {}
    for member in INI_MEMBERS + [RANGER_ANIMS]:
        for name in re.findall(r'^\s*AnimationName\s*=\s*(\S+)', clean(game.read(member).decode('latin-1')), re.I | re.M):
            name = name.rsplit('.', 1)[-1].lower()
            (files if game.has_model(name) else missing).setdefault(name, []).append(member)
    return dict(files={k: sorted(set(v)) for k, v in sorted(files.items())},
                missing={k: sorted(set(v)) for k, v in sorted(missing.items())})


ALLOWED_OBJECTS = {'GondorFighter', 'RohanSpearmen', 'GondorTowerShieldGuard', 'GondorArcher',
    'GondorRanger', 'GondorCavalry', 'RohanRohirrim', 'GondorKnightsofDol', 'GondorTrebuchet',
    'GondorInfantryBanner', 'GondorCavalryBanner', 'RohanBanner'}
INHERITED_DRAWS = {'GondorMinasMorgulTrebuchet': 'GondorTrebuchet',
    'RohanRoyalGuard': 'RohanRohirrim', 'GondorArcher_LoneTower': 'GondorArcher'}
ALLOWED_OBJECTS.update(INHERITED_DRAWS)


INHERITED_MODULES = {
    'GondorMinasMorgulTrebuchet': ('ModuleTag_DRAW', 'DustEffects', 'ModuleTag_FlamingRockUpgrade'),
    'RohanRoyalGuard': ('ModuleTag_01', 'DustEffects', 'Armor_Upgrade', 'FireArrows_Upgrade', 'Shield_Upgrade', 'ForgedBlades_Upgrade'),
    'GondorArcher_LoneTower': ('ModuleTag_01', 'ModuleTag_FireArrowSwapUpgrade', 'ModuleTag_HeavyArmorUpgrade'),
}


def inherited_visual_modules(block):
    """Read whole visual modules by INI depth; legacy draw indentation is inconsistent."""
    lines, out, i = block.splitlines(keepends=True), [], 0
    openers = {'defaultmodelconditionstate', 'modelconditionstate', 'animationstate',
        'idleanimationstate', 'transitionstate', 'animation', 'lodoptions'}
    while i < len(lines):
        if not re.match(r'\s*(?:Draw\s*=\s*W3D\w+Draw|Behavior\s*=\s*SubObjectsUpgrade)\b', clean(lines[i])):
            i += 1
            continue
        start, depth, script = i, 1, False
        i += 1
        while i < len(lines) and depth:
            line = clean(lines[i]).strip().lower()
            key = re.split(r'[\s=]+', line)[0]
            if script:
                if key == 'endscript': script = False
            elif key == 'beginscript': script = True
            elif key == 'end': depth -= 1
            elif key in openers: depth += 1
            i += 1
        assert depth == 0, ('Unclosed visual module', lines[start])
        out.append(''.join(lines[start:i]).rstrip('\r\n'))
    return out


def scoped_ini(member, text, replacements):
    """Keep campaign/structure children on original draws and original upgrade textures."""
    blocks = re.split(r'(?m)(?=^(?:Object|ChildObject)\s+)', text)
    originals = {}
    for b in blocks:
        head = re.match(r'(?:Object|ChildObject)\s+(\w+)', b)
        if head: originals[head[1]] = b
    for i, b in enumerate(blocks):
        head = re.match(r'(?:Object|ChildObject)\s+(\w+)[^\r\n]*', b)
        if not head or head[1] not in ALLOWED_OBJECTS: continue
        if head[1] in INHERITED_DRAWS:
            modules = inherited_visual_modules(originals[INHERITED_DRAWS[head[1]]])
            # Child-authored modules already override the matching parent tags.
            modules = [m for m in modules if m.splitlines()[0].split()[-1] not in b]
            blocks[i] = b[:head.end()] + '\n' + '\n'.join(modules) + '\n' + b[head.end():]
        else:
            blocks[i] = re.sub(r'(?im)^\s*(?:Model\s*=|Texture\s*=|UpgradeTexture\s*=|RandomTexture\s*=)[^\r\n]*',
                lambda line: re.sub(r'[\w.]+', lambda m: replacements.get(m[0].lower(), m[0]), line[0]), b)
    return ''.join(blocks)


def validate(game=None):
    from sagekit.game import Install
    from sagekit.formats.w3d import W3DFile, chunks, _cstr
    from sagekit.formats.w3dpose import Skeleton
    from sagekit.formats.textures import compiled_path
    game = game or Install(pristine=False)
    for member in SOURCE_MEMBERS: assert game.owner(member), member
    assert len(BY_KEY) == len(ROSTER)
    for model in MODELS: assert game.has_model(model), model
    for e in ROSTER:
        source = clean(game.read(e['source']).decode('latin-1')).lower()
        if e['key']=='ranger': source += clean(game.read(RANGER_ANIMS).decode('latin-1')).lower()
        blocks = re.split(r'^\s*(?:animationstate\s*=?\s*([^\n]*)|idleanimationstate([^\n]*))$', source, flags=re.M)
        routes = {}
        for i in range(1, len(blocks), 3):
            condition = ' '.join(blocks[i].upper().split()) if blocks[i] is not None else 'IDLE'
            routes.setdefault(condition, []).extend(re.findall(r'animationname\s*=\s*(\S+)', blocks[i+2]))
        for v in e['variants']:
            for pose in e['animations']:
                s = state(e, v['key'], pose)
                assert any(a.rsplit('.', 1)[-1] == s['animation'] for a in routes.get(s['condition'], [])), (e['key'], pose, s['condition'], s['animation'])
                w = W3DFile(game.read(game.model_path(s['model'])))
                assert w.skeleton() in (None, s['skeleton']+'.w3d'), (e['key'], pose, w.skeleton())
                assert game.has_model(s['animation']), s['animation']
                skel = Skeleton(game.read(game.model_path(s['skeleton'])))
                data = game.read(game.model_path(s['animation']))
                headers = [data[p+8:p+8+n] for tag, off, size, _ in chunks(data, 0, len(data))
                    if tag in (0x200, 0x280) for kind, p, n, _ in chunks(data, off+8, off+8+size)
                    if kind in (0x201, 0x281)]
                assert headers and _cstr(headers[0][20:36]).upper() == skel.name.upper(), (e['key'], pose)
                for tex in s.get('textures', {}).values():
                    assert any(game.owner(compiled_path(tex, ext)) for ext in ('.dds', '.tga')), tex
    def objects(text):
        return {m[1]:b for b in re.split(r'(?m)(?=^(?:Object|ChildObject)\s+)',text)
                if (m := re.match(r'(?:Object|ChildObject)\s+(\w+)',b))}
    for member in INI_MEMBERS:
        original = game.read(member).decode('latin1')
        patched = scoped_ini(member, original, {n:'test_'+n for n in MODELS})
        before, after = objects(original), objects(patched)
        assert before.keys() == after.keys()
        for name in before:
            if name not in ALLOWED_OBJECTS: assert before[name] == after[name], name
            if name in INHERITED_DRAWS:
                parent = before[INHERITED_DRAWS[name]]
                expected = inherited_visual_modules(parent)
                for module in expected:
                    assert module in after[name], (name, module.splitlines()[0])
                assert tuple(m.splitlines()[0].split()[-1] for m in expected) == INHERITED_MODULES[name]

    print('Men troop source, models and animation routes passed.')


if __name__ == '__main__':
    validate()
