"""One palantir frame per faction: the APT edit (stdlib). docs/HUD.md, "One palantir per faction".

The game (game.dat 2.01) sends the palantir movie SetPalantirFrameState("_good" | "_goodSingle" |
"_evil" | "_evilSingle" | "_hide") from PlayerTemplate `Evil`, and SetPlayerFaction(<Side>) from
PlayerTemplate `Side`. EA's script turns the frame clip (PalantirFrame, character 105) to the state's
label and never uses the side. This edit, data only:

  PalantirExport  per look and kind (double: minimap and portrait; single: minimap alone) a new image,
                  shape and sprite (copies of EA's Good or Evil ones with the image swapped), exported
                  as PalantirFrame_<Look><Kind>; the .dat gets the images, the .ru files the shapes
  Palantir        imports of those sprites; per Side two frames on PalantirFrame, labelled _<Side> and
                  _<Side>Single, placing them exactly where EA places its own (Arnor shares Men's);
                  and an action appended to the root's first frame that wraps EA's two functions:
                  each stores its argument, calls EA's original, then sgApply(), which turns
                  PalantirFrame to _<Side>[Single] when the side is one of ours and the state is one of
                  the four shown states. Any other side or state leaves EA's frame (our Good/Evil pack).

Append-only: every new structure goes at the end of the file; old structures are never moved or
edited, only the 12 header words that point at the arrays that grew (characters, imports, exports,
frames) are repointed at grown copies. Nothing holding a pointer is shared (the game relocates each
pointer it reaches once). The bytecode uses only opcodes EA's own palantir.apt uses (checked).
"""
import struct

from .aptfile import Movie

SIG = 0x09876543
FRAME_CLIP = 105                                    # palantir.apt's PalantirFrame sprite
STATES = {("good", "double"): "_good", ("good", "single"): "_goodSingle",
          ("evil", "double"): "_evil", ("evil", "single"): "_evilSingle"}
EXPORTS = {("good", "double"): "PalantirFrame_GoodDouble", ("good", "single"): "PalantirFrame_GoodSingle",
           ("evil", "double"): "PalantirFrame_EvilDouble", ("evil", "single"): "PalantirFrame_EvilSingle"}
KINDS = ("double", "single")
FN_FLAGS = 0x006A0004                               # EA's: preload _root in r1, 4 registers


class Blob:
    def __init__(self, data):
        self.b = bytearray(data)

    def add(self, data):
        while len(self.b) % 4:
            self.b.append(0)
        at = len(self.b)
        self.b += data
        return at

    def s(self, text):                              # a fresh string, never shared
        return self.add(text.encode("latin-1") + b"\0")

    def u32s(self, vals):
        return self.add(struct.pack("<%dI" % len(vals), *vals) if vals else b"\0\0\0\0")

    def put(self, off, fmt, *v):
        struct.pack_into(fmt, self.b, off, *v)


def place(ch, depth, flags, mat, tx, ty, ratio=0.0):
    return struct.pack("<IIii4f2fIIfIiI", 3, flags, depth, ch, *mat, tx, ty, 0xFFFFFFFF, 0, ratio, 0, -1, 0)


def cap(name):
    return name[0].upper() + name[1:]


def base_shape(m, ru, side, kind):
    """(shape character, image id, shape bounds) EA's side/kind export draws."""
    spr = dict(m.exports())[EXPORTS[side, kind]]
    shape = [v["ch"] for items in m.frames(spr) for k, v, _ in items if k == "place"][0]
    p = m.chars()[shape]
    bounds = struct.unpack_from("<4f", m.d, p + 8)
    text = ru("palantirexport_geometry\\%d.ru" % shape).decode("latin-1")
    imgs = {int(line.split(":")[5]) for line in text.splitlines() if line.startswith("s t")}
    if len(imgs) != 1:
        raise ValueError("EA's %s %s shape draws images %s" % (side, kind, sorted(imgs)))
    return shape, imgs.pop(), bounds


