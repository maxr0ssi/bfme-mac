"""Fitted Elven edging and private neutral-cloth sheets; original anatomy and rigs retained."""
import json
import math
import subprocess
from pathlib import Path

from assets.dwarves.porter.unit import Mesh as Primitives
from assets.dwarves.troops.infantry import Mesh as Edging
from assets.dwarves.troops.paint import write_sheet
from assets.elves.style import PALETTE
from sagekit.formats import w3dmesh as WM, w3dpose as P
from sagekit.formats.w3d import MESH, TRIANGLES, W3DFile, chunks
from sagekit.formats.w3dframes import mesh_bones

# Rectangles are image coordinates, checked against the extracted source sheets. Face,
# hair, bare hands, horse hides and natural creatures are never recoloured.
PROTECT = {
    'eulorarch':[(.64,0,.82,.23),(.79,.49,1,.68),(.64,.58,1,1)],
    'eulorienwarrior':[(.64,0,.82,.23),(.79,.49,1,.68),(.64,.58,1,1)],
    'eulorarch_ha':[(.64,0,.82,.23),(.79,.49,1,.68),(.64,.58,1,1)],
    'eulorwarha':[(.64,0,.82,.23),(.79,.49,1,.68),(.64,.58,1,1)],
    'eumthlnd_c':[(.64,.60,1,1)], 'eurivenlan_c':[(.64,.60,1,1)],
    'eumthlndb_c':[(.62,.09,.82,.57),(.88,.38,1,.67),(.54,.89,.72,1)],
    'rulaelvnwrrior':[(.64,0,.91,.39)],
    'eumirkarch_c':[(.47,.39,.72,.59),(.47,.63,.80,1),(.77,0,1,.39)],
    'eumirkban_c':[(.62,0,.95,.43),(.45,.43,.63,.59),(.47,.63,.78,1)],
}
CLOTH = {
    'eulorarch':[(0,.24,.45,1),(.44,0,.64,.78),(.80,0,1,.56)],
    'eulorienwarrior':[(0,.24,.45,1),(.44,0,.64,.78),(.80,0,1,.56)],
    'eulorarch_ha':[(0,.24,.45,.48),(.44,0,.64,.78),(.80,.23,1,.56)],
    'eulorwarha':[(0,.24,.45,.48),(.44,0,.64,.78),(.80,.23,1,.56)],
    'eumthlnd_c':[(0,.66,.46,1)], 'eurivenlan_c':[(0,.66,.46,1),(.29,0,.39,.40)],
    'eumthlndb_c':[(0,0,.41,.90),(.62,0,.82,.12)],
    'rulaelvnwrrior':[(0,.42,.35,.64)],
    'eumirkarch_c':[(0,.47,.47,1)], 'eumirkban_c':[(0,.42,.47,1)],
}
# Tiny occupied silver/gold samples used by added faces; no source UVs are moved.
METAL = {'eulorarch':(.10,.09), 'eulorienwarrior':(.10,.09),
         'eulorarch_ha':(.10,.09), 'eulorwarha':(.10,.09),
         'eumthlnd_c':(.16,.23), 'eurivenlan_c':(.16,.23),
         'eumthlndb_c':(.49,.31), 'rulaelvnwrrior':(.23,.30),
         'eumirkarch_c':(.59,.27), 'eumirkban_c':(.23,.66),
         'mirkwoodshield':(.47,.13), 'euhaldirgear':(.24,.36)}
