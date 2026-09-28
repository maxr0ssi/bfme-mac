"""Read-only staged troop-art audit; python3 -m assets.dwarves.troops.audit.

No installation, game launch, or live cache writes. Reports go beside build.json.
"""
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

from sagekit import paths
from sagekit.formats import w3dpose as P
from sagekit.formats.assetcache import AssetCache
from sagekit.formats.big import Archive
from sagekit.formats.textures import compiled_path, dds_info
from sagekit.formats.w3d import W3DFile, MESH, HLOD, MESH_HEADER3, VERTEX_INFLUENCES, chunks
from sagekit.game import Install
from sagekit.install import cache_records
from . import build, catalog, paint


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pixels(path):
    size = tuple(map(int, subprocess.check_output(['magick','identify','-format','%w %h',str(path)]).split()))
    return size, subprocess.check_output(['magick',str(path),'-depth','8','rgba:-'])


def flags(mesh):
    o=next(o for t,o,s,h in chunks(mesh.bytes,8,len(mesh.bytes)) if t==MESH_HEADER3)
    return mesh.bytes[o+12:o+16]


def skin_arrays(raw,start=8,end=None):
    """Keep every original influence field and opaque secondary-skin payload."""
    for tag,offset,size,nested in chunks(raw,start,len(raw) if end is None else end):
        if tag==VERTEX_INFLUENCES or tag>=0xC00:
            yield tag,raw[offset+8:offset+8+size]
        elif nested:yield from skin_arrays(raw,offset+8,offset+8+size)