def build_export(apt, looks):
    """looks: [(look, side)]. Returns (members {name: bytes}, images {image id: (look, kind, EA's image)},
    exports {(look, kind): export name})."""
    m = Movie(apt.read("palantirexport.apt"), apt.read("palantirexport.const"))
    b = Blob(m.d)
    chars, exports = m.chars(), m.exports()
    dat = apt.read("palantirexport.dat").decode("latin-1").rstrip("\r\n").split("\r\n")
    sizes = {int(x.split("=")[0]): x.split("=")[1] for x in dat if "=" in x}
    members, images, names = {}, {}, {}
    for look, side in looks:
        for kind in KINDS:
            shape, img, bounds = base_shape(m, apt.read, side, kind)
            i_img, i_shape, i_sprite = len(chars), len(chars) + 1, len(chars) + 2
            chars.append(b.add(struct.pack("<III", 7, SIG, i_img)))
            chars.append(b.add(struct.pack("<II4fI", 1, SIG, *bounds, i_shape)))
            items = b.u32s([b.add(place(i_shape, 1, 6, (1, 0, 0, 1), 0, 0))])
            frame = b.add(struct.pack("<II", 1, items))
            chars.append(b.add(struct.pack("<IIIII", 5, SIG, 1, frame, 0)))
            name = "PalantirFrame_%s%s" % (cap(look), cap(kind))
            exports.append((name, i_sprite))
            dat.append("%d=%s" % (i_img, sizes[img]))
            text = apt.read("palantirexport_geometry\\%d.ru" % shape).decode("latin-1")
            lines = []
            for line in text.split("\n"):
                if line.startswith("s t"):
                    f = line.split(":")
                    f[5] = str(i_img)                   # s tc:r:g:b:a:IMAGE:a:b:c:d:tx:ty
                    line = ":".join(f)
                lines.append(line)
            members["palantirexport_geometry\\%d.ru" % i_shape] = "\n".join(lines).encode("latin-1")
            images[i_img] = (look, kind, img)
            names[look, kind] = name
    exp = b.add(b"".join(struct.pack("<II", b.s(n), c) for n, c in exports))
    b.put(m.root + 5 * 4, "<II", len(chars), b.u32s(chars))
    b.put(m.root + 12 * 4, "<II", len(exports), exp)
    members["palantirexport.apt"] = bytes(b.b)
    members["palantirexport.dat"] = ("\r\n".join(dat) + "\r\n").encode("latin-1")
    return members, images, names


class Asm:
    """APT ActionScript, the opcodes EA's palantir.apt uses. Operands of the multi-byte opcodes pad
    to 4 bytes; the action is placed 4-aligned, so padding is relative to its start."""

    def __init__(self, blob, base, pool):
        self.b, self.base, self.pool, self.code = blob, base, pool, bytearray()

    def op(self, o, *payload):
        self.code.append(o)
        for p in payload:
            if isinstance(p, tuple):
                while len(self.code) % 4:
                    self.code.append(0)
                self.code += struct.pack(p[0], *p[1])
            else:
                self.code.append(p)

    def c(self, name):                              # PushConst <pool index>
        self.op(0xA2, self.pool.index(name))

    def reg(self, r):                               # PushData [register r]
        self.op(0x96, ("<II", (1, self.b.u32s([self.base["reg%d" % r]]))))

    def member(self, name):                         # GetNamedMember
        self.op(0xAF, self.pool.index(name))

    def branch(self, o):
        self.op(o, ("<i", (0,)))
        return len(self.code)

    def land(self, at):
        struct.pack_into("<i", self.code, at - 4, len(self.code) - at)

    def function(self, name, arg, body):
        """DefineFunction2 name(arg) with EA's flags: r1 = _root, r2 = the argument, r3 free."""
        args = self.b.add(struct.pack("<II", 2, self.b.s(arg))) if arg else self.b.add(b"\0" * 8)
        self.op(0x8E, ("<IIIII", (self.b.s(name), 1 if arg else 0, FN_FLAGS, args, 0)),
                ("<II", (0x98765432, 0x12345678)))
        at = len(self.code)
        body()
        struct.pack_into("<I", self.code, at - 12, len(self.code) - at)


