"""EA's APT movie files read as data (stdlib): the .apt structures the per-faction palantir edits and
its ActionScript bytecode. Own code; the layout was read from RotWK's palantir.apt and checked on
every structure and action of it (sagekit/hud/factioncheck.py).

  .const  0x14: offset of the movie in the .apt; 0x18: item count; 0x1c: items, (type, value) each:
          type 1 a string (value: its offset in the .const), type 4 a register number
  .apt    the movie: 15 u32 words at that offset (type, signature, frame count, frames, ...,
          character count, characters, width, height, ms, import count, imports, export count,
          exports, count). Pointers are offsets in the file; the game relocates each one once.
  frame   (item count, items); item (type, ...): 1 action (bytecode), 2 label (name, flags, frame),
          3 place (flags, depth, character, matrix, x, y, ...), 4 remove (depth)
  sprite  character type 5: (5, signature, frame count, frames, pointer)
  bytecode EA's Flash-derived opcodes; an opcode with operands pads to 4 bytes before them
"""
import struct

ROOT = ("type", "sig", "nframes", "frames", "ptr", "nchars", "chars", "width", "height", "ms",
        "nimports", "imports", "nexports", "exports", "count")
NOARG = {0x00: "End", 0x04: "NextFrame", 0x05: "PrevFrame", 0x06: "Play", 0x07: "Stop", 0x0a: "Add", 0x0b: "Subtract", 0x0c: "Multiply",
         0x0d: "Divide", 0x0e: "Equals", 0x0f: "Less", 0x10: "And", 0x11: "Or", 0x12: "Not",
         0x17: "Pop", 0x18: "ToInteger", 0x1c: "GetVariable", 0x1d: "SetVariable", 0x20: "SetTarget2",
         0x21: "StringAdd", 0x22: "GetProperty", 0x23: "SetProperty", 0x24: "CloneSprite",
         0x25: "RemoveSprite", 0x26: "Trace", 0x27: "StartDrag", 0x28: "EndDrag", 0x34: "GetTime",
         0x30: "RandomNumber", 0x3a: "Delete", 0x3b: "Delete2", 0x3c: "DefineLocal", 0x3d: "CallFunction",
         0x3e: "Return", 0x3f: "Modulo", 0x40: "NewObject", 0x41: "DefineLocal2", 0x42: "InitArray",
         0x43: "InitObject", 0x44: "TypeOf", 0x46: "Enumerate", 0x47: "Add2", 0x48: "Less2",
         0x49: "Equals2", 0x4a: "ToNumber", 0x4b: "ToString", 0x4c: "PushDuplicate", 0x4d: "StackSwap",
         0x4e: "GetMember", 0x4f: "SetMember", 0x50: "Increment", 0x51: "Decrement", 0x52: "CallMethod",
         0x53: "NewMethod", 0x54: "InstanceOf", 0x55: "Enumerate2", 0x59: "PushZero", 0x5a: "PushOne",
         0x5b: "CallFunctionPop", 0x5c: "CallFunction*", 0x5d: "CallMethodPop", 0x5e: "CallMethod*",
         0x60: "BitAnd", 0x61: "BitOr", 0x62: "BitXor", 0x63: "BitLShift", 0x64: "BitRShift",
         0x65: "BitURShift", 0x66: "StrictEquals", 0x67: "Greater", 0x69: "Extends",
         0x70: "PushThis", 0x71: "PushGlobal", 0x72: "ZeroVariable", 0x73: "PushTrue",
         0x74: "PushFalse", 0x75: "PushNull", 0x76: "PushUndefined", 0x9a: "GetURL2"}
BYTE = {0xa2: "PushConst", 0xae: "PushValueOfVar", 0xaf: "GetNamedMember", 0xb0: "CallNamedFuncPop",
        0xb1: "CallNamedFunc", 0xb2: "CallNamedMethodPop", 0xb3: "CallNamedMethod", 0xb5: "PushByte",
        0xb9: "PushRegister"}
WORD32 = {0x81: "GotoFrame", 0x87: "SetRegister", 0x8a: "WaitForFrame",
          0x8d: "WaitForFrame2", 0x9f: "GotoFrame2"}
STRING = {0x8b: "SetTarget", 0x8c: "GotoLabel", 0xa1: "PushString", 0xa4: "GetStringVar",
          0xa5: "GetStringMember", 0xa6: "SetStringVar", 0xa7: "SetStringMember"}
BRANCH = {0x99: "Jump", 0x9d: "IfTrue", 0xb8: "IfFalse"}
POINTERS = (0x88, 0x96, 0x8e, 0x9b, 0x83, 0x94) + tuple(STRING)   # operands the loader relocates


def u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def cstr(d, o):
    return d[o:d.index(b"\0", o)].decode("latin-1")


class Const:
    def __init__(self, data):
        self.d = data
        self.root = u32(data, 0x14)
        n, io = struct.unpack_from("<II", data, 0x18)
        self.items = [struct.unpack_from("<II", data, io + 8 * i) for i in range(n)]

    def value(self, i):
        t, v = self.items[i]
        return cstr(self.d, v) if t == 1 else ("r%d" % v if t == 4 else (t, v))


