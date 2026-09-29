#!/usr/bin/env python3
"""Rules for the BFME-MAC harness. Every check returns (path, line_no, message, text).

Four families:
  blob_gate     copyright/binary gate — game data, Wine builds, dumps, archives never enter git
  line_rules    per-line hazards in scripts/docs/ini/reg (added lines only on diff surfaces)
  file_rules    whole-file properties: syntax, shebang/exec bit, env.sh sourcing, guards
  tree_rules    repo-wide invariants: .gitignore integrity, the script index in docs/REFERENCE.md
"""

import ast
import json
import os
import re
import subprocess
import sys
import tempfile

ALLOW = "harness-allow"
MB = 1 << 20
MAX_FILE_BYTES = 1 * MB
MAX_FILE_LINES = 600  # per file, every touched code file (not only new ones)
LARGE_FILE_ALLOW = "allow-large-file"

# Packages at the repo root, importable from anywhere (see sagekit/__init__.py).
FIRST_PARTY = {"sagekit", "assets"}
# Code that runs inside Blender's bundled Python (3.11 with numpy), never on the system python3:
# the only places Blender's modules and numpy may be imported. Everything else stays stdlib-only,
# which also keeps sagekit's host side (formats, pipeline, cli) runnable without Blender.
BLENDER_ZONES = ("sagekit/blender/", "sagekit/paint/", "assets/")
BLENDER_MODULES = {"bpy", "bmesh", "mathutils", "bpy_extras", "numpy"}

# ---------------------------------------------------------------------------
# Copyright / binary gate. No escape hatch: EA's game data and Wine binaries are
# either copyrighted or rebuildable from the scripts, and the repo is on GitHub.
# ---------------------------------------------------------------------------

NEVER_COMMIT_DIRS = (
    "prefixes", "engines", "downloads", "wine", "build", "logs", "patches/wined3d",
    "patches/nxcompat/all", "__pycache__",
)
NEVER_COMMIT_EXT = {
    ".exe", ".dll", ".dat", ".big", ".bag", ".w3d", ".dds", ".tga", ".bik", ".wav", ".mp3",
    ".cah", ".sys", ".drv", ".ocx", ".msi", ".cab", ".dmp", ".dylib", ".so", ".tar", ".xz",
    ".zst", ".gz", ".bz2", ".zip", ".7z", ".rar", ".iso", ".dmg", ".bin", ".img", ".pak",
    ".bundle", ".chm", ".pyc",
}
MAGIC = [
    (b"MZ", "Windows PE executable/DLL"),
    (b"BIGF", "EA .big archive"),
    (b"BIG4", "EA .big archive"),
    (b"MDMP", "crash minidump"),
    (b"PK\x03\x04", "zip archive"),
    (b"\x1f\x8b", "gzip archive"),
    (b"\xfd7zXZ\x00", "xz archive"),
    (b"\x28\xb5\x2f\xfd", "zstd archive"),
    (b"BZh", "bzip2 archive"),
    (b"7z\xbc\xaf\x27\x1c", "7z archive"),
    (b"Rar!", "rar archive"),
    (b"\xcf\xfa\xed\xfe", "Mach-O binary"),
    (b"\xca\xfe\xba\xbe", "Mach-O universal binary"),
    (b"\x7fELF", "ELF binary"),
]


def blob_gate(path, head, size):
    """path: repo-relative; head: first bytes of the blob; size: full byte length."""
    out = []
    top = path.split("/")[0]
    if top.startswith("prefix") or any(path == d or path.startswith(d + "/") for d in NEVER_COMMIT_DIRS):
        out.append((path, 0, "game data / Wine build / prefix content must never be committed "
                    "(copyrighted or rebuildable) — unstage it and check .gitignore", ""))
        return out
    ext = os.path.splitext(path)[1].lower()
    if ext in NEVER_COMMIT_EXT:
        out.append((path, 0, f"'{ext}' files are game binaries, Wine builds or archives — never "
                    f"committed. Keep them under an ignored dir; document the download in README", ""))
        return out
    for magic, what in MAGIC:
        if head.startswith(magic):
            out.append((path, 0, f"content is a {what} — binaries are never committed, whatever "
                        f"the filename says", ""))
            return out
    if b"\x00" in head[:8192]:
        if os.environ.get("HARNESS_ALLOW_BINARY") != "1":
            out.append((path, 0, "binary file — this repo holds scripts and docs only. "
                        "HARNESS_ALLOW_BINARY=1 if it is genuinely yours and needed", ""))
        return out
    if size > MAX_FILE_BYTES and os.environ.get("HARNESS_ALLOW_LARGE_FILE") != "1":
        out.append((path, 0, f"{size // 1024} KB file (limit {MAX_FILE_BYTES // 1024} KB) — logs "
                    f"and captures belong in logs/. HARNESS_ALLOW_LARGE_FILE=1 to override", ""))
    return out


