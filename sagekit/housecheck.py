"""House-colour lines as the engine resolves them (docs/CAH.md "Hero colours"), and the share of each
part the three Create-a-Hero colours reach.

What game.dat does (read from the exe, RotWK 2.02):
- housecolor.ini (block parser 0x828365 -> 0x536643): each BaseTexture name goes through the asset
  manager (0xa32ee0: the textures asset.dat files at startup) to a texture id, and the HouseTexture
  is stored under that id (map 0xdd83f4). A BaseTexture asset.dat does not file gets id -1, so its
  line never matches a mesh (a texture created later gets an id of its own, 0x532875): the texture
  draws, without house or hero colours.
- A mesh with a legacy material (0x54bde0 from 0x54c49e: one pass) looks its stage-0 texture's id up
  (0x535e86) and builds the coloured texture `#<mask>#<key>` (0x5326f8). The mask file is found by
  name, .dds before .tga (0x530d29), and loaded in its own format (D3DFMT_UNKNOWN, 0x53117e), a
  24/32-bit TGA as X8R8G8B8/A8R8G8B8 (0x5310ad). The colouring (0x531c77) handles A8R8G8B8 and
  A4R4G4B4 only: any other mask stays uncoloured.
- The colour is mask R x colour 1 + G x colour 2 + B x colour 3, alpha kept. The Create-a-Hero
  pickers set them: Hair -> 1 (R), Skin -> 2 (G), Paint -> 3 (B) (handlers 0x9c3c22, 0x9c3c4c,
  0x9c3c76 -> MyHero +0x2c/+0x30/+0x34, registered with OnHairColor/OnSkinColor/OnPaintColor).

    validate()     python3 -m sagekit validate: every house-colour line of ours whose texture an
                   archive ships has its BaseTexture filed in asset.dat and a mask the colouring
                   handles; no archive of ours serves a mask it cannot colour
    tint(archive)  per part mesh of an archive: the share of its surface each picker colours
                   (shares(); the CaH parts' rules on it: assets/cah/kit/attach_lint.py paint_lint)
    python3 -m sagekit.housecheck [--tint archive.big] [--selfcheck]
"""
import math
import re
import struct
import sys

LINE = re.compile(r"(?is)HouseColor\s+BaseTexture\s*=\s*(\S+)\s+HouseTexture\s*=\s*(\S+)\s+End")
INI = "data\\ini\\housecolor.ini"
PICKERS = ("Hair (R)", "Skin (G)", "Paint (B)")


def lines(text):
    """[(BaseTexture, HouseTexture)] of a housecolor.ini text, in order."""
    return LINE.findall(text)


def mask_problem(name, data):
    """None, or why the colouring (0x531c77) cannot use this mask file."""
    if name.lower().endswith(".dds"):
        flags, bits, r, g, b, a = struct.unpack_from("<I4xIIIII", data, 80)
        if flags & 0x40 and bits == 32 and (r, g, b, a) == (0xff0000, 0xff00, 0xff, 0xff000000):
            return None                                     # A8R8G8B8
        if flags & 0x40 and bits == 16 and (r, g, b, a) == (0xf00, 0xf0, 0xf, 0xf000):
            return None                                     # A4R4G4B4
        return "%s: DDS %s, not A8R8G8B8/A4R4G4B4 (left uncoloured)" % (
            name, data[84:88].decode("latin-1") if flags & 4 else "%d-bit" % bits)
    if data[2] in (2, 10) and data[16] == 32:
        return None
    return "%s: TGA type %d, %d-bit (a 32-bit truecolour TGA is the only kind loaded with alpha)" % (name, data[2], data[16])


