"""Checks of the per-faction palantir without the game (stdlib). docs/HUD.md, "One palantir per faction".

  structure  the edited .apt keeps EA's bytes except the 12 header words it repoints; every action of
             the movie (EA's 152 and ours) decodes to its End with consistent function sizes; ours
             uses only opcodes EA's palantir.apt uses, only constant items that exist, and every
             pointer it holds lies inside the file
  references every import resolves to an export of the shipped PalantirExport, every new label's
             character is an import, every export a sprite placing a shape whose .ru draws one image
             the .dat declares and the archive ships at twice EA's size, with the matrix doubled
  trace      our bytecode run in a small interpreter of exactly those opcodes, the game's calls
             replayed (side first or state first, single and double, _hide), EA's two originals as
             stubs; then the label PalantirFrame ends on is followed to the texture it draws
"""
import struct

from .apt import matrices
from .aptfile import Movie, actions, decode
from .factionapt import FRAME_CLIP, STATES

EA_STATES = ("_hide", "_good", "_goodSingle", "_evil", "_evilSingle")


class Clip:
    def __init__(self):
        self.label, self.calls = None, []

    def gotoAndPlay(self, label):
        self.label = label
        self.calls.append(label)


class VM:
    """The opcodes our appended action uses, with ActionScript's semantics as EA's code relies on."""

    def __init__(self, movie, start):
        self.m, self.start = movie, start
        self.frame = Clip()
        self.icon = []
        self.root = {"PalantirFrame": self.frame,
                     "SetPalantirFrameState": lambda s: self.frame.gotoAndPlay(s),
                     "SetPlayerFaction": lambda f: self.icon.append(f)}
        self.ins = {a: (op, arg) for a, op, _, arg in decode(movie.d, start)}
        self.order = sorted(self.ins)

    def item(self, i):
        t, v = self.m.const.items[i]
        return ("reg", v) if t == 4 else self.m.const.value(i)

    def run(self, pc, end, regs, pool):
        stack = []
        while pc < end:
            op, arg = self.ins[pc]
            nxt = self.order[self.order.index(pc) + 1] if pc != self.order[-1] else end
            if op == 0x00:
                return pool
            elif op == 0x88:
                pool = [self.m.const.value(i) for i in arg]
            elif op == 0xA2:
                stack.append(pool[arg])
            elif op == 0xAE:
                if pool[arg] != "_root":
                    raise ValueError("variable %s" % pool[arg])
                stack.append(self.root)
            elif op == 0xAF:
                o = stack.pop()
                stack.append(o.get(pool[arg]) if isinstance(o, dict) else getattr(o, pool[arg], None))
            elif op == 0x96:
                for i in arg:
                    v = self.item(i)
                    stack.append(regs[v[1]] if isinstance(v, tuple) else v)
            elif op == 0x4F:
                v, k, o = stack.pop(), stack.pop(), stack.pop()
                o[k] = v
            elif op in (0x59, 0x5A):
                stack.append(op - 0x59)
            elif op == 0xB2:
                o, n = stack.pop(), stack.pop()
                args = [stack.pop() for _ in range(n)]
                f = o.get(pool[arg]) if isinstance(o, dict) else getattr(o, pool[arg], None)
                if f is not None:
                    self.call(f, args)
            elif op == 0x49:
                b, a = stack.pop(), stack.pop()
                stack.append(a == b)
            elif op == 0x47:
                b, a = stack.pop(), stack.pop()
                stack.append(str(a) + str(b) if isinstance(a, str) or isinstance(b, str) else a + b)
            elif op == 0x87:
                regs[arg] = stack[-1]
            elif op == 0x17:
                stack.pop()
            elif op == 0x9D:
                if stack.pop():
                    nxt = arg
            elif op == 0x99:
                nxt = arg
            elif op == 0x8E:
                self.root[arg["name"]] = ("fn", arg, pool)
                nxt = arg["body"] + arg["size"]
            else:
                raise ValueError("opcode %#x outside the interpreter" % op)
            pc = nxt
        return pool

    def call(self, f, args):
        if callable(f):
            return f(*args)
        _, fn, pool = f
        regs = [None] * (fn["flags"] & 0xFFFF)
        if fn["flags"] >> 16 & 0x40:
            regs[1] = self.root
        for (r, _), v in zip(fn["args"], args):
            regs[r] = v
        self.run(fn["body"], fn["body"] + fn["size"], regs, pool)

    def boot(self):
        self.run(self.start, 1 << 40, [None] * 4, [])
        return self

    def game(self, name, *args):
        self.call(self.root[name], list(args))


