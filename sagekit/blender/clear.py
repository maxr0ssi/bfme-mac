"""Building.clear applied to a Blender mesh (the specs: sagekit/clear.py)."""
import bmesh

from ..clear import select


def apply(obj, specs, world=False):
    """Delete the faces of a mesh object the specs select, with the edges and vertices only they
    used; -> how many. world: the specs are in world coordinates (a `world_space` recipe)."""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    m = obj.matrix_world if world else None
    verts = [tuple(m @ v.co) if m else tuple(v.co) for v in bm.verts]
    faces = list(bm.faces)
    gone = select(specs, verts, [[v.index for v in f.verts] for f in faces])
    if len(gone) == len(faces):                 # everything: loose vertices and edges go too
        bmesh.ops.delete(bm, geom=list(bm.verts), context="VERTS")
    else:
        bmesh.ops.delete(bm, geom=[faces[i] for i in sorted(gone)], context="FACES")
    bm.to_mesh(me)
    bm.free()
    me.update()
    return len(gone)