def names_for(sides):
    return ["SetPalantirFrameState", "SetPlayerFaction", "sgEAState", "sgEAFaction", "sgState",
            "sgFaction", "sgApply", "PalantirFrame", "gotoAndPlay", "_", "Single",
            "_good", "_evil", "_goodSingle", "_evilSingle", "_root"] + list(sides)


def script(a, sides):
    """The appended root action (see the module's docstring)."""
    pool = a.pool
    a.op(0x88, ("<II", (len(pool), a.b.u32s([a.base[x] for x in pool]))))
    for new, old in (("sgEAState", "SetPalantirFrameState"), ("sgEAFaction", "SetPlayerFaction")):
        a.op(0xAE, pool.index("_root"))
        a.c(new)
        a.op(0xAE, pool.index("_root"))
        a.member(old)
        a.op(0x4F)                                  # _root[new] = _root[old]

    def wrap(var, orig):
        def body():
            a.reg(1), a.c(var), a.reg(2), a.op(0x4F)                    # _root[var] = arg
            a.reg(2), a.op(0x5A), a.reg(1), a.op(0xB2, pool.index(orig))  # _root[orig](arg)
            a.op(0x59), a.reg(1), a.op(0xB2, pool.index("sgApply"))    # _root.sgApply()
        return body

    a.function("SetPalantirFrameState", "state", wrap("sgState", "sgEAState"))
    a.function("SetPlayerFaction", "faction", wrap("sgFaction", "sgEAFaction"))

    def apply_body():
        out, ok = [], []
        for side in sides:                          # only sides that have frames
            a.reg(1), a.member("sgFaction"), a.c(side), a.op(0x49)
            ok.append(a.branch(0x9D))
        out.append(a.branch(0x99))
        for j in ok:
            a.land(j)
        a.c("_"), a.reg(1), a.member("sgFaction"), a.op(0x47)          # r3 = "_" + faction
        a.op(0x87, ("<I", (3,))), a.op(0x17)
        dbl, sgl = [], []
        for st in ("_good", "_evil"):
            a.reg(1), a.member("sgState"), a.c(st), a.op(0x49)
            dbl.append(a.branch(0x9D))
        for st in ("_goodSingle", "_evilSingle"):
            a.reg(1), a.member("sgState"), a.c(st), a.op(0x49)
            sgl.append(a.branch(0x9D))
        out.append(a.branch(0x99))                  # _hide or anything else: EA's frame stays
        for j in sgl:
            a.land(j)
        a.reg(3), a.c("Single"), a.op(0x47), a.op(0x87, ("<I", (3,))), a.op(0x17)
        for j in dbl:
            a.land(j)
        a.reg(3), a.op(0x5A), a.reg(1), a.member("PalantirFrame"), a.op(0xB2, pool.index("gotoAndPlay"))
        for j in out:
            a.land(j)

    a.function("sgApply", None, apply_body)
    a.op(0x00)


def build_const(c, extra):
    """EA's .const with `extra` items [(type, string or register)] appended; EA's keep their indices."""
    n, io = struct.unpack_from("<II", c, 0x18)
    items = [struct.unpack_from("<II", c, io + 8 * i) for i in range(n)]
    strs = [c[v:c.index(b"\0", v)] if t == 1 else None for t, v in items]
    for t, v in extra:
        items.append((t, v if t != 1 else 0))
        strs.append(v.encode("latin-1") if t == 1 else None)
    out = bytearray(c[:0x14]) + struct.pack("<III", struct.unpack_from("<I", c, 0x14)[0], len(items), 0x20)
    table = len(out)
    out += b"\0" * (8 * len(items))
    for i, ((t, v), s) in enumerate(zip(items, strs)):
        if t == 1:
            while len(out) % 4:
                out.append(0)
            v = len(out)
            out += s + b"\0"
        struct.pack_into("<II", out, table + 8 * i, t, v)
    return bytes(out)


