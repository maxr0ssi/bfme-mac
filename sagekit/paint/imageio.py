"""Pixels in and out (numpy), in the formats the game reads.

Normal-map convention, established from the game's shader and the original data:
  * NormalMapped.fx's vertex shader builds its tangent basis as (x, y, z) = (-BINORMAL, -TANGENT,
    NORMAL); the pixel shader dots (tex * 2 - 1) with the light in that basis.
  * The original files store tangents = -dP/dv and binormals = +dP/du, and the Blender add-on's
    exporter writes the same (tangent = -Blender bitangent, binormal = Blender tangent).
  * So against Blender's (OpenGL) tangent space the RED channel is inverted, green is not:
    game R = 1 - GL R. `game_to_gl` / `gl_to_game` convert (the same flip both ways).
"""
import struct

import numpy as np

TGA_FOOTER = b"\0" * 8 + b"TRUEVISION-XFILE.\0"


def gl_to_game(rgb):
    out = rgb.copy()
    out[..., 0] = 1.0 - out[..., 0]
    return out


game_to_gl = gl_to_game


def write_tga24(path, rgb01, ref_header=None, ref_footer=None):
    """24-bit uncompressed TGA, bottom-up rows (descriptor 0), BGR, with the TRUEVISION footer:
    byte for byte the layout of the game's normal maps. rgb01: (h, w, 3), rows bottom-up."""
    h, w = rgb01.shape[:2]
    hdr = bytearray(ref_header) if ref_header else bytearray(18)
    hdr[2] = 2
    struct.pack_into("<HH", hdr, 12, w, h)
    hdr[16], hdr[17] = 24, 0
    px = np.clip(np.rint(rgb01 * 255), 0, 255).astype(np.uint8)[..., ::-1]
    with open(path, "wb") as f:
        f.write(bytes(hdr))
        f.write(px.tobytes())
        f.write(ref_footer if ref_footer is not None else TGA_FOOTER)


def read_tga24(path):
    with open(path, "rb") as fh:
        d = fh.read()
    idl, cmt, typ = d[0], d[1], d[2]
    w, h = struct.unpack_from("<HH", d, 12)
    bpp, desc = d[16], d[17]
    off = 18 + idl
    px = np.frombuffer(d, np.uint8, w * h * 3, off).reshape(h, w, 3)[..., ::-1].astype(np.float32) / 255
    if desc & 0x20:
        px = px[::-1]
    return dict(type=typ, width=w, height=h, bpp=bpp, desc=desc, cmap=cmt, idlen=idl, header=d[:18],
                footer=d[off + w * h * 3:], pixels=px)


def to_srgb(lin):
    lin = np.maximum(lin, 0)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055)


def pull_push(img, mask):
    """Fill everything outside mask from the covered texels, coarse to fine, so mips and bilinear
    filtering never pull in black. img (h, w, c), mask (h, w) in [0, 1]."""
    levels = []
    c, wgt = img * mask[..., None], mask.astype(np.float32).copy()
    while c.shape[0] > 1:
        levels.append((c, wgt))
        h, w = c.shape[:2]
        c = c.reshape(h // 2, 2, w // 2, 2, -1).sum((1, 3))
        wgt = wgt.reshape(h // 2, 2, w // 2, 2).sum((1, 3))
    avg = c / np.maximum(wgt, 1e-8)[..., None]
    for c_l, w_l in reversed(levels):
        up = np.repeat(np.repeat(avg, 2, 0), 2, 1)
        a = c_l / np.maximum(w_l, 1e-8)[..., None]
        k = np.clip(w_l, 0, 1)[..., None]
        avg = a * k + up * (1 - k)
    return avg


def downsample(img, factor):
    """Box-filter an (h, w, ...) image by an integer factor."""
    if factor == 1:
        return img
    h, w = img.shape[:2]
    return img.reshape(h // factor, factor, w // factor, factor, *img.shape[2:]).mean((1, 3))
