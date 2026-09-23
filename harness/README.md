# Repo harness

Mechanical guardrails so that any model (or human) editing this repo cannot commit a copyrighted
game binary, break a launch script, or repeat a mistake that has already cost an afternoon. Same
design as ResumeAI's harness: one stdlib-only rule engine (`harness/harness.py` + `rules.py`),
wired into three surfaces. Every message says how to fix the violation.

| Surface | When | What runs |
|---|---|---|
| Claude Code hook (PostToolUse on Edit\|Write, `.claude/settings.json`) | every AI edit | blob gate + file rules + line rules on the edited file; exit 2 feeds the violations back to the model |
| `pre-commit` (`.githooks/`) | every commit | blob gate + file rules on staged files, line rules on **added lines only**, repo invariants, commit budget |
| `pre-push` (`.githooks/`) | every push | every object the push uploads through the blob gate (any commit, so a `--no-verify` commit still gets caught), then the diff and tree rules on the outgoing commits |

Activation: the SessionStart hook runs `git config core.hooksPath .githooks`; do the same by hand
after a fresh clone.

## Tier 0 — the copyright gate (no escape)

A staged or pushed blob is rejected when any of these holds:

- path under `prefixes/`, `engines/`, `downloads/`, `wine/`, `build/`, `logs/`, `patches/wined3d/`,
  `patches/nxcompat/all/` (and the pre-reorganisation names)
- extension in the game/Wine/archive set (`.exe .dll .dat .big .bag .w3d .dds .bik .dmp .dylib .tar .xz .zip …`)
- content magic: PE (`MZ`), EA `BIGF`/`BIG4`, minidump, zip/gzip/xz/zstd/7z/rar, Mach-O, ELF
- any other binary (NUL bytes) unless `HARNESS_ALLOW_BINARY=1`; over 1 MB unless `HARNESS_ALLOW_LARGE_FILE=1`

`tree` also refuses a commit whose `.gitignore` lost one of the protective patterns.

## Tier 1 — per file

- **Syntax**: `zsh -n` / `sh -n` / `bash -n` by shebang, Python `compile`, JSON parse, `.reg` header.
- **Shebang + exec bit** on `.sh` (except `env.sh`) and on Python CLIs.
- **Size**: no code file over **600 lines** (`allow-large-file` escape in a comment).
- **Wine hygiene**: a script that runs `wine` must source `env.sh` (or export `WINEPREFIX`);
  never `~/.wine`; `winecfg -v` only `win10`; launch lines carry `-win`; no `winedbg` attach;
  `wineserver -k` only right after killing the game; no LARGEADDRESSAWARE.
- **Safety**: no `sudo` in scripts; no `rm -r` of a prefix/engine; a script that overwrites a
  `.dll/.big/.dat/.exe` must keep a `.orig`/`.bak`.
- **Python**: stdlib only (`sys.stdlib_module_names`), no bare `except:`, no `shell=True`.
- **Paths**: no `/Users/<name>/` or the old `Games/bfme` location in code.
- **Secrets**: API/GitHub/AWS/Slack keys, private keys, and a real CD key in a `.reg` `ergc` value.
- **Ini**: `Resolution` must be `1512 982` or `3024 1900` (`HARNESS_ALLOW_RESOLUTION=1` for another verified mode).

## Tier 2 — per change

- **Commit budget**: warn over 400 changed lines, block over 600 (`HARNESS_ALLOW_LARGE=1`).
- **README index**: every top-level script and `tools/*.py` is named in `README.md`.

Universal escape for line rules: `harness-allow` on the line. The blob gate and secrets have none.

## Running by hand

```
python3 harness/harness.py diff --staged      # what pre-commit sees
python3 harness/harness.py diff origin/main   # everything since the last push
python3 harness/harness.py tree               # invariants at HEAD
echo '{"tool_input":{"file_path":"'$PWD'/play-rotwk.sh"}}' | python3 harness/harness.py hook
```

## Adding a rule

Line hazards go in `LINE_RULES` (extension set, regex, fix message). Whole-file properties go in
`file_rules`; repo-wide ones in `tree_rules`. Calibrate against the tree before committing
(`diff` over the whole history must stay clean), and keep the message actionable.
