"""Placing the Men of the West's and the Wizards' parts in every model of a subclass.

Their models re-exported EA's parts, so a part's vertices come in another order in each model and
the kit's whole-model fit (FIT_REFS) finds nothing. Here a part's vertices are matched by their
UVs (only UVs unique in both copies) and kit.geom.affine_fit must then be exact. Each group has
its own fit (the mounted rider's head, shield and sword moved differently), and the designs ride
abstract bones ("HEAD", "SPINE", "UARM_L", "UARM_R", "SHIELD", "HAND") named per skeleton.

The class lists every model in OWN_SPACE (the kit then places nothing) and wraps each design:
wrap(spec, group, fn) sets the Gear's placement (seat, then the group's fit) and bone names for
the model being built, then draws.
"""
from collections import Counter

from sagekit.formats import w3dpose as P
from sagekit.formats.w3d import W3DFile

from ..kit.geom import affine, affine_fit
from ..kit.models import folder, skeleton

_MEMO = {}


def points(w, sk, name):
    me = w.meshes[name]
    return [P.point(sk.rest[b], v) for v, b in zip(me.verts, P.influences(me.bytes))]


def uv_fit(a, b, name):
    """(3 x 4 matrix, largest error) mapping part `name` of a = (W3DFile, Skeleton) onto b's, or
    None when the copies share fewer than 8 unique UVs."""
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
    return affine_fit([pa[ia[k]] for k in common], [pb[ib[k]] for k in common])


def _load(spec, model):
    key = (spec.NAME, model)
    if key not in _MEMO:
        _MEMO[key] = W3DFile(str(folder(spec)[1] / (model + ".w3d"))), skeleton(spec, spec.SKELETONS[model])
    return _MEMO[key]


def model_of(spec, sk):
    """The spec's model whose skeleton `sk` is (by its bone names)."""
    for model, skl in spec.SKELETONS.items():
        if _load(spec, model)[1].names == sk.names:
            return model
    raise SystemExit("%s: no model of ours has this skeleton" % spec.NAME)


def place(spec, model, group):
    """design space -> `model`'s rest space for `group`: identity in the design model, else the
    first of spec.REFS[group] that fits exactly (None: identity, the same rest pose). A ref may be
    (part, tolerance) where EA re-modelled a part a little between models (the Shieldmaiden's
    creation-screen SHLD_01 is within 0.2 of an affine copy, and the only one held like hers)."""
    key = (spec.NAME, model, group)
    if key in _MEMO:
        return _MEMO[key]
    tries = spec.REFS.get(group)
    if model == spec.DESIGN or tries is None:
        fn = lambda p: tuple(p)
    else:
        X = None
        for ref in tries:
            ref, tol = ref if isinstance(ref, tuple) else (ref, 1e-3)
            got = uv_fit(_load(spec, spec.DESIGN), _load(spec, model), ref)
            if got and got[1] < tol:
                X = got[0]
                break
        if X is None:
            raise SystemExit("%s %s: none of EA's %s fits the design model exactly" % (model, group, list(tries)))
        fn = (lambda M: lambda p: affine(M, p))(X)
    _MEMO[key] = fn
    return fn


def wrap(spec, group, fn, seat=None):
    """The design `fn` drawn in the model the kit is building: seat (helmets), the group's fit,
    the model's bones."""
    def draw(m):
        model = model_of(spec, m.skeleton)
        to = place(spec, model, group)
        m.place = (lambda p: to(seat(p))) if seat else to
        m.bone_map = dict(spec.PER_SKELETON[spec.SKELETONS[model]], HAND=spec.HAND[spec.SKELETONS[model]])
        fn(m)
    draw.__doc__ = fn.__doc__
    return draw
