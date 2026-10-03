"""Placing the Archers' parts (both archer folders). Every part is drawn once, in the Elven Archer's
creation-screen rest space (CHAR_EL_C_SKN on CHAR_AR_C_SKL: +X front, +Y the archer's left, +Z
up), and mapped into each of the four models by REGION.

EA's archer models share no part with identical vertices (each model's parts were refitted by
hand; the creation-screen bodies are taller and the female archer slighter), so the kit's exact
fit does not apply (docs/CAH.md). A part names the region it is drawn in (head, back, arm, bow)
and that region's map places it:

- head, back, arm: the per-axis scale and offset that best maps EA's own matching parts' boxes
  (least squares over their min and max), measured from EA's files at build time;
- bow: exact through the bow bone, bone-local: EA's bows sit identically in the Elven Archer's two
  bow bones; the female archer's bow bones hold the bow along other local axes (LOCAL, read off
  EA's BOW_03/04/05 boxes).

The class's design uses OWN_SPACE (kit/models.py): the kit hands each part the identity and the
part's wrapper (wrap) sets the model's maps and bone names on the Gear itself.
"""
import functools

from sagekit.formats import w3dpose as P
from sagekit.formats.w3d import W3DFile

# the bow bone's local axes per model, as rows in the Elven Archer's frame (bow along z, belly -x)
LOCAL = {"el_c": ((1, 0, 0), (0, 1, 0), (0, 0, 1)), "el_u": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
         "fe_u": ((0, 0, 1), (0, 1, 0), (-1, 0, 0)),     # bow along x, belly +z
         "fe_c": ((1, 0, 0), (0, 0, 1), (0, -1, 0))}     # bow along y, belly -x
BOW_BONE = {"el_c": "BOWBONE", "el_u": "B_HAND_L", "fe_c": "B_HANDL", "fe_u": "B_HAND_L"}
FILES = {"el_c": ("char_el_c_skn", "char_ar_c_skl", "OBJCHAR_EL"), "el_u": ("char_el_u_skn", "char_ar_u_skl", "LOWLOD"),
         "fe_c": ("char_fe_c_skn", "char_fe_c_skl", "CHAR_FE1"), "fe_u": ("char_fe_u_skn", "char_fe_u_skl", "CHAR_FE1")}
# design bone -> bone in each model
BONES = {"el_c": {}, "fe_c": {"BOWBONE": "B_HANDL"},
         "el_u": {"B_HEAD": "BAT_HEAD", "BAT_SPINE2": "BAT_RIBS", "BAT_SPINE1": "BAT_RIBS", "B_CLAVL": "BAT_RIBS",
                  "B_CLAVR": "BAT_RIBS", "B_PELVIS": "BAT_RIBS", "BOWBONE": "B_HAND_L"},
         "fe_u": {"B_HEAD": "BAT_HEAD", "BAT_SPINE2": "BAT_RIBS", "BAT_SPINE1": "BAT_RIBS", "B_CLAVL": "BAT_RIBS",
                  "B_CLAVR": "BAT_RIBS", "B_PELVIS": "B_WAIST", "BOWBONE": "B_HAND_L"}}
TORSO_C = {"BAT_SPINE1", "BAT_SPINE2", "B_CLAVL", "B_CLAVR", "B_PELVIS"}
# per region and model pair: [(EA meshes, bones or None)] whose boxes fit the map
REFS = {
    ("el_c", "el_u"): {"head": [(["HLMT_01"], None), (["HLMT_02"], None)],
                       "back": [(["SLDR_01"], None), (["SLDR_04"], None), (["QUIVR"], None), (["@body"], TORSO_C)],
                       "arm": [(["GNLT_04"], None), (["GNLT_01"], None)]},
    ("fe_c", "fe_u"): {"head": [(["HLMT_05"], None), (["HAIR"], None), (["HLMT_03"], None), (["HLMT_04"], None)],
                       "back": [(["SLDR_01"], None), (["SLDR_06"], None), (["QUIVR"], None), (["@body"], TORSO_C)],
                       "arm": [(["GNLT_07"], None), (["GNLT_01"], None)]},
    ("el_c", "fe_c"): {"head": [(["@body"], {"B_HEAD"})],
                       "back": [(["SLDR_01"], None), (["SLDR_02"], None), (["QUIVR"], None), (["@body"], TORSO_C)],
                       "arm": [(["GNLT_01"], None), (["GNLT_02"], None)]},
}
GAME_BONES = {"BAT_SPINE1": "BAT_RIBS", "BAT_SPINE2": "BAT_RIBS", "B_CLAVL": "BAT_RIBS", "B_CLAVR": "BAT_RIBS",
              "B_HEAD": "BAT_HEAD"}
