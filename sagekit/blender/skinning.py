"""EA's two-bone skin vertices posed as the game poses them (numpy; sagekit/formats/w3dpose.skin).

A skin vertex is stored in its first bone's space; one with a second weight also has a position in
its second bone's space (VERTICES_2), and the game blends the two transformed points by weight
(VERTEX_INFLUENCES weights are percent). Weight (0, 100) rows exist (EA's Dwarven cart): such a
vertex follows its second bone only, though it is stored in its first's.
"""
import numpy as np

from ..formats import w3dpose as P


def blended(mesh):
    """(rows (N, 4), second positions (N, 3)) of a Mesh with two-bone vertices, else None (cached)."""
    if not hasattr(mesh, "blend"):
        sk = P.skin(mesh.bytes) if mesh.skinned else None
        mesh.blend = None
        if sk and any(r[3] for r in sk[0]):
            if sk[1] is None or len(sk[1]) != len(mesh.verts) or len(sk[0]) != len(mesh.verts):
                raise ValueError("%s: two-bone vertices without their second positions" % mesh.name)
            mesh.blend = (np.array(sk[0], int), np.array(sk[1], float))
    return mesh.blend


def follow(mesh, bones):
    """Per vertex the bone it follows most: `bones` (each vertex's first), a two-bone vertex's
    heavier one (the first on a tie)."""
    sk = blended(mesh)
    if sk is None:
        return bones
    return [b2 if w2 > w else b for b, b2, w, w2 in sk[0].tolist()]


def blend(mesh, pose, first, own_points=False):
    """World positions `first` (each vertex on its first bone under the pose) with the two-bone
    vertices blended in. own_points: the caller's points are not the mesh's vertices, so a mesh
    with two-bone vertices has no second positions for them (ValueError)."""
    sk = blended(mesh)
    if sk is None:
        return first
    if own_points:
        raise ValueError("%s: own points on a two-bone skin have no second positions" % mesh.name)
    rows, second = sk
    on = np.flatnonzero(rows[:, 3])
    mats = np.array(pose[0], float).reshape(-1, 3, 4)[rows[on, 1]]
    q = np.einsum("nij,nj->ni", mats[:, :, :3], second[on]) + mats[:, :, 3]
    out = np.array(first, float)
    out[on] = (out[on] * rows[on, 2:3] + q * rows[on, 3:4]) / 100.0
    return out