# ---------------------------------------------------------------------------
# Line rules
# ---------------------------------------------------------------------------

SH = (".sh",)
PY = (".py",)
STDLIB_ONLY_RE = r"^\s*(import|from)\s+(requests|pefile|numpy|PIL|yaml|lief)\b"
CODE = SH + PY
ANY = None
LAUNCH_RE = r"\bwine\b.*\b(lotrbfme2(ep1)?\.exe|game\.dat)\b"
GOOD_RESOLUTIONS = {("1512", "982"), ("3024", "1964")}

LINE_RULES = [
    # (extensions or None for all, regex, message)
    (CODE + (".ahk",), r"/Users/[A-Za-z0-9_]+/",
     "hardcoded home path — use $HOME or $BFME_ROOT so the scripts survive a move"),
    (SH, r"winecfg\s+-v\s+(?!win10\b)\S+",
     "keep the prefix at Windows 10: XP crashes wined3d at startup, other versions are untested"),
    (CODE, r"\bwinedbg\b(?!.*--help)",
     "never attach winedbg to a running WoW64 game (it kills it) — read the WINEDEBUG=+seh log or "
     "run tools/parse_minidump.py on the .dmp instead"),
    (SH, LAUNCH_RE + r"(?!.*\s-win\b)",
     "launch with -win: exclusive fullscreen minimizes on focus loss under the Mac driver and comes "
     "back black"),
    (SH, r"\bsudo\b",
     "scripts must not escalate (a hook or harness run would hang on the password prompt) — "
     "print the command for the user to run instead"),
    (SH, r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*\s+.*(prefix|engines|WINEPREFIX|Wine (Stable|Staging))",
     "never rm -r a prefix or engine (hours to rebuild) — mv it to a .trash-* dir and let the user delete"),
    (SH, r"WINEPREFIX=(\"?\$HOME|~)/\.wine\b",
     "this setup never uses ~/.wine — source env.sh (WINE_BUILD picks the prefix)"),
    (ANY, r"^(<<<<<<<|=======|>>>>>>>)( |$)", "merge-conflict marker"),
    (PY, r"^\s*except\s*:",
     "bare except hides the crash you are diagnosing — catch the specific exception"),
    (PY, STDLIB_ONLY_RE,
     "tools must run on the system python3 — stdlib only (urllib, struct, json, subprocess)"),
    (PY, r"\bshell\s*=\s*True\b",
     "subprocess with shell=True — pass an argv list (paths here contain spaces: 'Program Files (x86)')"),
]

