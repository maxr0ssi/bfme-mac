"""Audit private Elven art and every matching source animation without touching the game."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from sagekit import paths
from assets.elves.troops import build, catalog, art
from assets.dwarves.troops import audit, motion_check


def scope_check(folder=build.FOLDER, archive=build.ARCHIVE, roster=catalog, allowed=None, inherited=None):
    """Independently reverse aliases and check object boundaries, including inherited draws."""
    from sagekit.game import Install
    from sagekit.formats.big import Archive
    from sagekit.formats.w3d import W3DFile, chunks, TRIANGLES
    from sagekit.formats.w3dmesh import PER_VERTEX
    game=Install(pristine=False)
    package=Archive(str(folder/'staged'/archive))
    manifest=json.loads((folder/'build.json').read_text())
    def arrays(raw,start=8,end=None):
        for tag,offset,size,nested in chunks(raw,start,len(raw) if end is None else end):
            if tag in PER_VERTEX or tag==TRIANGLES or tag>=0xC00:
                yield tag,raw[offset+8:offset+8+size]
            elif nested:yield from arrays(raw,offset+8,offset+8+size)
    for name,item in manifest['models'].items():
        before=W3DFile(item['source']);after=W3DFile(package.read(game.model_path(item['alias'])))
        for key,mesh in before.meshes.items():
            a,b=list(arrays(mesh.bytes)),list(arrays(after.meshes[key].bytes))
            assert [t for t,_ in a]==[t for t,_ in b],('Original array inventory changed',name,key)
            for (tag,original),(_,updated) in zip(a,b):
                assert updated[:len(original)]==original,('Original array bytes changed',name,key,hex(tag))
                if tag>=0xC00:assert updated==original,('Secondary skin data changed',name,key,hex(tag))
    reverse={item['alias']:name for section in ('models','textures')
             for name,item in manifest[section].items()}
    if inherited is None:inherited={'ElvenFortressEagle':'GondorGwaihir','RohanEntFir':'RohanEntBase'}
    allowed=allowed if allowed is not None else {'ElvenLorienWarrior','ElvenLorienArcher','ElvenMithlondSentry','ElvenMirkwoodArcher',
        'ElvenRivendellLancer','ElvenRivendellArcher','NoldorWarrior','ElvenBanner',
        'ElvenMirkwoodArcherBanner','ElvenRivendellLancerBanner','ElvenFortressEagle',
        'RohanEntFir','RohanEntBirch','RohanEntOak','RohanEntAshMelee'}
    draw_pattern=r'(?ms)^\tDraw\s*=\s*W3DScriptedModelDraw[^\r\n]*.*?^\tEnd[^\r\n]*'
    def objects(text):
        matches=list(re.finditer(r'(?im)^(?:Object|ChildObject)\s+(\w+)',text))
        return {m[1]:text[m.start():matches[i+1].start() if i+1<len(matches) else len(text)]
                for i,m in enumerate(matches)}
    def lines(text):
        return [line.strip().lower() for line in text.splitlines() if line.strip()]
    changed=[]
    for member in roster.INI_MEMBERS:
        old=objects(game.read(member).decode('latin1'))
        new=objects(package.read(member).decode('latin1'))
        assert old.keys()==new.keys(),('Object inventory changed',member)
        for name,before in old.items():
            after=new[name]
            if before==after:continue
            assert name in allowed,('Unrelated object modified',name)
            restored=re.sub(r'[\w.]+',lambda m:reverse.get(m[0].lower(),m[0]),after)
            if name in inherited:
                if hasattr(roster,'INHERITED_MODULES'):
                    modules=roster.inherited_visual_modules(old[inherited[name]])
                    assert tuple(m.splitlines()[0].split()[-1] for m in modules)==roster.INHERITED_MODULES[name]
                    for module in modules:
                        assert restored.count(module)==1,('Original inherited visual module missing',name)
                        restored=restored.replace(module,'',1)
                    assert lines(restored)==lines(before),('Nonvisual child change',name)
                    changed.append(name)
                    continue
                draw=re.search(draw_pattern,restored)
                assert draw,('Missing isolated draw',name)
                parent=old[inherited[name]]
                parent_draw=re.search(draw_pattern,parent)
                assert parent_draw and lines(draw[0])==lines(parent_draw[0]),('Inherited draw changed',name)
                restored=restored[:draw.start()]+restored[draw.end():]
            assert lines(restored)==lines(before),('Nonvisual object change',name)
            changed.append(name)
    (folder/'scope-checks.json').write_text(json.dumps(dict(status='PASS',changed_objects=changed,
        unrelated_gameplay_and_effective_visuals_unchanged=True),indent=2)+'\n')


def preview_check(folder=build.FOLDER, roster=catalog):
    """Require the complete representative gallery to match the current staged art."""
    from types import SimpleNamespace
    from assets.dwarves.troops import preview
    preview.configure(folder,roster,preview.RUN_SCRIPT,preview.TITLE,preview.NOTES)
    data=json.loads((folder/'build.json').read_text())
    inputs=[Path(v['work']) for v in data['models'].values()]
    inputs += [Path(v['output']) for v in data['textures'].values()]
    inputs.append(ROOT/'assets/dwarves/troops/posing.py')
    newest=max(p.stat().st_mtime for p in inputs)
    request=json.loads((folder/'preview-request.json').read_text())
    samples=request['frames']
    jobs=preview.jobs(SimpleNamespace(unit=None,variant=None,pose=None,stills=True,motion=True,all_variants=False))
    records=[]
    for job in jobs:
        path=folder/'renders'/(preview.stem(job)+('.png' if job['kind']=='still' else '.gif'))
        assert path.is_file() and path.stat().st_size>0,('Missing preview',path)
        assert path.stat().st_mtime>newest,('Stale preview',path)
        frames=subprocess.check_output(['magick','identify','-format','%n %T\n',str(path)],text=True).splitlines()
        if job['kind']=='motion':
            delay=preview.frame_delay(job,samples)
            assert len(frames)==samples and all(row==f'{samples} {delay}' for row in frames),('GIF timing',path,frames)
        else:
            assert len(frames)==1 and frames[0].split()[0]=='1',('Still frame count',path)
        records.append(dict(**job,file=str(path),frames=len(frames),current=True))
    report=dict(status='PASS',stills=sum(j['kind']=='still' for j in jobs),
        motions=sum(j['kind']=='motion' for j in jobs),sampled_frames_per_motion=samples,
        source_nominal_delays_verified=True,newer_than_current_art_and_poser=True,previews=records)
    (folder/'preview-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: complete current gallery, source nominal GIF timing.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--motion',action='store_true',help='Also decode every matching source clip')
    p.add_argument('--previews',action='store_true',help='Verify full current gallery and source GIF timing')
    args=p.parse_args()
    scope_check()
    print(audit.audit(build.FOLDER,build.configure(),catalog,art)['status'])
    if args.previews:preview_check()
    if args.motion:
        from sagekit.pipeline import blender_slot, game_running
        if game_running():raise SystemExit('Close the game before checking animation data.')
        with blender_slot(),(build.FOLDER/'motion-checks.log').open('w') as log:
            subprocess.run([paths.BLENDER,'-b','--python-exit-code','1','--python',str(Path(__file__).resolve())],
                           stdout=log,stderr=subprocess.STDOUT,check=True)
        result=json.loads((build.FOLDER/'motion-checks.json').read_text())
        print(result['status'],json.dumps(result['counts'],sort_keys=True))


if __name__=='__main__':
    motion_check.run(build.FOLDER,catalog) if 'bpy' in sys.modules else main()
