"""Recipe-side workarounds for three framework limits the barracks is the first to hit (reported;
sagekit itself is not edited). Each is a no-op for every other building's files.

1. 32-bit normal map (sagekit/paint/imageio.py read_tga24 / write_tga24): EA's ebbarracks_nrm.tga is
   a 32-bit TGA (BGRA, alpha 255 everywhere, descriptor 0x08). read_tga24 assumes 3 bytes a pixel,
   so it takes the last quarter of the reference's pixels as its "footer", and the painter then
   writes our 24-bit map followed by that megabyte of stray pixels. Here reading honours the
   header's depth and writing keeps the reference's depth: our map is written in EA's exact
   layout (32-bit, alpha 255, the original descriptor and footer). 24-bit files behave as before.
   The checks' size formula (tga24_size, 3 bytes a pixel) is given the depth of the file it is
   checked against.
2. EA's degenerate triangles (sagekit/blender/checks.py snapshot): EA's RACKPIKE (a weapon rack we
   do not touch; its chunk is checked byte for byte) has 2 zero-area triangles of its own, which
   the "zero-area faces" check counts against us. They are discounted for that mesh only.
Blender side only (the host has no numpy and never runs these)."""

EA_DEGENERATE = {"RACKPIKE": 2}       # zero-area triangles in EA's own (untouched) meshes


def _patch_tga():
    try:
        import numpy as np
        from sagekit.paint import imageio
    except ImportError:
        return
    if getattr(imageio.read_tga24, "depth_fix", False):
        return
    import struct
    read24, write24 = imageio.read_tga24, imageio.write_tga24

    def read_tga24(path):
        with open(path, "rb") as fh:
            d = fh.read()
        if d[16] != 32:
            return read24(path)
        w, h = struct.unpack_from("<HH", d, 12)
        off = 18 + d[0]
        px = np.frombuffer(d, np.uint8, w * h * 4, off).reshape(h, w, 4)[..., 2::-1].astype(np.float32) / 255
        if d[17] & 0x20:
            px = px[::-1]
        return dict(type=d[2], width=w, height=h, bpp=32, desc=d[17], cmap=d[1], idlen=d[0], header=d[:18],
                    footer=d[off + w * h * 4:], pixels=px)

    def write_tga24(path, rgb01, ref_header=None, ref_footer=None):
        if not ref_header or ref_header[16] != 32:
            return write24(path, rgb01, ref_header, ref_footer)
        h, w = rgb01.shape[:2]
        hdr = bytearray(ref_header)
        struct.pack_into("<HH", hdr, 12, w, h)
        hdr[17] &= ~0x20 & 0xFF                        # rows bottom-up, as written below
        px = np.clip(np.rint(rgb01 * 255), 0, 255).astype(np.uint8)[..., ::-1]
        bgra = np.concatenate([px, np.full((h, w, 1), 255, np.uint8)], -1)
        with open(path, "wb") as f:
            f.write(bytes(hdr))
            f.write(bgra.tobytes())
            f.write(ref_footer if ref_footer is not None else imageio.TGA_FOOTER)
    read_tga24.depth_fix = True
    imageio.read_tga24, imageio.write_tga24 = read_tga24, write_tga24

    from sagekit.formats import textures
    size24 = textures.tga24_size

    def tga24_size(w, h, footer=26):
        if footer == 26 and _REF_DEPTH.get("bpp") == 32:
            return 18 + w * h * 4 + footer
        return size24(w, h, footer)
    textures.tga24_size = tga24_size


_REF_DEPTH = {}


def note_reference(path):
    """The depth of the normal map ours is checked against (read on the Blender side)."""
    try:
        with open(path, "rb") as fh:
            _REF_DEPTH["bpp"] = fh.read(18)[16]
    except OSError:
        pass


def _patch_snapshot():
    try:
        from sagekit.blender import checks
    except ImportError:
        return
    if getattr(checks.snapshot, "degenerate_fix", False):
        return
    snapshot = checks.snapshot

    def fixed(path, skeletons=None):
        s = snapshot(path, skeletons)
        for name, n in EA_DEGENERATE.items():
            m = s["meshes"].get(name)
            if m is not None:
                m["zero_area"] = max(0, m["zero_area"] - n)
        return s
    fixed.degenerate_fix = True
    checks.snapshot = fixed


def apply():
    import os

    from sagekit import paths
    note_reference(os.path.join(paths.BUILD, "dwarves", "barracks", "src", "ebbarracks_nrm.tga"))
    _patch_tga()
    _patch_snapshot()
