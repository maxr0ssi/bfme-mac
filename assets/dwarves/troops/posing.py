"""Troop-only two-bone skinning for offline previews and animation preservation checks.

OpenSAGE's local mesh_export.py writes each position in its influence bone's inverse
rest frame; VertexInfluence.read stores primary/secondary uint16 weights divided by 100.
The world point is the weighted sum of those independently transformed positions.
Run in Blender: ``blender -b --python assets/dwarves/troops/posing.py``.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))

import numpy as np

from sagekit.blender.lifecycle import Model as BaseModel
from sagekit.formats.w3d import VERTEX_INFLUENCES, VERTICES, NORMALS, chunks

VERTICES_2, NORMALS_2 = 0xC00, 0xC01


def skin_channels(mesh):
    return {t:mesh.bytes[o+8:o+8+s] for t,o,s,_ in chunks(mesh.bytes,8,len(mesh.bytes))
            if t in (VERTICES,NORMALS,VERTEX_INFLUENCES,VERTICES_2,NORMALS_2)}


def assert_original_skin(before,after):
    """Exact inputs prove original blended positions/normals equal for every bone pose."""
    old,new=skin_channels(before),skin_channels(after)
    for tag,raw in old.items():
        if tag==NORMALS and VERTICES_2 not in old:continue
        assert tag in new and new[tag][:len(raw)]==raw,(before.name,hex(tag),'skin channel')
    if VERTICES_2 in old or NORMALS_2 in old:
        assert after.bytes==before.bytes,(before.name,'blended body must remain byte-exact')


def blend_world(primary,secondary,influences,matrices):
    """Blend only vertices with an active second weight; rigid vertices stay exact."""
    active=np.flatnonzero(influences[:,3])
    out=primary.copy()
    if len(active):
        rows=influences[active]
        mats=matrices[rows[:,1]]
        second=np.einsum('nij,nj->ni',mats[:,:,:3],secondary[active])+mats[:,:,3]
        out[active]=primary[active]*(rows[:,2:3]/100)+second*(rows[:,3:4]/100)
    return out


class Model(BaseModel):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.secondary={}
        for name,mesh in self.w3d.meshes.items():
            channels=skin_channels(mesh)
            raw=channels.get(VERTEX_INFLUENCES)
            if not mesh.skinned or raw is None:continue
            inf=np.asarray(list(struct.iter_unpack('<4H',raw)),dtype=int)
            assert len(inf)==len(mesh.verts),(name,'influence count')
            if not np.any(inf[:,3]):continue
            assert VERTICES_2 in channels and NORMALS_2 in channels,(name,'missing secondary skin')
            second=np.asarray(list(struct.iter_unpack('<3f',channels[VERTICES_2])),dtype=float)
            assert second.shape==(len(mesh.verts),3),(name,'secondary count')
            assert len(channels[NORMALS_2])==len(mesh.verts)*12,(name,'secondary normals')
            active=inf[:,3]>0
            assert np.all(inf[active,2:].sum(axis=1)==100),(name,'skin weights')
            assert np.all(inf[active,:2]<len(self.skel.pivots)),(name,'secondary bone')
            assert np.isfinite(second).all(),name
            self.secondary[name]=(second,inf)

    def world(self,name,pose,verts=None):
        primary=self.primary_world(name,pose,verts)  # (the base blends too: one blend only)
        if name not in self.secondary:return primary
        if verts is not None:raise ValueError('Custom vertices require their own secondary coordinates')
        second,inf=self.secondary[name]
        return blend_world(primary,second,inf,np.asarray(pose[0],dtype=float).reshape(-1,3,4))


def check():
    # Different local coordinates and bones: second rotates +90 degrees about Z then
    # translates +8 in X. Its local (2,0,0) becomes (8,2,0); first is (2,0,0).
    matrices=np.asarray([[[1,0,0,0],[0,1,0,0],[0,0,1,0]],
                         [[0,-1,0,8],[1,0,0,0],[0,0,1,0]]],dtype=float)
    first=np.asarray([[2,0,0],[3,4,5],[2,0,0]],dtype=float)
    second=np.asarray([[2,0,0],[999,999,999],[2,0,0]],dtype=float)
    inf=np.asarray([[0,1,25,75],[0,0,100,0],[0,1,50,50]])
    result=blend_world(first,second,inf,matrices)
    assert np.array_equal(result,np.asarray([[6.5,1.5,0],[3,4,5],[5,1,0]]))
    assert np.array_equal(first,np.asarray([[2,0,0],[3,4,5],[2,0,0]]))
    print('PASS: two-bone weighted world positions and exact rigid vertices')


if __name__=='__main__':check()
