"""Private Gondor troop steel and charcoal cloth; source bodies, faces and mounts retained."""
import json
import math
import subprocess
from pathlib import Path

from assets.dwarves.porter.unit import Mesh as Primitives
from assets.dwarves.troops.paint import write_sheet
from assets.elves.troops.art import Mesh as Edging
from sagekit.formats import w3dmesh as WM, w3dpose as P
from sagekit.formats.w3d import MESH, W3DFile, chunks
from sagekit.formats.w3dframes import mesh_bones

# Image coordinates reviewed on installed HD sheets. Broad guards retain faces,
# hair, hands and natural textures, including the secondary crew portrait on siege.
PROTECT = {
    'gumanatarms':[(.62,.06,.74,.29)], 'guarcher':[(.62,.06,.74,.29)],
    'gutowrgrd':[(0,.30,.28,.48)], 'guranger':[(0,.46,.53,1)],
    'gudolamroth':[(0,.103,.25,.26),(.135,0,.25,.105),
                   (0,.038,.034,.104),(.045,.010,.061,.027),(.55,.53,.91,1)],
    'gunumnrean':[(.41,.65,1,1)],
    'rupeasant02':[(.45,0,.75,.30)], 'ruarcher':[(.84,0,1,.25)],
    'guseigtreb':[(.37,.44,.50,.51),(.43,.77,1,1)],
    'guseigtreb_dmg':[(.37,.44,.50,.51),(.43,.77,1,1)],
    **{f'rurohrm{i:02}':[(.86,0,1,.23)] for i in range(1,5)},
}
# Only reviewed cloth islands are desaturated. Rangers and Rohan retain green.
CLOTH = {
    'gudolamroth':[(0,0,.14,.11),(0,.25,.37,.50),(.18,.50,.50,.78),(.50,0,.84,.50)],
    'gunumnrean':[(0,.04,.45,.97)],
    'rupeasant02':[(0,.06,.44,.97),(.75,.18,1,.81)],
    'ruarcher':[(0,.02,.51,.90)],
}
# Restrict paint to actual silver surfaces, leaving timber/leather and green cloth.
SILVER = {
    'gumanatarms':[(0,0,1,1)], 'guarcher':[(0,0,1,1)],
    'gutowrgrd':[(0,0,1,1)], 'gumaarmsshield':[(0,0,.54,1)],
    'gudolamroth':[(.25,0,1,.50),(0,.78,.50,1)],
    'guithilstuff':[(0,0,1,1)], 'gunumshield':[(0,0,1,1)],
    'gunumnrean':[(.58,.1,1,.72)],
    'rupeasant02':[(.49,.63,.84,1),(0,0,.45,.15)],
    'ruarcher':[(.52,.29,.92,.97)],
    'guseigtreb':[(0,0,.50,.45),(0,.47,1,.60)],
    'guseigtreb_dmg':[(0,0,.50,.45),(0,.47,1,.60)],
    **{f'rurohrm{i:02}':[(0,0,.43,1),(.52,.28,.76,.49)] for i in range(1,5)},
}
BANNERS = {'gubanner','gurgbanr','ruyeobanner','ruyeobannerb','rurohbanner'}
RECIPES = {
    'gumaarms_skn':('BAT_SHIELD','SWORD'), 'gucavalry_skn':('SSHIELD','SWORD'),
    'gubanner_skn':('BAT_SHIELD','SWORD'), 'gubnrcav_skn':('BACKSHIELD','SWORD'),
    'gutowergrd_skn':('SHIELD','SPEAR','PAULDRONS'),
    'gutwrgrd_skn':('SPEAR','PAULDRONS'), 'ruspear_skn':('SPEAR',),
    'guranger_skn':('RANGERSWORD',), 'gurngrbnr_skn':('SWORD',),
    'gudolamrth_skn':('LANCE','SWORD','COLLAR','COLLAR2'),
    'rurohrm_skn':('SPEAR',), 'rurrmbnr_skn':('SPEAR',),
    'ruyeobnr_skn':('SHOULDER','SWORD'), 'gusiegtreb_skn':('BRACERS','BRACERS01'),
}
METAL = {'gumanatarms':(.08,.36),'gumaarmsshield':(.04,.36),
         'gutowrgrd':(.43,.21),'rupeasant02':(.425,.70),
         'guithilstuff':(.35,.51),'gudolamroth':(.36,.12),
         'rurohrm01':(.79,.12),'rurohrm02':(.79,.12),
         'ruarcher':(.838,.409),'guseigtreb':(.15,.12)}
supported_modelnames = tuple(RECIPES)


def family(name):
    stem=Path(name).stem.lower()
    if stem.endswith('_ha'):return stem[:-3]
    if stem.startswith('rurohrm') and stem.endswith('ha'):return stem[:-2]
    return stem


class Mesh(Edging):
    def __init__(self,original,skeleton,rigid_bone):
        Primitives.__init__(self,original,skeleton)
        self.bones=P.influences(original.bytes) or [rigid_bone]*len(original.verts)
        self.verts=[(0,[(i,1)],P.IDENTITY,b,{}) for i,b in enumerate(self.bones)]
        self.tris=list(zip(original.tris,original.surface))
        self.world=[P.point(skeleton.rest[b],v) for b,v in zip(self.bones,original.verts)]
        self.patch=METAL[family(original.textures[0])]


