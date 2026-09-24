"""Texture files by their headers (stdlib only; pixels live in sagekit/paint/imageio.py).

The game resolves a model's `NAME.tga` reference to art/compiledtextures/<first two letters>/
name.dds (or .tga) in any archive; diffuse maps ship as DXT1 DDS with a full mip chain, normal
maps as 24-bit uncompressed TGA like the originals (see NormalMapped.fx notes in imageio.py).
"""
import os
import struct
import subprocess

MAGICK = "magick"


def compiled_path(texture_name, ext):
    """Archive path the game loads `DBFortressH.tga` from: art\\compiledtextures\\db\\dbfortressh.dds"""
    stem = os.path.splitext(texture_name)[0].lower()
    return "art\\compiledtextures\\%s\\%s%s" % (stem[:2], stem, ext)


def dds_info(path):
    with open(path, "rb") as fh:
        d = fh.read(128)
    if d[:4] != b"DDS ":
        raise ValueError("%s: not a DDS" % path)
    size, flags, h, w, pitch, depth, mips = struct.unpack_from("<7I", d, 4)
    return dict(width=w, height=h, mips=mips, fourcc=d[84:88].decode("latin-1"), flags=flags,
                bytes=os.path.getsize(path))


def dxt1_size(w, h, mips):
    """Bytes of a DXT1 DDS (header included) with `mips` levels."""
    n = 128
    for i in range(mips):
        wi, hi = max(1, w >> i), max(1, h >> i)
        n += ((wi + 3) // 4) * ((hi + 3) // 4) * 8
    return n


def full_chain(size):
    """Mip levels down to 1x1: 4096 -> 13."""
    return size.bit_length()


def tga24_size(w, h, footer=26):
    return 18 + w * h * 3 + footer


def tga_header(path):
    with open(path, "rb") as fh:
        d = fh.read(18)
    w, h = struct.unpack_from("<HH", d, 12)
    return dict(idlen=d[0], cmap=d[1], type=d[2], width=w, height=h, bpp=d[16], desc=d[17], header=d)


def write_dds_dxt1(png_path, dds_path):
    """DXT1 with a full mip chain via ImageMagick (cluster fit)."""
    w = int(subprocess.check_output([MAGICK, "identify", "-format", "%w", png_path]).decode())
    subprocess.check_call([MAGICK, png_path, "-define", "dds:compression=dxt1", "-define",
                           "dds:mipmaps=%d" % (full_chain(w) - 1), "-define", "dds:cluster-fit=true", dds_path])
    return dds_info(dds_path)
