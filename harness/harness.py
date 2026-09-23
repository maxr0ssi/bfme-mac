#!/usr/bin/env python3
"""BFME-MAC repo harness — one rule engine, three surfaces (Claude hook, pre-commit, pre-push).

Subcommands:
  hook                          Claude Code PostToolUse (Edit|Write) — JSON on stdin, exit 2 = feedback
  loc     [--staged]            commit size budget: warn >400 changed lines, block >600
  diff    [--staged|--pre-push] blob gate + file rules on touched files, line rules on ADDED lines
  tree    [--staged|<rev>]      repo-wide invariants (.gitignore protection, README index)
  objects --pre-push            every object the push uploads: game/Wine binaries, archives, size

Escapes: 'harness-allow' on a line; HARNESS_ALLOW_LARGE=1 (commit budget);
HARNESS_ALLOW_LARGE_FILE=1 / HARNESS_ALLOW_BINARY=1 (non-game blobs only);
HARNESS_ALLOW_RESOLUTION=1. The copyright gate and secrets have no escape.
"""

import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules  # noqa: E402

WARN_LOC = 400
BLOCK_LOC = 600
ZERO = "0" * 40
TEXT_EXT = (".sh", ".py", ".md", ".ini", ".reg", ".ahk", ".json", ".txt", ".gitignore", "")


def sh(cmd, stdin=None):
    try:
        return subprocess.run(cmd, capture_output=True, check=False, input=stdin).stdout
    except OSError:
        return b""


def sht(cmd, stdin=None):
    return sh(cmd, stdin).decode("utf-8", "replace")


def repo_root():
    return sht(["git", "rev-parse", "--show-toplevel"]).strip()


def empty_tree():
    return sht(["git", "hash-object", "-t", "tree", "/dev/null"]).strip()


def report(violations):
    if not violations:
        return 0
    print("✖ Harness violations:", file=sys.stderr)
    seen = set()
    for path, line_no, msg, text in violations:
        key = (path, line_no, msg)
        if key in seen:
            continue
        seen.add(key)
        loc = f"{path}:{line_no}" if line_no else path
        print(f"  {loc}  {msg}", file=sys.stderr)
        if text:
            print(f"    {text}", file=sys.stderr)
    return 1


# ---------------------------------------------------------------------------
# git plumbing helpers
# ---------------------------------------------------------------------------

def blob_at(spec):
    """Bytes of `git show <spec>` (':path' for the index, '<sha>:path' for a commit), or None."""
    r = subprocess.run(["git", "show", spec], capture_output=True, check=False)
    return r.stdout if r.returncode == 0 else None


def mode_at(rev, path):
    if rev is None:
        out = sht(["git", "ls-files", "-s", "--", path])
    else:
        out = sht(["git", "ls-tree", rev, "--", path])
    return out.split()[0] if out.strip() else None


def added_lines(diff_args):
    """Parse `git diff -U0` into {path: [(line_no, text), ...]}."""
    out = {}
    path, line_no = None, 0
    for raw in sht(["git", "diff", "--unified=0", "--no-color"] + diff_args).splitlines():
        if raw.startswith("+++ "):
            p = raw[4:]
            path = None if p == "/dev/null" else p.removeprefix("b/")
        elif raw.startswith("@@"):
            m = re.search(r"\+(\d+)", raw)
            line_no = int(m.group(1)) if m else 0
        elif raw.startswith("+") and not raw.startswith("+++"):
            if path:
                out.setdefault(path, []).append((line_no, raw[1:]))
            line_no += 1
    return out


def touched(diff_args, filt="ACMR"):
    return [p for p in sht(["git", "diff", "--name-only", f"--diff-filter={filt}"] + diff_args).splitlines() if p]


def pre_push_ranges():
    """[(base, local_sha)] for every ref being pushed; base = remote tip or the empty tree."""
    ranges = []
    for line in sys.stdin.read().splitlines():
        parts = line.split()
        if len(parts) != 4 or parts[1] == ZERO:
            continue
        local, remote = parts[1], parts[3]
        if remote == ZERO:
            mb = sht(["git", "merge-base", local, "origin/main"]).strip()
            remote = mb or empty_tree()
        ranges.append((remote, local))
    return ranges


# ---------------------------------------------------------------------------
# loc
# ---------------------------------------------------------------------------

def cmd_loc(staged):
    total = 0
    for line in sht(["git", "diff", "--numstat"] + (["--cached"] if staged else [])).splitlines():
        parts = line.split("\t")
        if len(parts) != 3 or parts[0] == "-":
            continue
        total += int(parts[0]) + int(parts[1])
    if total > BLOCK_LOC and os.environ.get("HARNESS_ALLOW_LARGE") != "1":
        print(f"✖ Commit changes {total} lines (limit {BLOCK_LOC}). Split it, or HARNESS_ALLOW_LARGE=1 "
              f"for a genuine bulk change.", file=sys.stderr)
        return 1
    if total > WARN_LOC:
        print(f"⚠ Large commit: {total} changed lines (warn {WARN_LOC}, block {BLOCK_LOC}).", file=sys.stderr)
    return 0


# ---------------------------------------------------------------------------
# diff: blob gate + file rules on touched files, line rules on added lines
# ---------------------------------------------------------------------------

