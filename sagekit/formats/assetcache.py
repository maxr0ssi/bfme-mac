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
A model the cache does not file is not drawn at all, even when an archive holds it: a model of
our own name needs a record (add_model).
"""
import os
import shutil
import struct

from .w3d import W3DFile

MODEL_TAGS = (b"REIH", b"HSEM", b"DOLH", b"MINA", b"XOB\0")   # hierarchy, mesh, HLOD, animation, box (reversed)


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

    def has_texture(self, name):
        return name.lower().encode("latin-1") in self.texture_names()

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
            entries = self._entries_at(data, at + len(key) + 8)     # skip the timestamp
            if entries:
                return entries
            at = data.lower().find(key, at + 1)     # the name also appears in dependency lists
        raise CacheError("no W3D record for %s in %s" % (model, self.path))

    @staticmethod
    def _entries_at(data, p):
        """The model record entries starting at p, or None if what is there is not one."""
        if p + 2 > len(data):
            return None
        count = struct.unpack_from("<H", data, p)[0]
        entries, q = [], p + 2
        for _ in range(count):
            if q >= len(data) or q + 13 + data[q] > len(data):
                return None
            n = data[q]
            tag = data[q + 1 + n:q + 5 + n]
            if tag not in MODEL_TAGS:
                return None
            offset, size = struct.unpack_from("<II", data, q + 5 + n)
            entries.append((data[q + 1:q + 1 + n].decode("latin-1", "replace"), tag, offset, size, q + 5 + n))
            q += 13 + n
        return entries or None

    def has_model(self, model):
        try:
            self.model_record(model)
            return True
        except CacheError:
            return False

    def stale_entries(self, w3d_path, model=None):
        """[(record entry, file entry)] whose offset/size differ. Raises if the entry names differ
        (the record cannot be patched in place then)."""
        model = model or os.path.basename(w3d_path).lower()
        records = []
        for n,s,e in self.sections()[0]:
            if n.lower() == model.lower().encode("latin-1"):
                rec = self._entries_at(self.data,s+1+len(n)+8)
                if rec:
                    records.append(rec)
        if not records:
            raise CacheError("no W3D record for %s in %s" % (model,self.path))
        have = W3DFile(w3d_path).cache_entries()
        stale = []
        for rec in records:
            if [(n.upper(), t) for n, t, _, _, _ in rec] != [(n.upper(), t) for n, t, _, _ in have]:
                raise CacheError("entry names/order differ - cannot patch in place (rebuild the cache)\n"
                                 "record entries: %s\nfile entries:   %s" % (
                                     [(n, t[::-1].decode()) for n, t, _, _, _ in rec],
                                     [(n, t[::-1].decode()) for n, t, _, _ in have]))
            stale += [(r, h) for r, h in zip(rec, have) if (r[2], r[3]) != (h[2], h[3])]
        return stale

    def patch_model(self, w3d_path, model=None):
        """Point the model's record at this file's layout. Returns report lines."""
        data = bytearray(self.data)
        lines = []
        for r, h in self.stale_entries(w3d_path, model):
            struct.pack_into("<II", data, r[4], h[2], h[3])
            lines.append("patched %-24s offset %d -> %d, size %d -> %d" % (r[0], r[2], h[2], r[3], h[3]))
        self.data = bytes(data)
        return lines or ["record already matches the file"]

    def add_model(self, new, like, w3d_path, own=False):
        """File model `new` (our copy of EA's `like` under another name: sagekit/owncopy.py,
        house.py) - the engine draws no model the cache does not file, even when an archive holds
        it. The asset record has like's timestamp and the file's own layout; the object records are
        like's, renamed (a dropped mesh left out, a mesh of ours without one given the textures it
        names). An earlier filing of `new` is replaced. own=True: `new` is a model of our own, not a
        copy (assets/cah/kit/attach.py): like gives only the timestamp and the cache; its HLOD record
        lists its own sub-objects and hierarchy, as EA's attached weapons' do. Returns report lines."""
        import re
        newb, likeb = new.lower().encode("latin-1"), like.lower().encode("latin-1")
        old_u, new_u = likeb[:-4].upper(), newb[:-4].upper()
        data = self.data
        assets, _, objs = self.sections(data)
        tmpl = next(((n, s) for n, s, e in assets if n.lower() == likeb and self._entries_at(data, s + 1 + len(n) + 8)), None)
        if tmpl is None:
            raise CacheError("no W3D record for %s to copy" % like)
        stamp = data[tmpl[1] + 1 + len(tmpl[0]):tmpl[1] + 9 + len(tmpl[0])]

        def ren(x):                                         # like's name in an object or dependency
            u = x.upper()
            for pre in (b"", b"H*"):
                if u == pre + old_u or u.startswith(pre + old_u + b"."):
                    return pre + new_u + u[len(pre) + len(old_u):]
            return u

        like_entries = {n.upper().encode("latin-1") for n, _, _, _, _ in self._entries_at(data, tmpl[1] + 9 + len(tmpl[0]))}
        like_names = {o.upper() for f, o, s, e in objs if f.lower() == likeb} | {b"H*" + old_u} | like_entries
        cloned = {}
        for f, o, s, e in objs:
            if f.lower() == likeb and ren(o) not in cloned:
                rec, deps = data[s:e], []
                p = 2 + rec[0] + rec[1 + rec[0]] + 2
                while p < len(rec):                         # sub-objects renamed, textures kept
                    d = rec[p + 1:p + 1 + rec[p]]
                    deps.append((ren(d) if d.upper() in like_names else d).lower())
                    p += 1 + rec[p]
                cloned[ren(o)] = cloned[o.upper()] = deps           # (a lone mesh keeps its name)
        gone = [0, 0]
        for f, o, s, e in reversed(objs):                   # objects come after every asset record
            if f.lower() == newb:
                data, gone[1] = data[:s] + data[e:], gone[1] + 1
        for n, s, e in reversed(assets):
            if n.lower() == newb:
                data, gone[0] = data[:s] + data[e:], gone[0] + 1
        data = data[:8] + struct.pack("<II", len(assets) - gone[0], len(objs) - gone[1]) + data[16:]

        f = W3DFile(w3d_path)
        entries = f.cache_entries()
        rec = bytes([len(newb)]) + newb + stamp + struct.pack("<H", len(entries))
        for name, tag, off, size in entries:
            nb = name.encode("latin-1")
            rec += bytes([len(nb)]) + nb + tag + struct.pack("<II", off, size)
        kept = {n.upper().encode("latin-1") for n, _, _, _ in entries if n}
        dropped = {ren(n).lower() for n in like_entries if ren(n) not in kept}       # `replaces`
        body, n_obj = b"", 0
        for name, tag, off, size in entries:
            key = (name or "").upper().encode("latin-1")
            if tag not in (b"HSEM", b"DOLH"):
                continue
            if own and tag == b"DOLH":                      # EA's form: 'model.mesh' ..., 'h*hierarchy'
                deps = [n.lower().encode("latin-1") for n, t, _, _ in entries if t == b"HSEM"]
                deps += [n.lower().encode("latin-1") for n, t, _, _ in entries if t == b"REIH"]
            elif own and tag == b"HSEM":
                deps = sorted({t.lower().encode("latin-1") for t in re.findall(
                    r"[A-Za-z0-9_\-]+\.(?:tga|dds|fx)", f.data[off:off + size].decode("latin-1"), re.I)})
            elif key in cloned:                             # the HLOD without the meshes we dropped
                deps = [d for d in cloned[key] if d not in dropped]
            elif tag == b"HSEM":
                deps = sorted({t.lower().encode("latin-1") for t in re.findall(
                    r"[A-Za-z0-9_\-]+\.(?:tga|dds|fx)", f.data[off:off + size].decode("latin-1"), re.I)})
            else:
                continue
            if deps:
                body += bytes([len(newb)]) + newb + bytes([len(key)]) + key + struct.pack("<H", len(deps))
                body += b"".join(bytes([len(d)]) + d for d in deps)
                n_obj += 1
        assets, end, objs = self.sections(data)
        at = next((s for n, s, e in assets if n.lower() > newb), end)
        data = data[:at] + rec + data[at:]
        at = next((s + len(rec) for fl, o, s, e in objs if fl.lower() > newb), len(data))
        data = data[:at] + body + data[at:]
        data = data[:8] + struct.pack("<II", len(assets) + 1, len(objs) + n_obj) + data[16:]
        self.sections(data)                                         # still parses end to end
        self.data = data
        return ["filed %s (copied from %s): %d entries, %d objects%s" % (
            new, like, len(entries), n_obj, ", replacing an earlier filing" if any(gone) else "")]

    # ------------------------------------------------------------------ textures
    def add_texture(self, new, like, model=None, obj=None):
        """Register texture `new` (copying `like`'s record) and, for model/obj, switch its dependency
        on `like` to `new`. Idempotent. Returns report lines."""
        done = []
        data = self.data
        newb, likeb = new.lower().encode("latin-1"), like.lower().encode("latin-1")
        if model:
            found = False
            # The HD caches contain duplicate objects. Reverse order keeps offsets valid
            # when replacement names differ in length; update every copy consistently.
            for f, o, s, e in reversed(self.sections(data)[2]):
                if f.lower() == model.lower().encode("latin-1") and o.upper() == obj.upper().encode("latin-1"):
                    found = True
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
            if not found:
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
