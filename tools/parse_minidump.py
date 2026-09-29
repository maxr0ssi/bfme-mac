#!/usr/bin/env python3
"""parse_minidump.py - print the exception, modules and system info of a Windows minidump.

The SAGE engine (BFME1/BFME2, C&C Generals) writes a standard ``MDMP`` minidump,
``DUMP_*.dmp``, next to the game's ``.exe`` when it crashes. This reads the exception, module
list and system-info streams with the stdlib only: what faulted and where. The pre-menu crash
(tools/neuter_gamelod.py) shows as a write access violation (``0xC0000005``) to ``0x08110000``
inside ``game.dat``.

    parse_minidump.py DUMP_1.06.2429.30210_*.dmp

Format reference: MINIDUMP_HEADER / _DIRECTORY / _EXCEPTION_STREAM /
MINIDUMP_MODULE_LIST / MINIDUMP_SYSTEM_INFO (Windows ``minidumpapiset.h``).
"""
from __future__ import annotations

import struct
import sys

# Stream types we care about.
EXCEPTION_STREAM = 6
MODULE_LIST_STREAM = 4
SYSTEM_INFO_STREAM = 7

ARCH = {0: "x86", 5: "ARM", 6: "IA64", 9: "x64", 12: "ARM64"}

# A few common NTSTATUS exception codes.
EXC = {
    0xC0000005: "EXCEPTION_ACCESS_VIOLATION",
    0xC000001D: "EXCEPTION_ILLEGAL_INSTRUCTION",
    0xC0000094: "EXCEPTION_INT_DIVIDE_BY_ZERO",
    0xC00000FD: "EXCEPTION_STACK_OVERFLOW",
    0x80000003: "EXCEPTION_BREAKPOINT",
    0xC0000409: "STATUS_STACK_BUFFER_OVERRUN",
}
AV_OP = {0: "read", 1: "write", 8: "execute (DEP)"}


def _u(fmt, data, off):
    return struct.unpack_from(fmt, data, off)


def read_minidump_string(data: bytes, rva: int) -> str:
    (length,) = _u("<I", data, rva)  # length in bytes of the UTF-16 text
    raw = data[rva + 4: rva + 4 + length]
    return raw.decode("utf-16-le", errors="replace")


def parse(data: bytes) -> dict:
    if data[0:4] != b"MDMP":
        raise ValueError(f"not a minidump (magic {data[0:4]!r})")
    _sig, _ver, n_streams, dir_rva = _u("<IIII", data, 0)
    streams = {}
    for i in range(n_streams):
        st, dsize, drva = _u("<III", data, dir_rva + i * 12)
        streams.setdefault(st, (dsize, drva))

    result: dict = {}

    # ---- system info ----
    if SYSTEM_INFO_STREAM in streams:
        _, rva = streams[SYSTEM_INFO_STREAM]
        arch, plevel, prev, ncpu, ptype = _u("<HHHBB", data, rva)
        maj, minor, build = _u("<III", data, rva + 8)
        result["system"] = {
            "arch": ARCH.get(arch, f"0x{arch:x}"),
            "cpus": ncpu,
            "windows": f"{maj}.{minor}.{build}",
        }

    # ---- modules (for attributing the fault address) ----
    modules = []
    if MODULE_LIST_STREAM in streams:
        _, rva = streams[MODULE_LIST_STREAM]
        (n_mods,) = _u("<I", data, rva)
        rec = rva + 4
        for _ in range(n_mods):
            base, = _u("<Q", data, rec)
            size, = _u("<I", data, rec + 8)
            name_rva, = _u("<I", data, rec + 20)
            name = read_minidump_string(data, name_rva)
            modules.append((base, size, name))
            rec += 108  # sizeof(MINIDUMP_MODULE)
    result["modules"] = modules

    # ---- the exception ----
    if EXCEPTION_STREAM in streams:
        _, rva = streams[EXCEPTION_STREAM]
        # MINIDUMP_EXCEPTION_STREAM: ThreadId, __align, then MINIDUMP_EXCEPTION
        exc = rva + 8
        code, flags = _u("<II", data, exc)
        addr, = _u("<Q", data, exc + 16)
        nparams, = _u("<I", data, exc + 24)
        params = [
            _u("<Q", data, exc + 32 + i * 8)[0] for i in range(min(nparams, 15))
        ]
        result["exception"] = {
            "code": code,
            "name": EXC.get(code, "unknown"),
            "address": addr,
            "params": params,
        }
    return result


def attribute(addr: int, modules) -> str | None:
    for base, size, name in modules:
        if base <= addr < base + size:
            short = name.split("\\")[-1]
            return f"{short}+0x{addr - base:X}"
    return None


def report(path: str) -> int:
    with open(path, "rb") as f:
        data = f.read()
    info = parse(data)

    print(f"# {path.split('/')[-1]}")
    if "system" in info:
        s = info["system"]
        print(f"  system     : {s['arch']}, {s['cpus']} CPU(s), Windows {s['windows']}")

    e = info.get("exception")
    if not e:
        print("  (no exception stream)")
        return 0

    where = attribute(e["address"], info["modules"]) or "unknown module"
    print(f"  exception  : 0x{e['code']:08X}  {e['name']}")
    print(f"  address    : 0x{e['address']:08X}  ({where})")
    if e["code"] == 0xC0000005 and len(e["params"]) >= 2:
        op = AV_OP.get(e["params"][0], f"op={e['params'][0]}")
        tgt = e["params"][1]
        ttgt = attribute(tgt, info["modules"]) or "unmapped"
        print(f"  access     : {op} of 0x{tgt:08X}  ({ttgt})")
    else:
        print(f"  params     : {[hex(p) for p in e['params']]}")
    return 0


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(__doc__)
        print("usage: parse_minidump.py DUMP_*.dmp [more.dmp ...]", file=sys.stderr)
        return 2
    rc = 0
    for path in argv:
        try:
            rc |= report(path)
        except (ValueError, FileNotFoundError, struct.error) as ex:
            print(f"{path}: error: {ex}", file=sys.stderr)
            rc = 1
        print()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
