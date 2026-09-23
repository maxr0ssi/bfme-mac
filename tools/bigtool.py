#!/usr/bin/env python3
"""bigtool — list / extract / replace / pack EA SAGE ``.big`` (BIGF) archives.

The BIGF container is the asset archive used by EA's **SAGE engine** — *Command
& Conquer: Generals* / *Zero Hour* and *The Lord of the Rings: The Battle for
Middle-earth 1 & 2*. ``ini.big`` (the file this repo's GameLOD fix edits),
``W3D.big``, ``Textures.big`` etc. are all BIGF archives.

Layout (validated against retail BFME2 ``ini.big``, v1.06, 666 members):

    off  size  field          endian   notes
    0    4     magic "BIGF"   -
    4    4     archiveSize    LITTLE    total file size in bytes
    8    4     numEntries     BIG
    12   4     dataStart      BIG       byte offset of the first member's data
    -- then numEntries index records, each: --
    +0   4     offset         BIG       member data offset from start of file
    +4   4     size           BIG       member size in bytes
    +8   var   name           ASCII, NUL-terminated, '\\' path separators

No compression — members are stored raw, so extract/replace is a byte copy.

Usage:
    bigtool.py list    archive.big
    bigtool.py extract archive.big [member] [-o OUTDIR]
    bigtool.py replace archive.big "data\\ini\\gamelodpresets.ini" new.ini [-o out.big]
    bigtool.py pack    OUTDIR archive.big        # rebuild from an extracted tree

This is a clean-room reimplementation of the public BIGF format; it ships no
game assets. Bring your own legally-owned copy of the game.
"""
from __future__ import annotations

import argparse
import os
import struct
import sys
from dataclasses import dataclass


@dataclass
class Entry:
    name: str          # original name, '\'-separated, as stored
    offset: int
    size: int


def _norm(name: str) -> str:
    """Normalize a member name for case-insensitive, separator-agnostic match."""
    return name.replace("/", "\\").lower()


def read_index(path: str) -> tuple[list[Entry], int]:
    """Return (entries, data_start). Raises ValueError on a non-BIGF file."""
    with open(path, "rb") as f:
        head = f.read(16)
        # BFME2/RotWK archives use the "BIG4" variant: identical layout, different magic.
        if len(head) < 16 or head[0:4] not in (b"BIGF", b"BIG4"):
            raise ValueError(f"{path}: not a BIGF/BIG4 archive (bad magic {head[0:4]!r})")
        global LAST_MAGIC
        LAST_MAGIC = bytes(head[0:4])
        # archiveSize is little-endian; everything else big-endian.
        num_entries = struct.unpack(">I", head[8:12])[0]
        data_start = struct.unpack(">I", head[12:16])[0]
        entries: list[Entry] = []
        for _ in range(num_entries):
            rec = f.read(8)
            if len(rec) < 8:
                raise ValueError(f"{path}: truncated index")
            offset, size = struct.unpack(">II", rec)
            name = bytearray()
            while True:
                ch = f.read(1)
                if not ch or ch == b"\x00":
                    break
                name += ch
            entries.append(Entry(name.decode("latin-1"), offset, size))
    return entries, data_start


def read_member(path: str, entry: Entry) -> bytes:
    with open(path, "rb") as f:
        f.seek(entry.offset)
        return f.read(entry.size)


LAST_MAGIC = b"BIGF"  # magic of the most recently read archive; build_big reuses it


def build_big(members: list[tuple[str, bytes]], magic: bytes | None = None) -> bytes:
    """Serialize (name, data) pairs into a BIGF/BIG4 archive, preserving order."""
    magic = magic or LAST_MAGIC
    index_size = sum(8 + len(name.encode("latin-1")) + 1 for name, _ in members)
    data_start = 16 + index_size
    # Index
    out = bytearray()
    cursor = data_start
    for name, data in members:
        out += struct.pack(">II", cursor, len(data))
        out += name.encode("latin-1") + b"\x00"
        cursor += len(data)
    # Member data
    for _, data in members:
        out += data
    archive_size = len(out) + 16
    header = magic + struct.pack("<I", archive_size) + struct.pack(">II", len(members), data_start)
    return header + bytes(out)


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #
def cmd_list(args) -> int:
    entries, _ = read_index(args.archive)
    total = 0
    for e in entries:
        print(f"{e.size:>10}  {e.name}")
        total += e.size
    print(f"\n{len(entries)} members, {total:,} bytes of data", file=sys.stderr)
    return 0


def cmd_extract(args) -> int:
    entries, _ = read_index(args.archive)
    outdir = args.output or "."
    wanted = _norm(args.member) if args.member else None
    n = 0
    for e in entries:
        if wanted and _norm(e.name) != wanted:
            continue
        rel = e.name.replace("\\", os.sep)
        dest = os.path.join(outdir, rel)
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        with open(dest, "wb") as out:
            out.write(read_member(args.archive, e))
        print(dest)
        n += 1
    if wanted and n == 0:
        print(f"error: member not found: {args.member}", file=sys.stderr)
        return 1
    return 0


def cmd_replace(args) -> int:
    entries, _ = read_index(args.archive)
    target = _norm(args.member)
    with open(args.newfile, "rb") as f:
        new_bytes = f.read()
    members: list[tuple[str, bytes]] = []
    found = False
    for e in entries:
        if _norm(e.name) == target:
            members.append((e.name, new_bytes))
            found = True
        else:
            members.append((e.name, read_member(args.archive, e)))
    if not found:
        print(f"error: member not found: {args.member}", file=sys.stderr)
        return 1
    out_path = args.output or args.archive
    if out_path == args.archive and not args.no_backup:
        bak = args.archive + ".bak"
        if not os.path.exists(bak):
            with open(bak, "wb") as b, open(args.archive, "rb") as src:
                b.write(src.read())
            print(f"backup -> {bak}", file=sys.stderr)
    with open(out_path, "wb") as out:
        out.write(build_big(members))
    print(f"wrote {out_path} ({os.path.getsize(out_path):,} bytes)", file=sys.stderr)
    return 0


def cmd_pack(args) -> int:
    root = args.indir
    members: list[tuple[str, bytes]] = []
    for dirpath, _dirs, files in os.walk(root):
        for fn in sorted(files):
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace(os.sep, "\\")
            with open(full, "rb") as f:
                members.append((rel, f.read()))
    members.sort(key=lambda m: _norm(m[0]))
    with open(args.archive, "wb") as out:
        out.write(build_big(members))
    print(f"packed {len(members)} members -> {args.archive}", file=sys.stderr)
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    pl = sub.add_parser("list", help="list members and sizes")
    pl.add_argument("archive")
    pl.set_defaults(func=cmd_list)

    pe = sub.add_parser("extract", help="extract one member or the whole archive")
    pe.add_argument("archive")
    pe.add_argument("member", nargs="?", help="member name (omit for all)")
    pe.add_argument("-o", "--output", help="output directory (default: .)")
    pe.set_defaults(func=cmd_extract)

    pr = sub.add_parser("replace", help="swap one member's bytes, rewrite the archive")
    pr.add_argument("archive")
    pr.add_argument("member")
    pr.add_argument("newfile")
    pr.add_argument("-o", "--output", help="write to a new file instead of in place")
    pr.add_argument("--no-backup", action="store_true")
    pr.set_defaults(func=cmd_replace)

    pp = sub.add_parser("pack", help="build a .big from an extracted directory tree")
    pp.add_argument("indir")
    pp.add_argument("archive")
    pp.set_defaults(func=cmd_pack)

    args = p.parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
