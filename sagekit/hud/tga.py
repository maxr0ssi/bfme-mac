"""EA's APT textures are uncompressed 32-bit TGAs (rows bottom-up, BGRA; the atlases carry the
TRUEVISION footer). Ours keep EA's header and trailing bytes byte for byte, with the new size."""
import struct


def info(data):
    """(width, height, bits per pixel, image type, descriptor) of a TGA."""
    w, h = struct.unpack_from("<HH", data, 12)
    return w, h, data[16], data[2], data[17]


def decode(data):
    """A 32-bit uncompressed TGA as (width, height, RGBA bytes top-down)."""
    w, h, bpp, kind, desc = info(data)
    if kind != 2 or bpp != 32:
        raise ValueError("not an uncompressed 32-bit TGA (type %d, %d bits)" % (kind, bpp))
    start = 18 + data[0]
    px = data[start:start + w * h * 4]
    rows = [px[y * w * 4:(y + 1) * w * 4] for y in range(h)]
    if not desc & 0x20:                         # bottom-up
        rows.reverse()
    bgra = b"".join(rows)
    out = bytearray(len(bgra))
    out[0::4], out[1::4], out[2::4], out[3::4] = bgra[2::4], bgra[1::4], bgra[0::4], bgra[3::4]
    return w, h, bytes(out)


def encode(ref, w, h, rgba):
    """RGBA bytes (top-down) as a TGA laid out like EA's `ref` (its header, row order, footer)."""
    rw, rh, bpp, kind, desc = info(ref)
    if kind != 2 or bpp != 32:
        raise ValueError("EA's texture is not an uncompressed 32-bit TGA")
    if len(rgba) != w * h * 4:
        raise ValueError("%d bytes for %dx%d" % (len(rgba), w, h))
    head = bytearray(ref[:18 + ref[0]])
    struct.pack_into("<HH", head, 12, w, h)
    tail = ref[18 + ref[0] + rw * rh * 4:]
    bgra = bytearray(len(rgba))
    bgra[0::4], bgra[1::4], bgra[2::4], bgra[3::4] = rgba[2::4], rgba[1::4], rgba[0::4], rgba[3::4]
    rows = [bytes(bgra[y * w * 4:(y + 1) * w * 4]) for y in range(h)]
    if not desc & 0x20:
        rows.reverse()
    return bytes(head) + b"".join(rows) + bytes(tail)