def check(ini, ea_ini, filed, provider, read):
    """(problems, notes) for the lines of `ini` that EA's `ea_ini` lacks. filed: lower-case texture
    names asset.dat files; provider(name) -> (member, ours) of the file the game reads for a
    texture name (.dds before .tga) or None; read(member) -> bytes."""
    ea = {(b.lower(), h.lower()) for b, h in lines(ea_ini)}
    problems, notes, seen = [], [], set()
    for base, mask in lines(ini):
        if (base.lower(), mask.lower()) in ea:
            continue
        if provider(base) is None:
            notes.append("%s: no archive ships it; the line is inert (id -1)" % base)
            continue
        if base.lower() not in filed:
            problems.append("%s: asset.dat files no record, so the engine keys its line -1 and never "
                            "colours it (0x536643)" % base)
        got = provider(mask)
        if got is None:
            problems.append("%s: no archive ships its mask %s" % (base, mask))
        elif got[0] not in seen:
            seen.add(got[0])
            why = mask_problem(got[0], read(got[0]))
            if why:
                problems.append(why)
    for base, mask in lines(ini):                       # a mask of EA's name that an archive of ours replaces
        got = provider(mask)
        if got and got[1] and got[0] not in seen:
            seen.add(got[0])
            why = mask_problem(got[0], read(got[0]))
            if why:
                problems.append(why)
    return problems, notes


def validate():
    """sagekit validate over the installed game; 1 on a problem."""
    import os
    from . import paths
    from .formats.assetcache import AssetCache
    from .game import Install
    try:
        live, ea = Install(pristine=False), Install()
        ini, ea_ini = live.read(INI).decode("latin-1"), ea.read(INI).decode("latin-1")
        filed = set()
        for g in paths.GAMEDIRS.values():
            if os.path.exists(os.path.join(g, "asset.dat")):
                filed |= {n.decode("latin-1") for n in AssetCache(os.path.join(g, "asset.dat")).texture_names()}
        files = {}
        for m in live.members("art\\"):
            files.setdefault(m.split("\\")[-1], m)
    except OSError as e:
        print("note: game files not readable (%s): house-colour lines not checked" % e)
        return 0

    def provider(name):
        stem = name.lower().rsplit(".", 1)[0]
        for ext in (".dds", ".tga"):
            m = files.get(stem + ext)
            if m:
                return m, paths.is_ours(live.owner(m).path)
        return None
    problems, notes = check(ini, ea_ini, filed, provider, live.read)
    for p in problems:
        print("FAIL house colour: %s" % p)
    if not problems:
        print("ok   house colour: our %d lines filed and their masks colourable%s" % (
            len(lines(ini)) - len(lines(ea_ini)), "; %d inert (texture not shipped)" % len(notes) if notes else ""))
    return 1 if problems else 0


SUB = 4                         # each triangle sampled at the centres of its SUB x SUB equal sub-triangles
BARY = [((i + 1 / 3) / SUB, (j + 1 / 3) / SUB) for i in range(SUB) for j in range(SUB - i)] + \
       [((i + 2 / 3) / SUB, (j + 2 / 3) / SUB) for i in range(SUB) for j in range(SUB - 1 - i)]


def shares(mesh, w, h, px, rgb=(2, 1, 0)):
    """(area, [share of the mesh's surface per picker R, G, B]) over a mask of w x h texels, 4 bytes
    each, top row first, alpha the 4th byte; rgb: the byte offsets of R, G, B (a DDS A8R8G8B8 is
    stored B, G, R, A; a raw RGBA file 0, 1, 2). Image row = (1 - V) x height, as the part kit lays
    its tiles (assets/cah/kit/geom.py); a texel counts where alpha and the channel are over 16. A
    triangle is sampled at SUB^2 points of equal area (one sample at its centre misses a band that
    is narrower than the triangle)."""
    area, hit = 0.0, [0.0, 0.0, 0.0]
    for t in mesh.tris:
        p = [mesh.verts[j] for j in t]
        e1, e2 = [p[1][c] - p[0][c] for c in range(3)], [p[2][c] - p[0][c] for c in range(3)]
        ar = math.sqrt(sum(x * x for x in (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2],
                                            e1[0] * e2[1] - e1[1] * e2[0]))) / 2
        (u0, v0), (u1, v1), (u2, v2) = (mesh.uv[j] for j in t)
        area += ar
        for a, b in BARY:
            u, v = u0 + a * (u1 - u0) + b * (u2 - u0), 1 - (v0 + a * (v1 - v0) + b * (v2 - v0))
            o = ((int((v % 1) * h) % h) * w + int((u % 1) * w) % w) * 4
            if px[o + 3] > 16:
                for c in range(3):
                    if px[o + rgb[c]] > 16:
                        hit[c] += ar / len(BARY)
    return area, [x / area if area else 0 for x in hit]