def design(w,sk,name):
    rigid=mesh_bones(w.data);out={}
    for key in RECIPES.get(Path(name).stem.lower(),()):
        old=w.meshes[key]
        # The shared writer omits secondary skin data; complete bodies stay exact.
        if any(t in (0xC00,0xC01) for t,_,_,_ in chunks(old.bytes,8,len(old.bytes))):continue
        if len({i for tri in old.tris for i in tri})!=len(old.verts):continue
        mesh=Mesh(old,sk,rigid.get(key,0));mesh.edging(6,.038)
        if len(mesh.verts)>len(old.verts):out[key]=mesh.chunk()
    return out


def eligible(name):
    return family(name) in set(SILVER)|set(CLOTH)|BANNERS


def paint(source,dest,name):
    import numpy as np
    f=family(name)
    if not eligible(name):raise ValueError('Unreviewed Men troop sheet: '+name)
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
    cloth=rects(CLOTH.get(f,[]))&~protected
    if f in BANNERS:cloth=(b>r*1.08)&(b>g*.98)&(sat>.18)
    if f=='gudolamroth':cloth&=(b>r*1.08)&(b>g*.98)&(sat>.18)
    neutral=lum[:,:,None]*np.array([.99,1,1.02])
    out[cloth]=rgb[cloth]*.04+neutral[cloth]*.96
    metal=np.clip((.25-sat)/.10,0,1)
    if Path(name).stem.lower().endswith('_ha') and f in ('gumanatarms','guarcher','gutowrgrd'):
        # Heavy armour remains brighter than base, with the source gold as a warm accent.
        warm=np.clip((r-g)/.04,0,1)*np.clip((g-b)/.07,0,1)
        metal=np.maximum(metal,warm)
    silver=(rects(SILVER.get(f,[]))&~cloth&~protected)*metal*np.clip((lum-.06)/.12,0,1)
    # Continuous luminance retains etched trees, mail and painted metal scratches.
    steel=np.clip(lum[:,:,None]*1.12+.014,0,1)*np.array([.98,1,1.025])
    amount=silver[:,:,None]*.80
    out=out*(1-amount)+steel*amount
    result=original.copy();result[:,:,:3]=np.round(np.clip(out,0,1)*255).astype(np.uint8)
    result[protected]=original[protected]
    assert np.array_equal(result[:,:,3],original[:,:,3])
    assert np.array_equal(result[protected],original[protected])
    subprocess.run(['magick','-size',f'{w}x{h}','-depth','8','rgba:-',str(dest)],input=result.tobytes(),check=True)
    return dict(width=w,height=h,changed_pixels=int(np.any(result!=original,axis=2).sum()),
                protected_pixels=int(protected.sum()),alpha_preserved=True)


def protect_blocks(source,dest,name):
    """Keep protected face/hair RGB compressed blocks exact, including every source mip."""
    from sagekit.formats.textures import dds_info
    boxes=PROTECT.get(family(name),[])
    if not boxes:return
    before,after=dds_info(source),dds_info(dest)
    assert before['fourcc'] in ('DXT1','DXT3','DXT5')
    assert all(before[k]==after[k] for k in ('fourcc','width','height','mips'))
    original=source.read_bytes();data=bytearray(dest.read_bytes());a=b=128
    stride=8 if before['fourcc']=='DXT1' else 16
    target=8 if after['fourcc']=='DXT1' else 16
    for level in range(before['mips'] or 1):
        w,h=max(1,before['width']>>level),max(1,before['height']>>level)
        for y in range(0,h,4):
            for x in range(0,w,4):
                if any(x<c*w and x+4>p*w and y<d*h and y+4>q*h for p,q,c,d in boxes):
                    data[b+target-8:b+target]=original[a+stride-8:a+stride]
                a+=stride;b+=target
    dest.write_bytes(data)


def run(manifest):
    from sagekit.formats.textures import dds_info
    data=json.loads(Path(manifest).read_text());report={}
    for name,item in data['textures'].items():
        dest=Path(item['output']);png=dest.with_suffix('.png');source=Path(item['source'])
        report[name]=paint(source,png,name)
        before=dds_info(source)
        if before['fourcc']=='DXT1':
            # BC1's three-colour interpolation must stay BC1 for exact source faces.
            subprocess.run(['magick',str(png),'-define','dds:compression=dxt1',
                '-define',f"dds:mipmaps={max(1,before['mips'])-1}",
                '-define','dds:cluster-fit=true',str(dest)],check=True)
            assert dds_info(dest)['mips']==before['mips']
        else:write_sheet(png,dest,source)
        protect_blocks(source,dest,name)
    Path(manifest).with_name('paint-checks.json').write_text(json.dumps(report,indent=2)+'\n')


def check_sources(folder=Path('build/assets/men/troops/art-sources')):
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
