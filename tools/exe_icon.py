#!/usr/bin/env python3
"""Extract the largest icon from a Windows PE executable as a PNG (stdlib only).

Usage: exe_icon.py <file.exe> <out.png>

Reads the RT_GROUP_ICON / RT_ICON resources, picks the biggest 32-bpp (or PNG-encoded) entry,
and writes it as PNG. Enough for making a macOS .app icon out of a game's own icon.
"""

import struct
import sys
import zlib


def sections(data, pe):
    nsec = struct.unpack_from("<H", data, pe + 6)[0]
    opt = struct.unpack_from("<H", data, pe + 20)[0]
    return [struct.unpack_from("<8sIIII", data, pe + 24 + opt + i * 40) for i in range(nsec)]


def rva_to_off(secs, rva):
    for _name, vsize, va, rsize, raw in secs:
        if va <= rva < va + max(vsize, rsize):
            return rva - va + raw
    raise ValueError(f"rva {rva:#x} not in any section")


def dir_entries(data, off):
    n_named, n_id = struct.unpack_from("<HH", data, off + 12)
    return [struct.unpack_from("<II", data, off + 16 + i * 8) for i in range(n_named + n_id)]


def resources(data, base, type_id):
    """{resource id: bytes} for one resource type (first language of each)."""
    out = {}
    for tid, toff in dir_entries(data, base):
        if tid != type_id:
            continue
        for rid, roff in dir_entries(data, base + (toff & 0x7FFFFFFF)):
            for _lang, loff in dir_entries(data, base + (roff & 0x7FFFFFFF)):
                rva, size = struct.unpack_from("<II", data, base + loff)
                off = rva_to_off(SECS, rva)
                out[rid] = data[off:off + size]
                break
    return out


def png_chunk(kind, body):
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)


def dib_to_png(blob):
    """32-bpp bottom-up BGRA DIB (ICO payload) -> PNG bytes, or None if not 32 bpp."""
    hsize, width, height2, _planes, bpp = struct.unpack_from("<IiiHH", blob, 0)
    if bpp != 32:
        return None
    height = height2 // 2
    rows = []
    stride = width * 4
    for y in range(height - 1, -1, -1):
        row = blob[hsize + y * stride:hsize + (y + 1) * stride]
        rgba = bytearray()
        for x in range(width):
            b, g, r, a = row[x * 4:x * 4 + 4]
            rgba += bytes((r, g, b, a))
        rows.append(b"\x00" + bytes(rgba))
    raw = zlib.compress(b"".join(rows), 9)
    return (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + png_chunk(b"IDAT", raw) + png_chunk(b"IEND", b""))


def main():
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 1
    data = open(sys.argv[1], "rb").read()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    global SECS
    SECS = sections(data, pe)
    rsrc_rva = struct.unpack_from("<I", data, pe + 24 + 112)[0]
    base = rva_to_off(SECS, rsrc_rva)
    icons = resources(data, base, 3)
    best = None
    for blob in icons.values():
        if blob[:8] == b"\x89PNG\r\n\x1a\n":
            w = struct.unpack_from(">I", blob, 16)[0]
            png = blob
        else:
            w = struct.unpack_from("<i", blob, 4)[0]
            png = dib_to_png(blob)
        if png and (best is None or w > best[0]):
            best = (w, png)
    if not best:
        print("no usable 32-bpp or PNG icon found", file=sys.stderr)
        return 1
    open(sys.argv[2], "wb").write(best[1])
    print(f"wrote {sys.argv[2]} ({best[0]}px)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