RECIPES = {
    'eulorarch_skn':('SHLDR',), 'eulorwar_skn':('SHLD','SHLDR'),
    'eumirkarch_skn':(), 'eumirkbnr_skn':(),
    'eumthlnd_skn':('LANCE',), 'eumthlnd_sknb':(),
    'eurivenarch_skn':(), 'eurivenlan_skn':('LANCE',),
    'eurvnbnr_skn':('LANCE',), 'rulaelfwar_skn':('SWORD01',),
    'euarchbnr_skn':('SHLDR',), 'eulorbnr_skn':('SHLDR',),
    'eumthbnr_skn':('LANCE',), 'ruelvnbanr_skn':('SHLDR',),
}
# Armour upgrade layouts match their base sheets; the Mirkwood upgrade placeholder
# is deliberately not repainted. Natural cloak foliage stays green.
for upgraded,base in {'eumthlnd_ha':'eumthlnd_c','eumthlndb_ha':'eumthlndb_c',
                      'eurivenlan01ha':'eurivenlan_c'}.items():
    PROTECT[upgraded]=PROTECT[base]
    CLOTH[upgraded]=CLOTH[base]

supported_modelnames=tuple(RECIPES)


def family(name):
    return Path(name).stem.lower()


class Mesh(Edging):
    def __init__(self, original, skeleton, rigid_bone):
        Primitives.__init__(self, original, skeleton)
        self.bones=P.influences(original.bytes) or [rigid_bone]*len(original.verts)
        self.verts=[(0,[(i,1)],P.IDENTITY,b,{}) for i,b in enumerate(self.bones)]
        self.tris=list(zip(original.tris,original.surface))
        self.world=[P.point(skeleton.rest[b],v) for b,v in zip(self.bones,original.verts)]
        self.patch=METAL[Path(original.textures[0]).stem.lower()]

    def chunk(self):
        raw=bytearray(super().chunk())
        # Preserve every original per-vertex and triangle byte, including source normals.
        def arrays(data,start,end):
            for tag,off,size,nested in chunks(data,start,end):
                if tag in WM.PER_VERTEX or tag==TRIANGLES:yield tag,off+8,size
                elif nested:yield from arrays(data,off+8,off+8+size)
        old=list(arrays(self.original.bytes,8,len(self.original.bytes)))
        new=list(arrays(raw,8,len(raw)))
        assert [x[0] for x in old]==[x[0] for x in new]
        for (_,a,size),(_,b,_) in zip(old,new):raw[b:b+size]=self.original.bytes[a:a+size]
        return bytes(raw)



def design(w,sk,name):
    name=Path(name).stem.lower()
    if name not in RECIPES:return {}
    rigid=mesh_bones(w.data);out={}
    for key in RECIPES[name]:
        old=w.meshes[key]
        # Secondary-bone positions/normals are not handled by the shared writer.
        # Keep blended bodies byte-exact rather than risk changing their animation.
        if any(t in (0xC00,0xC01) for t,_,_,_ in chunks(old.bytes,8,len(old.bytes))):continue
        # Keep original helmet shape byte-exact; detail is carried by its sheet.
        if key.startswith(('HLMT')):continue
        if len({i for t in old.tris for i in t})!=len(old.verts):continue
        mesh=Mesh(old,sk,rigid.get(key,0))
        mesh.edging(6,.038)
        if len(mesh.verts)>len(old.verts):out[key]=mesh.chunk()
    return out


def eligible(name):
    return Path(name).stem.lower() in set(PROTECT)|{'mirkwoodshield','euhaldirgear','eurvnbanr','ruelvban'}