UNIFORM = {"head"}          # helmets keep their proportions: one scale, the mean of the three


def kind_of(sk):
    names = set(sk.names)
    return "el_c" if "BOWBONE" in names else "fe_c" if "B_HAIR01" in names else "fe_u" if "B_WAIST" in names else "el_u"


def box(w, sk, names, bones=None):
    """(min, max) of EA meshes `names` in rest space (only vertices on `bones` if given)."""
    pts = []
    for n in names:
        me = w.meshes[n]
        for v, b in zip(me.verts, P.influences(me.bytes)):
            if bones is None or sk.names[b] in bones:
                pts.append(P.point(sk.rest[b], v))
    return [min(p[k] for p in pts) for k in range(3)], [max(p[k] for p in pts) for k in range(3)]


def box_fit(src, dst, uniform=False):
    """Per-axis (scale, offset) mapping boxes `src` onto boxes `dst` (least squares over every
    min and max); uniform: one scale (the mean), offsets refitted."""
    fit = []
    for k in range(3):
        xs = [b[i][k] for b in src for i in (0, 1)]
        ys = [b[i][k] for b in dst for i in (0, 1)]
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        var = sum((x - mx) ** 2 for x in xs)
        s = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / var if var > 1e-9 else 1.0
        fit.append([s, my - s * mx, mx, my])
    if uniform:
        s = sum(f[0] for f in fit) / 3
        fit = [[s, my - s * mx, mx, my] for _, _, mx, my in fit]
    return [(s, t) for s, t, _, _ in fit]


def axis_map(fit):
    return lambda p: tuple(s * x + t for x, (s, t) in zip(p, fit))


def bone_map(rest_from, local_from, rest_to, local_to):
    """A point riding bone rest_from -> the same bow-frame spot on rest_to (local axes as rows in
    the Elven Archer's bow frame)."""
    inv = P.invert(rest_from)

    def f(p):
        q = P.point(inv, p)
        e = [sum(local_from[r][i] * q[r] for r in range(3)) for i in range(3)]    # into the el frame
        q = [sum(local_to[r][i] * e[i] for i in range(3)) for r in range(3)]
        return tuple(P.point(rest_to, q))
    return f


def compose(*fs):
    def f(p):
        for g in fs:
            p = g(p)
        return p
    return f


class Space:
    """The four archer models' sources (from a class's src folder): maps and bone names."""

    def __init__(self, src):
        self.src = src

    @functools.lru_cache(None)
    def model(self, kind):
        m, s, body = FILES[kind]
        return W3DFile(str(self.src / (m + ".w3d"))), P.Skeleton((self.src / (s + ".w3d")).read_bytes()), body

    def _boxes(self, kind, refs, game=False):
        w, sk, body = self.model(kind)
        out = []
        for names, bones in refs:
            names = [body if n == "@body" else n for n in names]
            if bones and game:
                bones = {GAME_BONES.get(b, b) for b in bones} | ({"B_WAIST"} if kind == "fe_u" else {"ROOT DUMMY"})
            out.append(box(w, sk, names, bones))
        return out

    @functools.lru_cache(None)
    def step(self, a, b, region):
        """The map from model a to model b for `region`."""
        if region == "bow":
            wa, ka, _ = self.model(a)
            wb, kb, _ = self.model(b)
            return bone_map(ka.rest[ka.names.index(BOW_BONE[a])], LOCAL[a], kb.rest[kb.names.index(BOW_BONE[b])], LOCAL[b])
        refs = REFS[(a, b)][region]
        return axis_map(box_fit(self._boxes(a, refs), self._boxes(b, refs, game=b.endswith("_u")), region in UNIFORM))

    @functools.lru_cache(None)
    def to(self, kind, region):
        """The map from the design space (el_c) into model `kind`."""
        if kind == "el_c":
            return lambda p: tuple(p)
        if kind == "el_u":
            return self.step("el_c", "el_u", region)
        if kind == "fe_c":
            return self.step("el_c", "fe_c", region)
        return compose(self.step("el_c", "fe_c", region), self.step("fe_c", "fe_u", region))


def region(m, name):
    """Draw what follows in region `name` (head, back, arm, bow) of the model being built."""
    m.place = m.space.to(m.kind, name)


def wrap(fn, space, default):
    """The kit calls fn(gear); set the gear's model maps and bone names first."""
    @functools.wraps(fn)
    def f(m):
        m.kind, m.space = kind_of(m.skeleton), space
        m.bone_map = dict(BONES[m.kind])
        region(m, default)
        fn(m)
    return f