SECRET_RULES = [
    (r"\bghp_[A-Za-z0-9]{36}\b", "GitHub token"),
    (r"\bgithub_pat_[A-Za-z0-9_]{60,}\b", "GitHub fine-grained token"),
    (r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b", "OpenAI-style API key"),
    (r"\bAKIA[0-9A-Z]{16}\b", "AWS access key"),
    (r"\bxox[bap]-[A-Za-z0-9-]{10,}\b", "Slack token"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private key block"),
]
CD_KEY_RE = re.compile(r'^\s*@="([A-Z0-9]{20})"\s*$')
RESOLUTION_RE = re.compile(r"^\s*Resolution\s*=\s*(\d+)\s+(\d+)\s*$")


def line_rules(path, line_no, text, ext=None):
    ext = ext if ext is not None else os.path.splitext(path)[1].lower()
    if ALLOW in text or path.startswith("harness/"):
        return []
    out = []
    for exts, pattern, msg in LINE_RULES:
        if exts is not None and ext not in exts:
            continue
        if pattern == STDLIB_ONLY_RE and path.startswith(BLENDER_ZONES) and "numpy" in text \
                and not re.search(r"\b(requests|pefile|PIL|yaml|lief)\b", text):
            continue
        if re.search(pattern, text):
            out.append((path, line_no, msg, text.strip()))
    for pattern, what in SECRET_RULES:
        if re.search(pattern, text):
            out.append((path, line_no, f"{what} in source — secrets never go in git, no escape", ""))
    if ext == ".reg":
        m = CD_KEY_RE.match(text)
        if m and not m.group(1).startswith("REPLACE"):
            out.append((path, line_no, "looks like a real CD key in an ergc value — keep the "
                        "REPLACEWITHYOURREALKEY00 placeholder in git, import the real key locally", ""))
    if ext == ".ini":
        m = RESOLUTION_RE.match(text)
        if m and (m.group(1), m.group(2)) not in GOOD_RESOLUTIONS \
                and os.environ.get("HARNESS_ALLOW_RESOLUTION") != "1":
            out.append((path, line_no, "Resolution must be a real display mode in points: 1512 982 "
                        "(native) or 3024 1964 (Retina, the whole screen: anything smaller leaves the menu bar and Dock "
                        "showing). 1920 1080 gives 'DirectX Error'. "
                        "HARNESS_ALLOW_RESOLUTION=1 for another verified mode", text.strip()))
    return out


# ---------------------------------------------------------------------------
# File rules (whole content)
# ---------------------------------------------------------------------------

SHELL_FOR = {"zsh": "zsh", "bash": "bash", "sh": "sh"}
SOURCED = ("env.sh", "lib.sh")   # sourced by the scripts, never run: no exec bit, no env.sh rule
WINE_CALL_RE = re.compile(r"^\s*(?:\(\s*)?(?:cd [^&;|]*&&\s*)?(?:exec\s+)?(wine|wineserver|wineboot|winetricks)\b", re.M)
OVERWRITE_RE = re.compile(r"\b(cp|mv|install|dd)\b[^\n#]*\.(dll|big|dat|exe)\b")
BACKUP_RE = re.compile(r"\.orig|\.bak|backup", re.I)


def _check_syntax(path, content, ext):
    if ext == ".py":
        try:
            compile(content, path, "exec")
        except SyntaxError as e:
            return [(path, e.lineno or 0, f"python syntax error: {e.msg}", "")]
        return []
    if ext == ".json":
        try:
            json.loads(content)
        except ValueError as e:
            return [(path, 0, f"invalid JSON: {e}", "")]
        return []
    if ext == ".sh":
        first = content.split("\n", 1)[0]
        m = re.match(r"#!\s*(?:/usr/bin/env\s+)?(?:/bin/|/usr/bin/)?(zsh|bash|sh)\b", first)
        if not m:
            return [(path, 1, "shell scripts need a shebang (#!/bin/zsh or #!/bin/sh) so the "
                     "syntax check and the exec bit mean something", first)]
        shell = SHELL_FOR[m.group(1)]
        with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as tmp:
            tmp.write(content)
        try:
            r = subprocess.run([shell, "-n", tmp.name], capture_output=True, text=True)
        finally:
            os.unlink(tmp.name)
        if r.returncode != 0:
            err = r.stderr.strip().replace(tmp.name, path)
            return [(path, 0, f"{shell} -n failed: {err}", "")]
        return []
    if ext == ".reg":
        first = content.lstrip("﻿").split("\n", 1)[0].strip()
        if first not in ("Windows Registry Editor Version 5.00", "REGEDIT4"):
            return [(path, 1, "a .reg file must start with 'Windows Registry Editor Version 5.00' "
                     "or Wine's regedit rejects it silently", first)]
    return []


def _stdlib_imports(path, content, root):
    out = []
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return out
    here = os.path.dirname(os.path.join(root, path))
    local_dirs = {here, os.path.join(root, "tools")}
    allowed = FIRST_PARTY | (BLENDER_MODULES if path.startswith(BLENDER_ZONES) else set())
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module]
        for name in names:
            top = name.split(".")[0]
            if top in sys.stdlib_module_names or top == "__future__" or top in allowed:
                continue
            if any(os.path.exists(os.path.join(d, top + ".py")) or os.path.isdir(os.path.join(d, top))
                   for d in local_dirs):
                continue
            out.append((path, node.lineno, f"third-party import '{top}' — tools must run on the "
                        f"system python3 with the stdlib only (Blender's modules and numpy: only "
                        f"under {', '.join(BLENDER_ZONES)})", ""))
    return out


def file_rules(path, content, root, executable=None):
    """content: full text. executable: True/False/None (None = unknown, skip the exec-bit rule)."""
    ext = os.path.splitext(path)[1].lower()
    out = _check_syntax(path, content, ext)
    lines = content.split("\n")
    base = os.path.basename(path)

    if ext == ".sh" and base not in SOURCED and content.startswith("#!") and executable is False:
        out.append((path, 0, "script has a shebang but no exec bit — chmod +x (git stores the mode)", ""))
    if ext == ".py" and re.search(r'^if __name__ == "__main__"', content, re.M) and executable is False:
        out.append((path, 0, "CLI tool without exec bit — chmod +x", ""))

    if ext == ".sh" and base not in SOURCED and WINE_CALL_RE.search(content):
        if not re.search(r"^\s*\.\s+\S*env\.sh\b|^\s*source\s+\S*env\.sh\b|^\s*export\s+WINEPREFIX=", content, re.M):
            out.append((path, 0, "this script runs wine but never sources env.sh (or exports "
                        "WINEPREFIX) — bare wine would use ~/.wine and whatever wine is on PATH", ""))

    if ext == ".sh":
        for i, text in enumerate(lines):
            if re.search(r"\bwineserver\s+-k\b", text) and ALLOW not in text and not text.lstrip().startswith("#"):
                window = "\n".join(lines[max(0, i - 4):i + 1])
                if not re.search(r"\bpkill\b|\bkill\b|kill_game", window):
                    out.append((path, i + 1, "wineserver -k with no game kill in the preceding lines "
                                "— it takes a running match down with it. pkill the game first "
                                "(see kill_game in test-skirmish.sh) or tag harness-allow", text.strip()))
        if OVERWRITE_RE.search(content) and not BACKUP_RE.search(content):
            out.append((path, 0, "this script overwrites a .dll/.big/.dat/.exe but keeps no "
                        ".orig/.bak copy — every binary patch here has needed reverting at least once", ""))

    if ext == ".py":
        out.extend(_stdlib_imports(path, content, root))

    if ext in CODE + (".ahk",) and len(lines) > MAX_FILE_LINES and LARGE_FILE_ALLOW not in content:
        out.append((path, 0, f"file is {len(lines)} lines (cap {MAX_FILE_LINES}) — split it into modules "
                    f"(tools/ for Python, a helper script for shell), or tag '{LARGE_FILE_ALLOW}' in a comment", ""))
    return out


# ---------------------------------------------------------------------------
# Tree rules
# ---------------------------------------------------------------------------

REQUIRED_IGNORES = [
    "prefixes/", "engines/", "downloads/", "wine/", "build/", "logs/", "patches/wined3d/",
    "patches/nxcompat/all/", "patches/nxcompat/*.exe", "patches/nxcompat/*.dat",
    "*.tar.xz", "*.dmp", "ahk/*.exe",
]
SCRIPT_DIRS_EXEMPT = ("harness/", ".githooks/")


def tree_rules(tracked, read):
    """tracked: list of repo-relative paths at the revision under test; read(path) -> text or None."""
    out = []
    gi = read(".gitignore") or ""
    patterns = {l.strip() for l in gi.splitlines() if l.strip() and not l.startswith("#")}
    for p in REQUIRED_IGNORES:
        if p not in patterns:
            out.append((".gitignore", 0, f"protective pattern '{p}' is missing — it is what keeps "
                        f"game data and Wine builds out of the repo", ""))
    # the index lives in docs/REFERENCE.md; the README (the landing page) may name scripts too
    readme = (read("README.md") or "") + (read("docs/REFERENCE.md") or "")
    for path in tracked:
        if path.startswith(SCRIPT_DIRS_EXEMPT) or not path.endswith((".sh", ".py", ".swift", ".ahk")):
            continue
        # a Python package the index names ("sagekit/") documents its own modules
        top = path.split("/")[0]
        if "/" in path and path.endswith(".py") and (top + "/") in readme \
                and os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), top, "__init__.py")):
            continue
        if os.path.basename(path) not in readme:
            out.append((path, 0, "not mentioned in docs/REFERENCE.md — every script gets a one-line "
                        "entry there so the next person (or model) knows it exists", ""))
    return out
