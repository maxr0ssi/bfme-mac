#!/usr/bin/env python3
"""pe_laa.py - show or clear the LARGEADDRESSAWARE flag of a 32-bit Windows executable.  (harness-allow: clears it)

RotWK 2.02 ships lotrbfme2ep1.exe and game.dat with the flag on (the 4 GB patch); under Wine it
crashes the game, so the installer turns it off. The first change keeps <file>.preLAAoff.bak.

    pe_laa.py <file>...            print on/off for each file
    pe_laa.py --off <file>...      clear the flag (no-op when it is already off)
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
    ap.add_argument("--off", action="store_true", help="clear the flag")
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    for path in a.files:
        with open(path, "rb") as f:
            head = bytearray(f.read(4096))
        off = characteristics_offset(head)
        flags = struct.unpack_from("<H", head, off)[0]
        if not a.off or not flags & LAA:
            print(f"{path}: LAA {'on' if flags & LAA else 'off'}")
            continue
        bak = path + ".preLAAoff.bak"
        if not os.path.exists(bak):
            shutil.copy2(path, bak)
        with open(path, "r+b") as f:
            f.seek(off)
            f.write(struct.pack("<H", flags & ~LAA))
        print(f"{path}: LAA off (original kept as {os.path.basename(bak)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
