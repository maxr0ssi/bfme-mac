"""EA's APT textures are uncompressed 32-bit TGAs (rows bottom-up, BGRA; the atlases carry the
TRUEVISION footer). Ours keep EA's header and trailing bytes, with the new size and one fix: the
descriptor always declares 8 alpha bits.

Why the alpha bits matter (game.dat 2.01, `0x531049`): the game copies a 32-bit TGA straight into
an A8R8G8B8 texture only when D3DX accepts it at the file's own size and format; otherwise it hands
the file to D3DXCreateTextureFromFileInMemoryEx, which reads a 32-bit TGA that declares 0 alpha bits
as X8R8G8B8, with no alpha. EA's two atlases (apt_palantir_1, apt_libingameimagesmain_1) declare 0
and always took the copy at 1024x512; at 2048x1024 ours went to D3DX and lost their alpha: the
power button's highlight drew as an opaque square (2026-10-04)."""
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
    head[17] = (head[17] & 0xF0) | 8                # 8 alpha bits, whatever EA declared
    tail = ref[18 + ref[0] + rw * rh * 4:]
    bgra = bytearray(len(rgba))
    bgra[0::4], bgra[1::4], bgra[2::4], bgra[3::4] = rgba[2::4], rgba[1::4], rgba[0::4], rgba[3::4]
    rows = [bytes(bgra[y * w * 4:(y + 1) * w * 4]) for y in range(h)]
    if not desc & 0x20:
        rows.reverse()
    return bytes(head) + b"".join(rows) + bytes(tail)


def alpha_bits(data):
    return data[17] & 0x0F
