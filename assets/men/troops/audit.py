"""Audit staged Men troop art, inherited object scope, skins, animations and previews."""
import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from sagekit import paths
from assets.men.troops import build, catalog, art
from assets.dwarves.troops import audit, motion_check
from assets.elves.troops.audit import scope_check, preview_check


def protected_dds_check():
    data=json.loads((build.FOLDER/'build.json').read_text())
    for name,item in data['textures'].items():
        boxes=art.PROTECT.get(art.family(name),[])
        if not boxes:continue
        (w,h),before=audit.pixels(item['source'])
        size,after=audit.pixels(item['output'])
        assert size==(w,h)
        for x,y,X,Y in boxes:
            left,right=max(0,math.ceil(x*w-.5)),min(w,math.ceil(X*w-.5))
            for row in range(max(0,math.ceil(y*h-.5)),min(h,math.ceil(Y*h-.5))):
                a,b=(row*w+left)*4,(row*w+right)*4
                assert before[a:b]==after[a:b],('DDS protected face/hair changed',name,row)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--motion',action='store_true')
    parser.add_argument('--previews',action='store_true')
    args=parser.parse_args()
    scope_check(build.FOLDER,build.ARCHIVE,catalog,catalog.ALLOWED_OBJECTS,catalog.INHERITED_DRAWS)
    report=audit.audit(build.FOLDER,build.configure(),catalog,art)
    assert all(v['dds_alpha_max_error']==0 for v in report['textures'].values())
    protected_dds_check()
    print(report['status'])
    if args.previews:preview_check(build.FOLDER,catalog)
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
