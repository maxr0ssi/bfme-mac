#!/usr/bin/env python3
"""pe_laa.py - show, set or clear the LARGEADDRESSAWARE flag of a 32-bit Windows executable.

RotWK 2.02 ships lotrbfme2ep1.exe and game.dat with the flag on (4 GB of address space) and
runs that way on the w10 engine (docs/MEMORY-4GB.md, tools/laaprobe.c); BFME2 ships it off. The
first change to a file keeps <file>.preLAAoff.bak or <file>.preLAAon.bak.

    pe_laa.py <file>...            print on/off for each file
    pe_laa.py --off <file>...      clear the flag (no-op when it is already off)
    pe_laa.py --on <file>...       set the flag (no-op when it is already on)
"""
import argparse
import os
import shutil
import struct
import sys

LAA = 0x0020  # IMAGE_FILE_LARGE_ADDRESS_AWARE in the COFF header's Characteristics  harness-allow


def characteristics_offset(data):
    if data[:2] != b"MZ":
        raise ValueError("not a PE file (no MZ header)")
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe:pe + 4] != b"PE\0\0":
        raise ValueError("not a PE file (no PE signature)")
    return pe + 22


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--off", action="store_true", help="clear the flag")
    mode.add_argument("--on", action="store_true", help="set the flag")
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    for path in a.files:
        with open(path, "rb") as f:
            head = bytearray(f.read(4096))
        off = characteristics_offset(head)
        flags = struct.unpack_from("<H", head, off)[0]
        if not (a.off or a.on) or bool(flags & LAA) == a.on:
            print(f"{path}: LAA {'on' if flags & LAA else 'off'}")
            continue
        bak = path + (".preLAAon.bak" if a.on else ".preLAAoff.bak")
        if not os.path.exists(bak):
            shutil.copy2(path, bak)
        with open(path, "r+b") as f:
            f.seek(off)
            f.write(struct.pack("<H", flags | LAA if a.on else flags & ~LAA))
        print(f"{path}: LAA {'on' if a.on else 'off'} (previous kept as {os.path.basename(bak)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