def check_range(base, head, root):
    """base/head: revisions, or (None, None) for the index. Returns violations."""
    diff_args = ["--cached"] if head is None else [f"{base}..{head}"]
    spec = (lambda p: f":{p}") if head is None else (lambda p: f"{head}:{p}")
    files = touched(diff_args)
    added = added_lines(diff_args)
    violations = []
    for path in files:
        data = blob_at(spec(path))
        if data is None:
            continue
        gate = rules.blob_gate(path, data[:8192], len(data))
        if gate:
            violations.extend(gate)
            continue
        ext = os.path.splitext(path)[1].lower()
        if ext not in TEXT_EXT and not path.endswith(".gitignore"):
            continue
        content = data.decode("utf-8", "replace")
        mode = mode_at(head, path)
        violations.extend(rules.file_rules(path, content, root, executable=(mode == "100755") if mode else None))
        for line_no, text in added.get(path, []):
            violations.extend(rules.line_rules(path, line_no, text))
    return violations


def cmd_diff(mode):
    root = repo_root()
    if mode == "--staged":
        return report(check_range(None, None, root))
    if mode == "--pre-push":
        violations = []
        for base, head in pre_push_ranges():
            violations.extend(check_range(base, head, root))
        return report(violations)
    base = mode or "origin/main"
    return report(check_range(base, "HEAD", root))


# ---------------------------------------------------------------------------
# tree: repo-wide invariants at the index or a revision
# ---------------------------------------------------------------------------

def cmd_tree(arg):
    if arg == "--staged":
        tracked = sht(["git", "ls-files", "--cached"]).splitlines()
        read = lambda p: (blob_at(f":{p}") or b"").decode("utf-8", "replace") or None  # noqa: E731
    else:
        rev = arg or "HEAD"
        tracked = sht(["git", "ls-tree", "-r", "--name-only", rev]).splitlines()
        read = lambda p: (blob_at(f"{rev}:{p}") or b"").decode("utf-8", "replace") or None  # noqa: E731
    return report(rules.tree_rules([t for t in tracked if t], read))


# ---------------------------------------------------------------------------
# objects: everything a push uploads, whatever commit it sits in
# ---------------------------------------------------------------------------

def cmd_objects():
    violations = []
    for _base, head in pre_push_ranges():
        listing = sht(["git", "rev-list", "--objects", head, "--not", "--remotes"])
        shas = {}
        for line in listing.splitlines():
            parts = line.split(" ", 1)
            if len(parts) == 2 and parts[1]:
                shas[parts[0]] = parts[1]
        if not shas:
            continue
        info = sht(["git", "cat-file", "--batch-check"], stdin="\n".join(shas).encode())
        for line in info.splitlines():
            parts = line.split()
            if len(parts) != 3 or parts[1] != "blob":
                continue
            sha, size = parts[0], int(parts[2])
            path = shas[sha]
            head_bytes = b"" if size > rules.MAX_FILE_BYTES else sh(["git", "cat-file", "blob", sha])[:8192]
            for v in rules.blob_gate(path, head_bytes, size):
                violations.append((f"{path} (blob {sha[:8]})", 0, v[2], ""))
    if violations:
        print("A pushed commit contains a forbidden object. Rewrite history before pushing "
              "(git rm --cached + amend/rebase); a private repo is still a copy on someone else's server.",
              file=sys.stderr)
    return report(violations)


# ---------------------------------------------------------------------------
# hook: Claude Code PostToolUse (Edit|Write)
# ---------------------------------------------------------------------------

def cmd_hook():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    file_path = payload.get("tool_input", {}).get("file_path", "")
    root = repo_root()
    if not root or not file_path.startswith(root + "/") or not os.path.isfile(file_path):
        return 0
    rel = os.path.relpath(file_path, root)
    try:
        with open(file_path, "rb") as fh:
            data = fh.read()
    except OSError:
        return 0
    violations = rules.blob_gate(rel, data[:8192], len(data))
    ext = os.path.splitext(rel)[1].lower()
    if not violations and (ext in TEXT_EXT or rel.endswith(".gitignore")):
        content = data.decode("utf-8", "replace")
        violations.extend(rules.file_rules(rel, content, root, executable=os.access(file_path, os.X_OK)))
        for i, text in enumerate(content.split("\n"), start=1):
            violations.extend(rules.line_rules(rel, i, text, ext))
        if rel in (".gitignore", "README.md"):
            tracked_paths = sht(["git", "ls-files", "--cached"]).splitlines()
            read = lambda p: open(os.path.join(root, p), encoding="utf-8", errors="replace").read() \
                if os.path.exists(os.path.join(root, p)) else None  # noqa: E731
            violations.extend(rules.tree_rules([t for t in tracked_paths if t], read))
    if violations:
        report(violations)
        return 2  # exit 2 feeds stderr back to the model as blocking feedback
    return 0


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__, file=sys.stderr)
        return 1
    cmd, rest = args[0], args[1:]
    if cmd == "hook":
        return cmd_hook()
    if cmd == "loc":
        return cmd_loc("--staged" in rest)
    if cmd == "diff":
        return cmd_diff(rest[0] if rest else "")
    if cmd == "tree":
        return cmd_tree(rest[0] if rest else "")
    if cmd == "objects":
        return cmd_objects()
    print(f"unknown subcommand: {cmd}\n{__doc__}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