def header_words(ea, ours):
    return [o for o in range(0, len(ea), 4) if ea[o:o + 4] != ours[o:o + 4]]


def structure(ea_apt, ea_const, apt, const, act, say):
    ea, m = Movie(ea_apt, ea_const), Movie(apt, const)
    diff = header_words(ea_apt, apt)
    say(len(diff) <= 12 and all(o in range(ea.root, ea.root + 60) or o in (m.chars()[FRAME_CLIP] + 8,
                                                                           m.chars()[FRAME_CLIP] + 12)
                               or o in (ea.h["frames"], ea.h["frames"] + 4) for o in diff),
        "palantir.apt: EA's bytes kept but %d header words (%s)" % (len(diff), ", ".join("%#x" % o for o in diff)))
    ea_ops = {op for _, _, a in actions(ea) for _, op, _, _ in decode(ea.d, a)}
    n, stops = 0, 0
    for cid, f, a in actions(m):
        ins = decode(m.d, a)
        n += 1
        stops += cid == FRAME_CLIP and f >= len(ea.frames(FRAME_CLIP)) and [x[1] for x in ins] == [0x07, 0x00]
    labels = sum(k == "label" for items in m.frames(FRAME_CLIP)[len(ea.frames(FRAME_CLIP)):] for k, _, _ in items)
    say(n == len(actions(ea)) + 1 + labels and stops == labels,
        "palantir.apt: all %d actions decode to their End (EA's %d, our script, %d Stops after our labels)" % (
            n, len(actions(ea)), stops))
    ours = decode(m.d, act)
    new = {op for _, op, _, _ in ours} - ea_ops
    say(not new, "our action uses only opcodes EA's palantir.apt uses%s" % (": not %s" % sorted(map(hex, new)) if new else ""))
    pool, bad = [], []
    for a, op, name, arg in ours:
        if op in (0x88, 0x96):
            bad += [i for i in arg if i >= len(m.const.items)]
        if op == 0x88:
            pool = arg
        if op in (0xA2, 0xAE, 0xAF, 0xB2) and arg >= len(pool):
            bad.append(("pool", a))
        if op in (0x99, 0x9D) and not (act <= arg <= ours[-1][0]):
            bad.append(("branch", a))
    say(not bad, "our action's constants, pool indices and branches all exist%s" % (": %s" % bad if bad else ""))
    flags = {arg["flags"] for _, op, _, arg in ours if op == 0x8E}
    ea_flags = {arg["flags"] for _, _, a in actions(ea) for _, op, _, arg in decode(ea.d, a) if op == 0x8E}
    say({f >> 16 for f in flags} <= {f >> 16 for f in ea_flags},
        "our functions' preload flags %s are EA's (r1 = _root)" % sorted(hex(f >> 16) for f in flags))
    tail = len(ea_apt)
    say(act >= tail and all(p < len(apt) for p in (m.h["chars"], m.h["imports"], m.h["frames"])),
        "our structures lie after EA's movie (%d bytes) and inside the file (%d)" % (tail, len(apt)))
    return m


def resolve(pal, exm, label, ru, dat):
    """label of PalantirFrame -> (frame, character, (movie, export), sprite, shape, [texture])."""
    frames = pal.frames(FRAME_CLIP)
    for i, items in enumerate(frames):
        if any(k == "label" and v == label for k, v, _ in items):
            ch = [v["ch"] for k, v, _ in items if k == "place"][0]
            mv, name = {c: (mv_, nm) for mv_, nm, c in pal.imports()}[ch]
            spr = dict(exm.exports())[name]
            shape = [v["ch"] for its in exm.frames(spr) for k, v, _ in its if k == "place"][0]
            imgs = sorted({i_ for i_, _ in matrices(ru(shape))})
            return i, ch, (mv, name), spr, shape, ["apt_palantirexport_%d.tga" % dat[i_] for i_ in imgs]
    raise KeyError(label)


def dat_ids(text):
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if "->" in line:
            a, b = line.split("->")
            out[int(a)] = int(b)
        elif line and line[0].isdigit():
            out[int(line.split("=")[0])] = int(line.split("=")[0])
    return out