def paint(source,dest,name):
    import numpy as np
    from sagekit.paint.fields import ramp
    f=Path(name).stem.lower()
    if not eligible(name):raise ValueError('Unreviewed troop sheet: '+name)
    w,h=map(int,subprocess.check_output(['magick','identify','-format','%w %h',str(source)]).split())
    raw=subprocess.check_output(['magick',str(source),'-depth','8','rgba:-'])
    original=np.frombuffer(raw,np.uint8).reshape(h,w,4).copy()
    rgb=original[:,:,:3].astype(float)/255;r,g,b=rgb.transpose(2,0,1)
    lum=.2126*r+.7152*g+.0722*b
    hi,lo=rgb.max(axis=2),rgb.min(axis=2);sat=(hi-lo)/np.maximum(hi,.001)
    y,x=np.mgrid[:h,:w];x=(x+.5)/w;y=(y+.5)/h
    def rects(boxes):
        mask=np.zeros((h,w),bool)
        for a,b,c,d in boxes:mask|=(x>=a)&(x<c)&(y>=b)&(y<d)
        return mask
    protected=rects(PROTECT.get(f,[]));out=rgb.copy()
    def apply(mask,material,strength,gain=1,lift=0):
        mask=mask&~protected&(hi>.035)
        target=ramp(np.clip(lum*gain+lift,0,1),PALETTE.ramps[material])
        out[mask]=rgb[mask]*(1-strength)+target[mask]*strength
    cloth=rects(CLOTH.get(f,[]))&~protected
    if f in ('eurvnbanr','ruelvban'):
        cloth=(b>r*1.10)&(b>g*.9)&(sat>.2)&~protected
    # Desaturate cloth at its original luminance: no thresholded ramp that produces
    # speckled edges between dark thread and dyed fabric. Embroidery keeps its shading.
    neutral=lum[:,:,None]*np.array([1.04,1.01,.96])
    out[cloth]=rgb[cloth]*.06+neutral[cloth]*.94
    # Existing silver only; coloured leather, wood, skin and hair remain untouched.
    silver=(sat<.18)&(lum>.18)&~cloth
    apply(silver,'trim',.45,1.06,.025)
    if f in ('mirkwoodshield','euhaldirgear'):
        gold=(r>g*1.05)&(g>b*1.18)&(lum>.4)&(sat<.65)
        apply(gold,'gold',.35)
    result=original.copy();result[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8)
    result[protected]=original[protected]
    assert np.array_equal(result[:,:,3],original[:,:,3])
    assert np.array_equal(result[protected],original[protected])
    subprocess.run(['magick','-size',f'{w}x{h}','-depth','8','rgba:-',str(dest)],input=result.tobytes(),check=True)
    return dict(width=w,height=h,changed_pixels=int(np.any(result!=original,axis=2).sum()),
                protected_pixels=int(protected.sum()),alpha_preserved=True)


def run(manifest):
    data=json.loads(Path(manifest).read_text());report={}
    for name,item in data['textures'].items():
        dest=Path(item['output']);png=dest.with_suffix('.png')
        report[name]=paint(item['source'],png,name)
        write_sheet(png,dest,Path(item['source']))
    Path(manifest).with_name('paint-checks.json').write_text(json.dumps(report,indent=2)+'\n')


def check_sources(folder=Path('build/assets/elves/troops/art-sources')):
    """Run on extracted source art only; never starts or writes to the game."""
    report={}
    for name in supported_modelnames:
        w=W3DFile(str(folder/(name+'.w3d')))
        sk=P.Skeleton((folder/w.skeleton().lower()).read_bytes())
        changes=design(w,sk,name);new=W3DFile(WM.replace_meshes(w.data,changes))
        assert [b for t,b in w.top() if t!=MESH]==[b for t,b in new.top() if t!=MESH]
        for key,old in w.meshes.items():
            m=new.meshes[key];n=len(old.verts)
            assert m.verts[:n]==old.verts and m.normals[:n]==old.normals
            assert m.uv[:n]==old.uv and m.tris[:len(old.tris)]==old.tris
            bones=P.influences(old.bytes);after=P.influences(m.bytes)
            assert after[:n]==bones if bones else after is None
            assert all(math.isfinite(v) for rows in (m.verts,m.normals,m.uv) for row in rows for v in row)
            assert all(0<=i<len(m.verts) for tri in m.tris for i in tri)
            if key not in changes:assert m.bytes==old.bytes
            if any(t in (0xC00,0xC01) for t,_,_,_ in chunks(old.bytes,8,len(old.bytes))):
                assert key not in changes and m.bytes==old.bytes
        report[name]=dict(changed_meshes=list(changes),added_triangles=sum(
            len(new.meshes[k].tris)-len(m.tris) for k,m in w.meshes.items()))
    (folder/'geometry-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    import sys
    if sys.argv[-1]=='--check':print(json.dumps(check_sources(),indent=2))
    else:run(sys.argv[-1])