def tint(archive):
    """{(model, mesh): (area, [share per picker])} for the models of `archive` whose texture has a
    mask `hc_<texture>` in the same archive (shares())."""
    from .formats.big import Archive
    from .formats.w3d import W3DFile
    a = Archive(archive)
    idx, masks, out = a.index(), {}, {}
    for k in sorted(idx):
        if not k.endswith(".w3d"):
            continue
        for name, m in W3DFile(a.read(k)).meshes.items():
            key = ("art\\compiledtextures\\hc\\hc_" + m.textures[0].lower()[:-4] + ".dds") if m.textures else None
            if key not in idx:
                continue
            if key not in masks:
                d = a.read(key)
                h, w = struct.unpack_from("<II", d, 12)
                masks[key] = (w, h, d[128:128 + w * h * 4])
            out[(k.split("\\")[-1][:-4], name)] = shares(m, *masks[key])
    return out


def selfcheck():
    """A good line passes; an unfiled base, a DXT mask, a 24-bit TGA mask and a missing mask fail."""
    a8 = b"DDS " + bytes(72) + struct.pack("<II4sIIIII", 32, 0x41, b"\0" * 4, 32, 0xff0000, 0xff00, 0xff, 0xff000000)
    dxt = b"DDS " + bytes(72) + struct.pack("<II4sIIIII", 32, 4, b"DXT5", 0, 0, 0, 0, 0)
    tga24 = bytes([0, 0, 2]) + bytes(13) + bytes([24, 0])
    ea = "HouseColor\r\n BaseTexture = ea.tga\r\n HouseTexture = hc_ea.tga\r\nEnd\r\n"
    data = {"m\\hc_a.dds": a8, "m\\hc_b.dds": dxt, "m\\hc_c.tga": tga24, "m\\a.dds": a8, "m\\b.dds": a8,
            "m\\c.dds": a8, "m\\d.dds": a8, "m\\e.dds": a8, "m\\hc_e.dds": a8}

    def provider(n):
        stem = n.lower().rsplit(".", 1)[0]
        return next(((m, True) for m in ("m\\%s.dds" % stem, "m\\%s.tga" % stem) if m in data), None)

    def run(base, mask, filed=("a.tga", "b.tga", "c.tga", "d.tga")):
        ini = ea + "HouseColor\r\n BaseTexture = %s\r\n HouseTexture = %s\r\nEnd\r\n" % (base, mask)
        return check(ini, ea, set(filed), provider, data.__getitem__)
    assert run("A.tga", "HC_A.tga") == ([], []), run("A.tga", "HC_A.tga")
    assert run("e.tga", "hc_e.tga")[0], "an unfiled base passed"
    assert run("b.tga", "hc_b.tga")[0], "a DXT mask passed"
    assert run("c.tga", "hc_c.tga")[0], "a 24-bit TGA mask passed"
    assert run("d.tga", "hc_d.tga")[0], "a missing mask passed"
    assert run("z.tga", "hc_z.tga") == ([], ["z.tga: no archive ships it; the line is inert (id -1)"])
    print("PASS: a filed line with an A8R8G8B8 mask passes; unfiled, DXT, 24-bit and missing masks fail")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--selfcheck"]:
        return selfcheck()
    if argv[:1] == ["--tint"] and len(argv) == 2:
        for (model, mesh), (area, share) in sorted(tint(argv[1]).items()):
            print("%-16s %-17s " % (model, mesh) + "  ".join("%s %5.1f%%" % (p, 100 * s) for p, s in zip(PICKERS, share)))
        return 0
    return validate()


if __name__ == "__main__":
    sys.exit(main())