def trace(members, ea_read, act, factions, images, say):
    """Per side and state, the texture PalantirFrame draws; the expected one is checked."""
    pal = Movie(members["palantir.apt"], members["palantir.const"])
    exm = Movie(members["palantirexport.apt"], ea_read("palantirexport.const"))
    dat = dat_ids(members["palantirexport.dat"].decode("latin-1"))

    def ru(shape):
        m = "palantirexport_geometry\\%d.ru" % shape
        return (members[m] if m in members else ea_read(m)).decode("latin-1")

    tex = {(look, kind): "apt_palantirexport_%d.tga" % i for i, (look, kind, _) in images.items()}
    ea_tex = {}
    for (side, kind), st in STATES.items():
        ea_tex[side, kind] = resolve(pal, exm, st, ru, dat)[5][0]
    lines = []
    sides = [(s, n, f["side"]) for n, f in factions.items() for s in f["sides"]]
    sides += [("Observer", None, "good"), ("Observer", None, "evil"), ("", None, "good"), ("Isengard ", None, "evil")]
    for side, look, evil in sides:
        for kind in ("double", "single"):
            state = STATES[evil, kind]
            want = tex[look, kind] if look else ea_tex[evil, kind]
            for order in ("faction first", "state first", "re-shown"):
                vm = VM(pal, act).boot()
                if order == "faction first":
                    vm.game("SetPlayerFaction", side)
                    vm.game("SetPalantirFrameState", state)
                elif order == "state first":
                    vm.game("SetPalantirFrameState", state)
                    vm.game("SetPlayerFaction", side)
                else:
                    other = STATES[evil, "single" if kind == "double" else "double"]
                    vm.game("SetPlayerFaction", side)
                    for st in ("_hide", other, "_hide", state):
                        vm.game("SetPalantirFrameState", st)
                got = resolve(pal, exm, vm.frame.label, ru, dat)
                ok = got[5] == [want] and vm.icon == [side]
                say(ok, "%-10r %-12s %-13s -> label %-15s frame %2d char %d %s -> %s" % (
                    side, state, order, vm.frame.label, got[0], got[1], got[2][1], got[5][0]), quiet=ok)
            lines.append("%-10r %-12s -> %s -> %s" % (side, state, vm.frame.label, ", ".join(got[5])))
    vm = VM(pal, act).boot()
    vm.game("SetPlayerFaction", "Mordor")
    vm.game("SetPalantirFrameState", "_hide")
    say(vm.frame.label == "_hide", "_hide stays EA's _hide (the frame is not shown)")
    say(all(t in EA_STATES for t in vm.frame.calls), "EA's original still runs first on every call")
    return lines


def references(members, ea_read, factions, images, size2x, say):
    pal = Movie(members["palantir.apt"], members["palantir.const"])
    exm = Movie(members["palantirexport.apt"], ea_read("palantirexport.const"))
    exports = dict(exm.exports())
    ours = [(mv, nm, c) for mv, nm, c in pal.imports() if mv == "PalantirExport"]
    say(all(nm in exports for _, nm, _ in ours), "every PalantirExport import resolves (%d)" % len(ours))
    say(all(pal.chars()[c] == 0 for _, _, c in pal.imports()), "every import's character slot is empty")
    dat = dat_ids(members["palantirexport.dat"].decode("latin-1"))
    for i, (look, kind, ea_img) in sorted(images.items()):
        member = "art\\textures\\apt_palantirexport_%d.tga" % i
        w, h = struct.unpack_from("<HH", members.get(member, b"\0" * 18), 12)
        ew, eh = size2x(ea_img)
        say(member in members and (w, h) == (ew, eh) and dat.get(i) == i,
            "%s %s: image %d declared, %s shipped %dx%d (EA's %d at 2x: %dx%d)" % (
                look, kind, i, member.split("\\")[-1], w, h, ea_img, ew, eh))
    for nm, spr in exports.items():
        if not nm.startswith("PalantirFrame_"):
            continue
        p = exm.chars()[spr]
        say(p and struct.unpack_from("<I", exm.d, p)[0] == 5, "export %s is a sprite" % nm, quiet=True)


def placements(ea_apt, ea_const, members, factions, say):
    """Each new label places its frame with the transform EA uses for that side and kind."""
    ea, m = Movie(ea_apt, ea_const), Movie(members["palantir.apt"], members["palantir.const"])

    def placed(movie):
        out = {}
        for items in movie.frames(FRAME_CLIP):
            labels = [v for k, v, _ in items if k == "label"]
            for k, v, ip in items:
                if k == "place" and labels:
                    out[labels[0]] = (v["matrix"], v["depth"], v["flags"], movie.d[ip + 40:ip + 64])
        return out

    a, b = placed(ea), placed(m)
    for name, f in factions.items():
        for s in f["sides"]:
            for kind in ("double", "single"):
                lab = "_" + s + ("Single" if kind == "single" else "")
                want = a[STATES[f["side"], kind]]
                say(b.get(lab) == want, "%s placed as EA's %s: matrix %s, depth %d" % (
                    lab, STATES[f["side"], kind], want[0], want[1]), quiet=True)
    say(all(a[k] == b[k] for k in a), "EA's own five labels unchanged")
