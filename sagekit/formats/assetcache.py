"""The SAGE asset cache, asset.dat: BFME2/RotWK read models through it, not by parsing them.

Whole file (little-endian):
    "ALAE", u32 version, u32 asset count, u32 object count
    asset records:   u8 len, name, u64 FILETIME, u16 n, n x { u8 len, name, u32 tag, u32 offset, u32 size }
    object records:  u8 len file, u8 len object ("DBFORTRESS.DBFORTRESS"), u16 n, n x { u8 len, name }

A model's asset record caches the byte offset and size of every top-level chunk (tags "REIH"
hierarchy "H*name", "HSEM" mesh "CONTAINER.MESH", "DOLH" HLOD) and the engine reads those ranges
blind: a re-exported model with any layout change silently fails to render until its record is
patched. Textures have a record too (one "XET" entry, offset/size 0; BFME2's list is sorted
case-insensitively) and a texture without one is drawn as the engine's missing-texture magenta.
Object records list what each object depends on (its textures, sub-objects).
"""
import os
import shutil
import struct

from .w3d import W3DFile

MODEL_TAGS = (b"REIH", b"HSEM", b"DOLH")   # hierarchy, mesh, HLOD (reversed)


class CacheError(Exception):
    pass


class AssetCache:
    def __init__(self, path):
        self.path = path
        with open(path, "rb") as fh:
            self.data = fh.read()

    # ------------------------------------------------------------------ structure
    def sections(self, data=None):
        """(asset records [(name, start, end)], end of assets, object records [(file, obj, start, end)])."""
        data = self.data if data is None else data
        count, objects = struct.unpack_from("<II", data, 8)
        q, assets = 16, []
        for _ in range(count):
            s = q
            n = data[q]
            name = bytes(data[q + 1:q + 1 + n])
            q += 1 + n + 8
            k = struct.unpack_from("<H", data, q)[0]
            q += 2
            for _ in range(k):
                q += 1 + data[q] + 12
            assets.append((name, s, q))
        r, objs = q, []
        for _ in range(objects):
            s = r
            names = []
            for _ in range(2):
                names.append(bytes(data[r + 1:r + 1 + data[r]]))
                r += 1 + data[r]
            k = struct.unpack_from("<H", data, r)[0]
            r += 2
            for _ in range(k):
                r += 1 + data[r]
            objs.append((names[0], names[1], s, r))
        if r != len(data):
            raise CacheError("asset.dat does not parse to its end (%d of %d bytes)" % (r, len(data)))
        return assets, q, objs

    def texture_names(self):
        return [a[0].lower() for a in self.sections()[0]]

    def dependencies(self, model, obj):
        """The names object `obj` of `model` depends on, or None if there is no such object."""
        for f, o, s, e in self.sections()[2]:
            if f.lower() == model.lower().encode("latin-1") and o.upper() == obj.upper().encode("latin-1"):
                rec = self.data[s:e]
                p = 2 + rec[0] + rec[1 + rec[0]] + 2
                out = []
                while p < len(rec):
                    out.append(rec[p + 1:p + 1 + rec[p]].decode("latin-1"))
                    p += 1 + rec[p]
                return out
        return None

    # ------------------------------------------------------------------ model records
    def model_record(self, model):
        """[(entry name, tag, offset, size, position of offset in the file)] for a model."""
        data = self.data
        key = bytes([len(model)]) + model.lower().encode("latin-1")
        at = data.lower().find(key)
        while at >= 0:
            p = at + len(key) + 8                              # skip the timestamp
            if p + 2 <= len(data):
                count = struct.unpack_from("<H", data, p)[0]
                entries, q, ok = [], p + 2, True
                for _ in range(count):
                    if q >= len(data):
                        ok = False
                        break
                    n = data[q]
                    name = data[q + 1:q + 1 + n].decode("latin-1", "replace")
                    tag = data[q + 1 + n:q + 5 + n]
                    offset, size = struct.unpack_from("<II", data, q + 5 + n)
                    entries.append((name, tag, offset, size, q + 5 + n))
                    q += 13 + n
                if ok and entries and all(e[1] in MODEL_TAGS for e in entries):
                    return entries
            at = data.lower().find(key, at + 1)
        raise CacheError("no W3D record for %s in %s" % (model, self.path))

    def stale_entries(self, w3d_path, model=None):
        """[(record entry, file entry)] whose offset/size differ. Raises if the entry names differ
        (the record cannot be patched in place then)."""
        model = model or os.path.basename(w3d_path).lower()
        rec = self.model_record(model)
        have = W3DFile(w3d_path).cache_entries()
        if [(n.upper(), t) for n, t, _, _, _ in rec] != [(n.upper(), t) for n, t, _, _ in have]:
            raise CacheError("entry names/order differ - cannot patch in place (rebuild the cache)\n"
                             "record entries: %s\nfile entries:   %s" % (
                                 [(n, t[::-1].decode()) for n, t, _, _, _ in rec],
                                 [(n, t[::-1].decode()) for n, t, _, _ in have]))
        return [(r, h) for r, h in zip(rec, have) if (r[2], r[3]) != (h[2], h[3])]

    def patch_model(self, w3d_path, model=None):
        """Point the model's record at this file's layout. Returns report lines."""
        data = bytearray(self.data)
        lines = []
        for r, h in self.stale_entries(w3d_path, model):
            struct.pack_into("<II", data, r[4], h[2], h[3])
            lines.append("patched %-24s offset %d -> %d, size %d -> %d" % (r[0], r[2], h[2], r[3], h[3]))
        self.data = bytes(data)
        return lines or ["record already matches the file"]

    # ------------------------------------------------------------------ textures
    def add_texture(self, new, like, model=None, obj=None):
        """Register texture `new` (copying `like`'s record) and, for model/obj, switch its dependency
        on `like` to `new`. Idempotent. Returns report lines."""
        done = []
        data = self.data
        newb, likeb = new.lower().encode("latin-1"), like.lower().encode("latin-1")
        if model:
            for f, o, s, e in self.sections(data)[2]:
                if f.lower() == model.lower().encode("latin-1") and o.upper() == obj.upper().encode("latin-1"):
                    rec = bytearray(data[s:e])
                    head_len = 2 + rec[0] + rec[1 + rec[0]] + 2
                    p, deps = head_len, []
                    while p < len(rec):
                        deps.append(bytes(rec[p + 1:p + 1 + rec[p]]))
                        p += 1 + rec[p]
                    if likeb in [d.lower() for d in deps]:
                        swap = [newb if d.lower() == likeb else d for d in deps]
                        body = b"".join(bytes([len(d)]) + d for d in swap)
                        data = data[:s] + bytes(rec[:head_len]) + body + data[e:]
                        done.append("%s %s now depends on %s instead of %s" % (model, obj, new, like))
                    break
            else:
                raise CacheError("no object %s in %s" % (obj, model))
        assets = self.sections(data)[0]
        if any(a[0].lower() == newb for a in assets):
            self.data = data
            return done + ["%s already registered" % new]
        tmpl = [a for a in assets if a[0].lower() == likeb]
        if not tmpl:
            raise CacheError("no asset record for %s to copy" % like)
        _, s, e = tmpl[0]
        rec = bytes(data[s:e])
        rec = bytes([len(newb)]) + newb + rec[1 + rec[0]:]          # the record's name
        q = 1 + len(newb) + 8 + 2                                   # its one TEX entry
        rec = rec[:q] + bytes([len(newb)]) + newb + rec[q + 1 + rec[q]:]
        at = next((a[1] for a in assets if a[0].lower() > newb), assets[-1][2])
        data = data[:at] + rec + data[at:]
        data = data[:8] + struct.pack("<I", len(assets) + 1) + data[12:]
        self.sections(data)                                         # still parses end to end
        self.data = data
        return done + ["registered %s (copied from %s)" % (new, like)]

    # ------------------------------------------------------------------ saving
    def save(self, path=None, backup=True):
        """Write the cache; the first write next to an original keeps <path>.orig."""
        path = path or self.path
        if backup and os.path.exists(path) and not os.path.exists(path + ".orig"):
            shutil.copy2(path, path + ".orig")
        with open(path, "wb") as fh:
            fh.write(self.data)
