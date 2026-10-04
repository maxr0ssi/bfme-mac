"""EA's map files (.map, AI bases .bse): which objects each map places, and where.

A map is "EAR\\0" + u32 size + a RefPack stream, or plain; the plain data is a CkMp chunk file:
"CkMp", u32 n, n x {u8 len, name, u32 id} (the chunk names), then chunks {u32 id, u16 version,
u32 size, data}. Objects sit in an ObjectsList chunk, one Object chunk each: x, y, z, angle
(radians) as floats, u32 flags, u16 len + the object's name, then its properties.

    placements(install)  {map member: [(object, x, y, z, angle)]}, cached in build/assets/_maps.json
                         keyed by the archives' sizes and dates
"""
import json
import os
import struct

MP = "\\map mp "                    # EA's multiplayer maps: maps\\map mp <name>\\<name>.map


def refpack(d):
    """The plain bytes of an EAR\\0-wrapped RefPack stream (anything else is returned as it is)."""
    if d[:4] != b"EAR\x00":
        return d
    d = d[8:]
    flags, p = d[0], 2
    n = 4 if flags & 0x80 else 3
    size = int.from_bytes(d[p:p + n], "big")
    p += n * (2 if flags & 0x01 else 1)
    out = bytearray()
    while p < len(d):
        b0 = d[p]
        if b0 < 0x80:
            b1 = d[p + 1]
            p += 2
            lit = b0 & 3
            cnt, off = ((b0 & 0x1C) >> 2) + 3, ((b0 & 0x60) << 3) + b1 + 1
        elif b0 < 0xC0:
            b1, b2 = d[p + 1], d[p + 2]
            p += 3
            lit = b1 >> 6
            cnt, off = (b0 & 0x3F) + 4, ((b1 & 0x3F) << 8) + b2 + 1
        elif b0 < 0xE0:
            b1, b2, b3 = d[p + 1], d[p + 2], d[p + 3]
            p += 4
            lit = b0 & 3
            cnt, off = ((b0 & 0x0C) << 6) + b3 + 5, ((b0 & 0x10) << 12) + (b1 << 8) + b2 + 1
        elif b0 < 0xFC:
            lit = ((b0 & 0x1F) << 2) + 4
            out += d[p + 1:p + 1 + lit]
            p += 1 + lit
            continue
        else:
            lit = b0 & 3
            out += d[p + 1:p + 1 + lit]
            break
        out += d[p:p + lit]
        p += lit
        s = len(out) - off
        for k in range(cnt):
            out.append(out[s + k])
    return bytes(out[:size])


def objects(data):
    """[(object, x, y, z, angle)] a plain CkMp file places."""
    if data[:4] != b"CkMp":
        raise ValueError("not a CkMp map file: %r" % data[:4])
    n = struct.unpack_from("<I", data, 4)[0]
    p, names = 8, {}
    for _ in range(n):
        ln = data[p]
        name = data[p + 1:p + 1 + ln].decode("latin-1")
        names[struct.unpack_from("<I", data, p + 1 + ln)[0]] = name
        p += 5 + ln
    out = []

    def walk(a, b):
        while a + 10 <= b:
            cid, _, size = struct.unpack_from("<IHI", data, a)
            s, e = a + 10, a + 10 + size
            if names.get(cid) == "ObjectsList":
                walk(s, e)
            elif names.get(cid) == "Object":
                x, y, z, angle = struct.unpack_from("<4f", data, s)
                ln = struct.unpack_from("<H", data, s + 20)[0]
                out.append((data[s + 22:s + 22 + ln].decode("latin-1"), x, y, z, angle))
            a = e
    walk(p, len(data))
    return out


def placements(install, refresh=False):
    """{map member: [(object, x, y, z, angle)]} of every map and AI base the game has."""
    from .. import paths
    from ..ownership import fingerprint
    cache = os.path.join(paths.BUILD, "_maps.json")
    fp = fingerprint(install)
    if not refresh and os.path.exists(cache):
        with open(cache) as fh:
            c = json.load(fh)
        if c.get("fingerprint") == fp:
            return {k: [tuple(o) for o in v] for k, v in c["maps"].items()}
    res = {}
    for m in install.members("maps") + install.members("bases"):
        if m.endswith((".map", ".bse")):
            try:
                res[m] = objects(refpack(install.read(m)))
            except (ValueError, IndexError, struct.error) as e:
                print("map not read: %s (%s)" % (m, e))
    os.makedirs(paths.BUILD, exist_ok=True)
    with open(cache + ".tmp", "w") as fh:
        json.dump({"fingerprint": fp, "maps": res}, fh)
    os.replace(cache + ".tmp", cache)
    return res


def map_name(member):
    """'maps\\map mp fords of isen\\map mp fords of isen.map' -> 'map mp fords of isen'."""
    return member.split("\\")[1]