class Movie:
    def __init__(self, apt, const):
        self.d = apt
        self.const = Const(const)
        self.root = self.const.root
        self.h = dict(zip(ROOT, struct.unpack_from("<15I", apt, self.root)))

    def chars(self):
        return [u32(self.d, self.h["chars"] + 4 * i) for i in range(self.h["nchars"])]

    def imports(self):
        """[(movie, name, character)]"""
        p = self.h["imports"]
        return [(cstr(self.d, u32(self.d, p + 16 * i)), cstr(self.d, u32(self.d, p + 16 * i + 4)),
                 u32(self.d, p + 16 * i + 8)) for i in range(self.h["nimports"])]

    def exports(self):
        """[(name, character)]"""
        p = self.h["exports"]
        return [(cstr(self.d, u32(self.d, p + 8 * i)), u32(self.d, p + 8 * i + 4)) for i in range(self.h["nexports"])]

    def frames_of(self, cid=None):
        """(frame count, frames pointer) of the root (cid None) or of sprite `cid`."""
        if cid is None:
            return self.h["nframes"], self.h["frames"]
        p = self.chars()[cid]
        if u32(self.d, p) != 5:
            raise ValueError("character %d is not a sprite" % cid)
        return struct.unpack_from("<II", self.d, p + 8)

    def frames(self, cid=None):
        """[[(kind, value, item address)]] per frame."""
        nf, fp = self.frames_of(cid)
        out = []
        for f in range(nf):
            cnt, itp = struct.unpack_from("<II", self.d, fp + 8 * f)
            items = []
            for k in range(cnt):
                ip = u32(self.d, itp + 4 * k)
                t = u32(self.d, ip)
                if t == 1:
                    items.append(("action", u32(self.d, ip + 4), ip))
                elif t == 2:
                    items.append(("label", cstr(self.d, u32(self.d, ip + 4)), ip))
                elif t == 3:
                    flags, depth, ch = struct.unpack_from("<Iii", self.d, ip + 4)
                    mat = struct.unpack_from("<6f", self.d, ip + 16)
                    items.append(("place", dict(flags=flags, depth=depth, ch=ch, matrix=mat), ip))
                elif t == 4:
                    items.append(("remove", u32(self.d, ip + 4), ip))
                else:
                    items.append(("type%d" % t, None, ip))
            out.append(items)
        return out


def decode(d, start, limit=None):
    """[(address, opcode, name, operand)] of the action at `start`, to its End. Raises on an opcode
    this reader does not know (so a check over all of EA's actions proves the table)."""
    p, out, ends = start, [], []
    al = lambda q: (q + 3) & ~3
    while True:
        if limit is not None and p >= limit:
            raise ValueError("action at %#x runs past %#x" % (start, limit))
        a, op = p, d[p]
        p += 1
        arg = None
        if op in NOARG:
            name = NOARG[op]
        elif op in BYTE:
            name, arg = BYTE[op], d[p]
            p += 1
        elif op == 0xa3:
            p = al(p)
            name, arg = "PushConstWord", struct.unpack_from("<H", d, p)[0]
            p += 2
        elif op == 0xb6:
            name, arg = "PushShort", struct.unpack_from("<h", d, p)[0]
            p += 2
        elif op in WORD32:
            p = al(p)
            name, arg = WORD32[op], struct.unpack_from("<i", d, p)[0]
            p += 4
        elif op in (0xb4, 0xb7):                        # EA's float and long pushes: not padded
            name, arg = ("PushFloat", struct.unpack_from("<f", d, p)[0]) if op == 0xb4 else \
                ("PushLong", struct.unpack_from("<i", d, p)[0])
            p += 4
        elif op in STRING:
            p = al(p)
            name, arg = STRING[op], cstr(d, u32(d, p))
            p += 4
        elif op in BRANCH:
            p = al(p)
            off = struct.unpack_from("<i", d, p)[0]
            p += 4
            name, arg = BRANCH[op], p + off
        elif op in (0x88, 0x96):
            p = al(p)
            cnt, ptr = struct.unpack_from("<II", d, p)
            p += 8
            name, arg = ("ConstantPool" if op == 0x88 else "PushData"), list(struct.unpack_from("<%dI" % cnt, d, ptr))
        elif op == 0x8e:
            p = al(p)
            fname, nargs, flags, argp, size = struct.unpack_from("<5I", d, p)
            p += 28
            args = [(r, cstr(d, s)) for r, s in (struct.unpack_from("<II", d, argp + 8 * i) for i in range(nargs))]
            name, arg = "DefineFunction2", dict(name=cstr(d, fname) if fname else "", flags=flags, args=args,
                                                size=size, body=p)
            ends.append(p + size)
        elif op == 0x9b:
            p = al(p)
            fname, nargs, argp, size = struct.unpack_from("<4I", d, p)
            p += 24
            name, arg = "DefineFunction", dict(name=cstr(d, fname) if fname else "", size=size, body=p)
            ends.append(p + size)
        elif op == 0x94:
            p = al(p)
            name, arg = "With", u32(d, p)
            p += 4
        else:
            raise ValueError("unknown opcode %#04x at %#x (action at %#x)" % (op, a, start))
        out.append((a, op, name, arg))
        while ends and p >= ends[-1]:
            if p != ends[-1]:
                raise ValueError("function body at %#x overruns its size" % a)
            ends.pop()
        if op == 0 and not ends:
            return out


def actions(movie):
    """Every action stream's address in the movie: the root's frames and every sprite's."""
    out = []
    owners = [None] + [i for i, p in enumerate(movie.chars()) if p and u32(movie.d, p) == 5]
    for cid in owners:
        for f, items in enumerate(movie.frames(cid)):
            out += [(cid, f, v) for k, v, _ in items if k == "action"]
    return out