def build_palantir(apt, frames):
    """frames: {Side: (look, side)}; the export names come from build_export. Returns members."""
    m = Movie(apt.read("palantir.apt"), apt.read("palantir.const"))
    c = apt.read("palantir.const")
    b = Blob(m.d)
    chars = m.chars()
    imports = [struct.unpack_from("<4I", m.d, m.h["imports"] + 16 * i) for i in range(m.h["nimports"])]
    ea_place = {}
    for items in m.frames(FRAME_CLIP):
        labels = [v for k, v, _ in items if k == "label"]
        for k, v, ip in items:
            if k == "place" and labels:
                ea_place[labels[0]] = m.d[ip:ip + 64]
    imported = {}
    for side_name, (look, side) in frames.items():
        for kind in KINDS:
            if (look, kind) not in imported:
                cid = len(chars)
                chars.append(0)
                imports.append((b.s("PalantirExport"), b.s("PalantirFrame_%s%s" % (cap(look), cap(kind))), cid, 0))
                imported[look, kind] = cid
    impp = b.add(b"".join(struct.pack("<4I", *i) for i in imports))
    nf, fp = m.frames_of(FRAME_CLIP)
    clip = [struct.unpack_from("<II", m.d, fp + 8 * i) for i in range(nf)]
    labels = {}
    for side_name, (look, side) in frames.items():
        for kind in KINDS:
            label = "_" + side_name + ("Single" if kind == "single" else "")
            idx = len(clip)
            rm = b.add(struct.pack("<II", 4, 1))
            lb = b.add(struct.pack("<IIII", 2, b.s(label), 0x70000, idx))
            pl = bytearray(ea_place[STATES[side, kind]])
            struct.pack_into("<i", pl, 12, imported[look, kind])
            clip.append((3, b.u32s([rm, lb, b.add(bytes(pl))])))
            stop = b.add(b"\x07\x00\x00\x00")                       # Stop, End
            clip.append((1, b.u32s([b.add(struct.pack("<II", 1, stop))])))
            labels[label] = (idx, imported[look, kind])
    b.put(m.chars()[FRAME_CLIP] + 8, "<II", len(clip), b.add(b"".join(struct.pack("<II", *f) for f in clip)))
    sides = list(frames)
    pool = names_for(sides)
    n0 = struct.unpack_from("<I", c, 0x18)[0]
    base = {nm: n0 + i for i, nm in enumerate(pool)}
    for r in (1, 2, 3):
        base["reg%d" % r] = n0 + len(pool) + r - 1
    const = build_const(c, [(1, nm) for nm in pool] + [(4, r) for r in (1, 2, 3)])
    a = Asm(b, base, pool)
    script(a, sides)
    act = b.add(bytes(a.code))
    cnt, items = struct.unpack_from("<II", m.d, m.h["frames"])
    old = list(struct.unpack_from("<%dI" % cnt, m.d, items))
    b.put(m.h["frames"], "<II", cnt + 1, b.u32s(old + [b.add(struct.pack("<II", 1, act))]))
    b.put(m.root + 5 * 4, "<II", len(chars), b.u32s(chars))
    b.put(m.root + 10 * 4, "<II", len(imports), impp)
    return {"palantir.apt": bytes(b.b), "palantir.const": const}, labels, act


def build(apt, factions):
    """factions: assets.hud.factions.FACTIONS. ({member: bytes}, {image id: (look, kind, EA's image)},
    {label: (frame, character)}, the script's address)."""
    looks = [(name, f["side"]) for name, f in factions.items()]
    members, images, _ = build_export(apt, looks)
    frames = {s: (name, f["side"]) for name, f in factions.items() for s in f["sides"]}
    pal, labels, act = build_palantir(apt, frames)
    members.update(pal)
    return members, images, labels, act
