"""Exact maps between a class's models when EA's shared parts list their vertices in another order
(the Men of the West and the Wizards: each model of a subclass re-exported its parts). Vertices
are matched by their UVs (only UVs unique in both copies), then kit.geom.affine_fit must be exact.

A class whose models need a map per group gives design.place = places(spec, REFS) with
REFS = {group: (EA parts to try, in order)} (the first exact fit wins; None = identity, the same
rest pose) and kit/models.py calls it per model and group.
"""
from collections import Counter

from sagekit.formats import w3dpose as P
from sagekit.formats.w3d import W3DFile

from .geom import affine, affine_fit


def points(w, sk, name):
    me = w.meshes[name]
    return [P.point(sk.rest[b], v) for v, b in zip(me.verts, P.influences(me.bytes))]


def uv_fit(a, b, name):
    """(3 x 4 matrix, largest error, matched vertices) mapping part `name` of a = (W3DFile,
    Skeleton) onto b's, or None when the two copies share too few unique UVs."""
    (wa, ska), (wb, skb) = a, b
    ma, mb = wa.meshes.get(name), wb.meshes.get(name)
    if not (ma and mb and ma.uv and mb.uv and ma.skinned and mb.skinned):
        return None
    ka = [tuple(round(x, 4) for x in u) for u in ma.uv]
    kb = [tuple(round(x, 4) for x in u) for u in mb.uv]
    ca, cb = Counter(ka), Counter(kb)
    common = [k for k in ca if ca[k] == 1 and cb.get(k) == 1]
    if len(common) < 8:
        return None
    pa, pb = points(wa, ska, name), points(wb, skb, name)
    ia, ib = {k: i for i, k in enumerate(ka)}, {k: i for i, k in enumerate(kb)}
    X, err = affine_fit([pa[ia[k]] for k in common], [pb[ib[k]] for k in common])
    return X, err, len(common)


def places(spec, refs):
    """spec.place for kit/models.py: place(model, group) -> design space -> model's rest space."""
    from .models import folder, skeleton
    memo = {}

    def load(model):
        return W3DFile(str(folder(spec)[1] / (model + ".w3d"))), skeleton(spec, spec.SKELETONS[model])

    def place(model, group):
        if (model, group) in memo:
            return memo[(model, group)]
        tries = refs.get(group, refs.get(None))
        if tries is None:
            fn = lambda p: tuple(p)
        else:
            a, b = load(spec.DESIGN), load(model)
            X = None
            for ref in tries:
                got = uv_fit(a, b, ref)
                if got and got[1] < 1e-3:
                    X = got[0]
                    break
            if X is None:
                raise SystemExit("%s %s: none of EA's %s fits the design model exactly" % (model, group, list(tries)))
            fn = (lambda M: lambda p: affine(M, p))(X)
        memo[(model, group)] = fn
        return fn
    return place