def audit(folder=build.FOLDER, pipeline=build, roster=catalog, painter=paint):
    build,catalog,paint=pipeline,roster,painter
    data=json.loads((folder/'build.json').read_text());g=Install(pristine=False)
    staged=Archive(str(folder/'staged'/build.ARCHIVE));members=set(staged.index())
    report={'sources':{},'models':{},'textures':{},'installation_unchanged':False,'issues':[]}
    for member,want in data['source_hashes'].items():
        local=folder/'src'/Path(*member.split('\\'))
        assert digest(local.read_bytes())==want,('extracted source changed',member)
        assert digest(g.read(member))==want,('active source changed',member)
    snapshot=Path(paths.BUILD)/'install-pair/after.json'
    for name,want in json.loads(snapshot.read_text()).items():
        assert digest(Path(name).read_bytes())==want,('installation changed',name)
    assert all(not (Path(d)/build.ARCHIVE).exists() for d in paths.GAMEDIRS.values())
    report['installation_unchanged']=True
    report['sources']['verified']=len(data['source_hashes'])
    assert build.ARCHIVE<'!!!!!!!!!!!!sagekit-dwarf-builder.big'
    live_caches=[AssetCache(str(Path(d)/'asset.dat')) for d in paths.GAMEDIRS.values()]
    caches=[AssetCache(str(folder/'staged'/(Path(d).name+'-asset.dat'))) for d in paths.GAMEDIRS.values()]
    new_textures={v['alias'].lower() for section in ('textures','house') for v in data[section].values()}
    for live,new in zip(live_caches,caches):
        assert cache_records(live)==cache_records(new,new_textures), 'Unrelated cache records changed'
    expected=set(catalog.INI_MEMBERS)|{'data\\ini\\housecolor.ini'}
    for name,item in data['models'].items():
        member=g.model_path(item['alias']);expected.add(member)
        old=W3DFile(item['source']);new=W3DFile(staged.read(member))
        assert not g.has_model(item['alias'])
        assert not any(c.has_model(item['alias']+'.w3d') for c in live_caches+caches)
        assert new.skeleton()==old.skeleton()
        assert P.hlod(new.data)[1:]==P.hlod(old.data)[1:]
        assert P.hlod(new.data)[0].lower()==item['alias']
        assert old.meshes.keys()==new.meshes.keys()
        assert [raw for tag,raw in old.top() if tag not in (MESH,HLOD)] == [raw for tag,raw in new.top() if tag not in (MESH,HLOD)]
        for key,m in old.meshes.items():
            n=new.meshes[key];count=len(m.verts)
            assert n.container.lower()==item['alias']
            assert n.verts[:count]==m.verts and n.uv[:count]==m.uv
            assert n.tris[:len(m.tris)]==m.tris and flags(n)==flags(m)
            assert n.skinned==m.skinned
            a,b=list(skin_arrays(m.bytes)),list(skin_arrays(n.bytes))
            assert [t for t,_ in a]==[t for t,_ in b],('Skin array inventory changed',name,key)
            for (tag,original),(_,updated) in zip(a,b):
                assert updated[:len(original)]==original,('Original skin fields changed',name,key,hex(tag))
                if tag>=0xC00:assert updated==original,('Secondary skin data changed',name,key,hex(tag))
            oldbones,newbones=P.influences(m.bytes),P.influences(n.bytes)
            assert newbones[:count]==oldbones if oldbones is not None else newbones is None
            assert all(math.isfinite(x) for rows in (n.verts,n.uv,n.normals) for row in rows for x in row)
            assert n.textures==[data['textures'].get(t.lower(),{}).get('alias',t) for t in m.textures]
        for base,lods in catalog.LOD_MODELS.items():
            if name in lods:
                assert item['alias']==data['models'][base]['alias']+name[len(base):]
                assert all(new.meshes[k].verts==m.verts and new.meshes[k].tris==m.tris for k,m in old.meshes.items())
        report['models'][name]={'alias':item['alias'],'original_geometry_rig_uv_preserved':True}
    for name,item in data['textures'].items():
        member=compiled_path(item['alias'],'.dds');expected.add(member)
        assert staged.read(member)==Path(item['output']).read_bytes()
        assert any(c.has_texture(item['alias']) for c in caches)
        size,old=pixels(item['source']);pngsize,png=pixels(Path(item['output']).with_suffix('.png'))
        newsize,new=pixels(item['output']);info=dds_info(item['output'])
        original_info=dds_info(item['source'])
        assert (info['mips'] or 1)==(original_info['mips'] or 1),('Mip count changed',name)
        if original_info['fourcc'] in ('DXT3','DXT5'):
            before=Path(item['source']).read_bytes();after=Path(item['output']).read_bytes()
            assert info['fourcc']==original_info['fourcc'],('Alpha codec changed',name)
            offset=128
            for level in range(info['mips'] or 1):
                w,h=max(1,info['width']>>level),max(1,info['height']>>level)
                for _ in range(((w+3)//4)*((h+3)//4)):
                    assert before[offset:offset+8]==after[offset:offset+8],('Alpha block changed',name,level)
                    offset+=16
            assert offset==len(before)==len(after),('DDS payload size changed',name)
        assert size==pngsize==newsize
        assert old[3::4]==png[3::4],('PNG alpha changed',name)
        for x,y,X,Y in paint.PROTECT.get(paint.family(name),[]):
            w,h=size
            left,right=max(0,math.ceil(x*w-.5)),min(w,math.ceil(X*w-.5))
            top,bottom=max(0,math.ceil(y*h-.5)),min(h,math.ceil(Y*h-.5))
            for row in range(top,bottom):
                a,b=(row*w+left)*4,(row*w+right)*4
                cutout=getattr(paint,'CLOTH_CUTOUT',{}).get(paint.family(name))
                if cutout is None:
                    assert old[a:b]==png[a:b],('Protected face/hair pixels changed',name,row)
                    continue
                for column in range(left,right):
                    i=(row*w+column)*4;red,green,blue_value=old[i:i+3]
                    xx,yy=(column+.5)/w,(row+.5)/h
                    blue=blue_value>red*1.03 and blue_value>green*.98 and (max(red,green,blue_value)-min(red,green,blue_value))/max(max(red,green,blue_value),.255)>.13
                    cloth=cutout[0]<=xx<cutout[2] and cutout[1]<=yy<cutout[3] and blue
                    if not cloth:assert old[i:i+4]==png[i:i+4],('Protected skin/hair changed',name,row,column)
        delta=max(abs(a-b) for a,b in zip(old[3::4],new[3::4]))
        if info['mips']<int(math.log2(max(size)))+1:
            report.setdefault('source_limitations',[]).append(name+': original incomplete mip chain retained '+str(info['mips']))
        report['textures'][name]={'size':size,'source_alpha_exact_in_png':True,'protected_skin_hair_exact_in_png':True,'dds_alpha_max_error':delta}
    for name,item in data['house'].items():
        member=compiled_path(item['alias'],Path(item['source']).suffix);expected.add(member)
        assert staged.read(member)==Path(item['source']).read_bytes()
        assert any(c.has_texture(item['alias']) for c in caches)
    replacements={name:item['alias'] for section in ('models','textures') for name,item in data[section].items()}
    for member in catalog.INI_MEMBERS:
        old=g.read(member).decode('latin1');new=staged.read(member).decode('latin1')
        def allowed(m):
            return re.sub(r'[\w.]+',lambda t:replacements.get(t[0].lower(),t[0]),m[0])
        want=re.sub(r'(?im)^\s*(?:Model|Texture|RandomTexture|UpgradeTexture)\s*=\s*[^\r\n;]*',allowed,old)
        if hasattr(catalog,'scoped_ini'):want=catalog.scoped_ini(member,old,replacements)
        assert want==new,('Nonvisual INI change',member)
    house=staged.read('data\\ini\\housecolor.ini')
    assert house.startswith(g.read('data\\ini\\housecolor.ini'))
    for name,item in data['house'].items():
        pattern=rb'BaseTexture\s*=\s*'+data['textures'][name]['alias'].encode()+rb'\s+HouseTexture\s*=\s*'+item['alias'].encode()
        assert re.search(pattern,house,re.I)
    for name,mask in data.get('shared_house',{}).items():
        assert mask in catalog.SHARED_HOUSE_TEXTURES
        for base,table in ((name,g.read('data\\ini\\housecolor.ini')),(data['textures'][name]['alias'],house)):
            pattern=rb'BaseTexture\s*=\s*'+re.escape(base.encode())+rb'\s+HouseTexture\s*=\s*'+re.escape(mask.encode())
            assert re.search(pattern,table,re.I),('Shared source mask mapping changed',name)
        assert any(c.has_texture(mask) for c in live_caches)
    assert members==expected,('Unexpected or missing package members',members^expected)
    report.update(status='FAIL' if report['issues'] else 'PASS',archive_members=len(members),nonvisual_ini_unchanged=True,
                  all_source_asset_names_unshipped=True,private_models_use_established_uncached_parse=True)
    (folder/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    assert not report['issues'],report['issues']
    return report



if __name__=='__main__':
    print(audit()['status'])
