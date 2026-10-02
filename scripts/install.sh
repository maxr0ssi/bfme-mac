#!/bin/zsh
# scripts/install.sh — set up BFME2 and Rise of the Witch-king on this Mac from your own game folders.
#
#   scripts/install.sh --bfme2 <dir> [--rotwk <dir>] [options]
#   scripts/install.sh --buildings [list] | --no-buildings     (on an existing install)
#   scripts/install.sh --status
#   scripts/install.sh --uninstall
#
# Steps: check the Mac; download the Wine engine (Sikarugir Wine 10.0) and AutoHotkey, each pinned by
# SHA-256; install the patched Wine DLLs from the release file (the engine's own kept as
# <dll>.orig-w10, so scripts/wine-fixes.sh --revert also undoes them); create prefixes/w10; copy your
# game folders into it (the originals are never touched) and apply the edits the games need under Wine:
# no LODPreset rows (the pre-menu crash, tools/neuter_gamelod.py) and the 4 GB flag as each game ships
# it (tools/pe_laa.py: on for RotWK 2.02, off for BFME2; docs/MEMORY-4GB.md), both keeping .bak
# copies; write the registry, your CD key and an Options.ini at
# this display's resolution; install the game patch for RotWK 2.02 if its exe matches every patch site.
# RotWK is an expansion and needs BFME2 installed too. Re-running is safe: finished steps are skipped.
#
# Options:
#   --from <file>     install the fixes from a local bfme-mac-fixes-*.tar.gz (scripts/make-release.sh)
#                     instead of downloading the latest GitHub release
#   --group-pack      also build and install the group pack (MULTIPLAYER.md); everyone you play
#                     with needs the same one
#   --buildings [list]  also install the new buildings from the release (RotWK): every finished
#                     faction (dwarves,elves,men,goblins,isengard,mordor,angmar: Arnor uses Men's;
#                     each brings its builder) or a comma list. Without this flag the installer asks
#                     (default no). Everyone in a LAN game must choose
#                     the same. The packs hold none of EA's files: each is checked against your game
#                     and rebuilt from it (sagekit/pack.py); a faction whose EA files differ is skipped
#   --no-buildings    take them out again (asset.dat restored from the scoped backup)
#   --no-apps         don't put the app bundles in /Applications
#   BFME2_KEY= / ROTWK_KEY=   CD keys (asked for otherwise; Enter generates one, as the
#                     All-in-One Launcher does)
set -eu
export BFME_ROOT="${0:A:h:h}" WINE_BUILD=w10
. "$BFME_ROOT/scripts/lib.sh"
DL="$BFME_ROOT/downloads"; ENG="$BFME_ROOT/engines"
ENGINE_URL="https://github.com/Sikarugir-App/Engines/releases/download/v1.0/WS12WineSikarugir10.0_6.tar.xz"
ENGINE_SHA="9da7ee0cbf386522f3a9906943726d9c3c125dbbd9ab120e3cde80e88d6091b2"
TEMPLATE_URL="https://github.com/Sikarugir-App/Template/releases/download/v1.0/Template-1.0.18.tar.xz"
TEMPLATE_SHA="00d1fcb66aebdef51981b26476a2fe8cd600c39552166f0e733f57272d9e97b3"
TEMPLATE_APP="Template-1.0.18.app"
AHK_URL="https://github.com/AutoHotkey/AutoHotkey/releases/download/v1.1.37.02/AutoHotkey_1.1.37.02.zip"
AHK_SHA="6f3663f7cdd25063c8c8728f5d9b07813ced8780522fd1f124ba539e2854215f"
EA="drive_c/Program Files (x86)/Electronic Arts"

step() { print -P "%B==> $*%b"; }
die() { print -u2 "install.sh: $*"; exit 1; }
sha_ok() { [[ -f "$1" && "$(shasum -a 256 "$1" | cut -d' ' -f1)" == "$2" ]]; }
fetch() {  # fetch <url> <sha256> <dest>: download once, verify
  sha_ok "$3" "$2" && return 0
  mkdir -p "${3:h}"; echo "downloading ${1:t}"
  curl -fL --progress-bar -o "$3.part" "$1" || die "download failed: $1"
  sha_ok "$3.part" "$2" || { rm -f "$3.part"; die "checksum mismatch for ${1:t}"; }
  mv "$3.part" "$3"
}
LIBDIR() { print -r -- "$ENG/w10/wswine.bundle/lib/wine"; }

status() {
  local lib; lib=$(LIBDIR)
  [[ -x "$ENG/w10/wswine.bundle/bin/wine" ]] && echo "engine: $(cat "$ENG/w10/wswine.bundle/version")" || echo "engine: not installed"
  [[ -f "$lib/i386-windows/wined3d.dll.orig-w10" ]] && echo "Wine fixes: installed" || echo "Wine fixes: not installed"
  [[ -d "$BFME_ROOT/prefixes/w10" ]] && echo "prefix: prefixes/w10" || echo "prefix: not created"
  for g in BFME2 RotWK; do
    [[ -d "$BFME_ROOT/prefixes/w10/$EA/$g" ]] && echo "$g: installed" || echo "$g: not installed"
  done
  [[ -f "$BFME_ROOT/prefixes/w10/$EA/RotWK/gamepatch.ini" ]] && echo "game patch: installed" || echo "game patch: not installed"
  pack status
}

pack() { (cd "$BFME_ROOT" && python3 -m sagekit.pack "$@" --prefix "$BFME_ROOT/prefixes/w10"); }

uninstall() {
  game_running && die "a game is running; quit it first"
  local trash="$BFME_ROOT/.trash-$(date +%Y%m%d-%H%M%S)"
  echo "This moves engines/w10, engines/template and prefixes/w10 (your copied games AND saved games"
  echo "under its My ... Files folders) to ${trash:t}/ and removes the app bundles. downloads/ is kept."
  read "ans?Type 'uninstall' to continue: "
  [[ "$ans" == uninstall ]] || { echo "nothing changed"; exit 1; }
  [[ -z "$(pack status --list)" ]] || pack revert || echo "buildings not reverted; they go with the prefix"
  "$BFME_ROOT/scripts/make-apps.sh" --remove 2>/dev/null || true
  for l in "$ENG"/*.dylib(N@); do rm -f "$l"; done
  mkdir -p "$trash/engines" "$trash/prefixes"
  [[ -d "$ENG/w10" ]] && mv "$ENG/w10" "$trash/engines/"
  [[ -d "$ENG/template" ]] && mv "$ENG/template" "$trash/engines/"
  [[ -d "$BFME_ROOT/prefixes/w10" ]] && mv "$BFME_ROOT/prefixes/w10" "$trash/prefixes/"
  echo "moved to $trash; delete that folder to free the space (or move things back to undo)"
}

# ---- arguments
FROM="" SRC_BFME2="" SRC_ROTWK="" GROUP=0 APPS=1 BUILDINGS="" url=""
while (( $# )); do
  case "$1" in
    --from) FROM="${2:A}"; shift ;;
    --bfme2) SRC_BFME2="${2:A}"; shift ;;
    --rotwk) SRC_ROTWK="${2:A}"; shift ;;
    --group-pack) GROUP=1 ;;
    --buildings) if [[ $# -gt 1 && "$2" != -* ]]; then BUILDINGS="$2"; shift; else BUILDINGS=all; fi ;;
    --no-buildings) BUILDINGS=remove ;;
    --no-apps) APPS=0 ;;
    --status) status; exit 0 ;;
    --uninstall) uninstall; exit 0 ;;
    -h|--help) usage ;;
    *) usage 2 ;;
  esac
  shift
done
PFX="$BFME_ROOT/prefixes/w10"
have_bfme2() { [[ -n "$SRC_BFME2" || -d "$PFX/$EA/BFME2" ]]; }
[[ -z "$FROM" || -f "$FROM" ]] || die "no such file: $FROM"
ONLY_BUILDINGS=0   # --buildings / --no-buildings alone, on an existing install
[[ -z "$SRC_BFME2$SRC_ROTWK" && -n "$BUILDINGS" && -d "$PFX/$EA/RotWK" ]] && ONLY_BUILDINGS=1
if (( ONLY_BUILDINGS )) && [[ "$BUILDINGS" == remove ]]; then
  game_running && die "a game is running; quit it first"
  pack revert; exit 0
fi
[[ -n "$SRC_BFME2$SRC_ROTWK" ]] || (( ONLY_BUILDINGS )) || die "give your game folder(s): --bfme2 <dir> and/or --rotwk <dir>"
[[ -z "$SRC_BFME2" || -f "$SRC_BFME2/game.dat" && -f "$SRC_BFME2/lotrbfme2.exe" ]] || die "$SRC_BFME2 is not a BFME2 folder (no lotrbfme2.exe + game.dat)"
[[ -z "$SRC_ROTWK" || -f "$SRC_ROTWK/game.dat" && -f "$SRC_ROTWK/lotrbfme2ep1.exe" ]] || die "$SRC_ROTWK is not a RotWK folder (no lotrbfme2ep1.exe + game.dat)"
[[ -z "$SRC_ROTWK" ]] || have_bfme2 || die "RotWK is an expansion: give --bfme2 <dir> as well"

# ---- 1. this Mac
step "Checking this Mac"
[[ "$(sysctl -n hw.optional.arm64 2>/dev/null)" == 1 ]] || die "this needs an Apple Silicon Mac"
arch -x86_64 /usr/bin/true 2>/dev/null || die "Rosetta 2 is not installed. Run: softwareupdate --install-rosetta --agree-to-license"
game_running && die "a game is running; quit it first"

# ---- 2. the release file
if [[ -z "$FROM" ]]; then
  step "Latest release"
  # asset URL and GitHub's SHA-256 of it; SHA256SUMS inside is checked as well
  rel=$(curl -fsSL "https://api.github.com/repos/maxr0ssi/bfme-mac/releases/latest" 2>/dev/null | python3 -c '
import json, sys
a = [x for x in json.load(sys.stdin).get("assets", []) if x["name"].startswith("bfme-mac-fixes-") and x["name"].endswith(".tar.gz")]
print(a[0]["browser_download_url"], (a[0].get("digest") or "sha256:").split(":", 1)[1]) if a else None
' 2>/dev/null) || true
  [[ -n "$rel" ]] || die "no release found on GitHub; build one with scripts/make-release.sh and pass --from"
  url=${rel% *}; sha=${rel#* }; FROM="$DL/${url:t}"
  if [[ -n "$sha" ]]; then fetch "$url" "$sha" "$FROM"
  elif [[ ! -f "$FROM" ]]; then curl -fL --progress-bar -o "$FROM" "$url" || die "download failed: $url"; fi
fi
step "Checking the release file"
REL="$BFME_ROOT/build/install/release"
rm -rf "$REL"; mkdir -p "$REL"
tar -xzf "$FROM" -C "$REL" --strip-components 1
( cd "$REL" && shasum -a 256 -c --quiet SHA256SUMS ) || die "the release file is damaged (SHA256SUMS)"
[[ "$(cat "$REL/ENGINE")" == "${ENGINE_URL:t} $ENGINE_SHA" ]] || die "the release was built for another engine: $(cat "$REL/ENGINE")"

# the building packs (sagekit/pack.py): REL/BUILDINGS lines are "<faction> <file> <sha256> <bytes>"
installed_buildings=$(pack status --list)
if [[ -z "$BUILDINGS" && -s "$REL/BUILDINGS" ]] && [[ -n "$SRC_ROTWK" || -d "$PFX/$EA/RotWK" ]]; then
  if [[ -n "$installed_buildings" ]]; then
    BUILDINGS=$installed_buildings   # installed before: updated to this release's packs
  elif [[ -t 0 ]]; then
    typeset -A label=(dwarves Dwarves elves Elves men "Men (and Arnor)" goblins Goblins isengard Isengard mordor Mordor angmar Angmar)
    names=(); for f in $(cut -d' ' -f1 "$REL/BUILDINGS"); do names+=("${label[$f]:-$f}"); done
    echo "New buildings for ${(j:, :)names} ($(awk '{s += $4} END {printf "%d", s / 1048576}' "$REL/BUILDINGS") MB download)."
    read "ans?Install them? Everyone in a LAN game must choose the same (they change INI files; mismatched INIs desync) [y/N] "
    [[ "$ans" == [yY]* ]] && BUILDINGS=all || BUILDINGS=no
  fi
fi
buildings() {  # install the chosen packs from the release, or take them out
  [[ "$BUILDINGS" == (|no) ]] && return 0
  step "Buildings"
  if [[ "$BUILDINGS" == remove ]]; then pack revert; return 0; fi
  [[ -d "$PFX/$EA/RotWK" ]] || { echo "skipped: the buildings are for RotWK"; return 0; }
  [[ -s "$REL/BUILDINGS" ]] || die "this release has no building packs (${FROM:t})"
  local want=$BUILDINGS f n sha size src unpacked="$BFME_ROOT/build/install/buildings"
  local -a dirs
  [[ "$want" == all ]] && want=$(awk '{printf "%s%s", (NR > 1 ? "," : ""), $1}' "$REL/BUILDINGS")
  rm -rf "$unpacked"; mkdir -p "$unpacked"
  for f in ${(s:,:)want}; do
    read -r n sha size <<< "$(awk -v f="$f" '$1 == f {print $2, $3, $4}' "$REL/BUILDINGS")"
    [[ -n "$n" ]] || die "no $f buildings in this release (it has: $(cut -d' ' -f1 "$REL/BUILDINGS" | tr '\n' ' '))"
    src="${FROM:h}/$n"   # beside the release file: --from's folder, or downloads/
    if [[ -n "$url" ]]; then fetch "${url%/*}/$n" "$sha" "$src"
    else sha_ok "$src" "$sha" || die "$n (SHA-256 $sha) must be beside ${FROM:t}"; fi
    tar -xzf "$src" -C "$unpacked"
    dirs+=("$unpacked/${n%.tar.gz}")
  done
  echo "checking them against your game, rebuilding them from its files and updating asset.dat (a few minutes)"
  pack install "${dirs[@]}" || echo "buildings not installed (above)"
  rm -rf "$unpacked"
}
if (( ONLY_BUILDINGS )); then buildings; exit 0; fi

# ---- 3. Wine engine, its support libraries, AutoHotkey
step "Wine engine"
if [[ ! -x "$ENG/w10/wswine.bundle/bin/wine" ]]; then
  fetch "$ENGINE_URL" "$ENGINE_SHA" "$DL/${ENGINE_URL:t}"
  mkdir -p "$ENG/w10"; tar -xJf "$DL/${ENGINE_URL:t}" -C "$ENG/w10"
fi
if [[ ! -d "$ENG/template/$TEMPLATE_APP" ]]; then
  fetch "$TEMPLATE_URL" "$TEMPLATE_SHA" "$DL/${TEMPLATE_URL:t}"
  mkdir -p "$ENG/template"; tar -xJf "$DL/${TEMPLATE_URL:t}" -C "$ENG/template"
fi
# the engine dlopen()s FreeType, gnutls, MoltenVK... by name from here (env.sh)
for f in "$ENG/template/$TEMPLATE_APP/Contents/Frameworks/"*.dylib(N); do
  [[ -e "$ENG/${f:t}" ]] || ln -s "template/$TEMPLATE_APP/Contents/Frameworks/${f:t}" "$ENG/${f:t}"
done
echo "$(cat "$ENG/w10/wswine.bundle/version")"
if [[ ! -f "$BFME_ROOT/ahk/AutoHotkeyU32.exe" ]]; then
  fetch "$AHK_URL" "$AHK_SHA" "$DL/${AHK_URL:t}"
  unzip -oq "$DL/${AHK_URL:t}" AutoHotkeyU32.exe license.txt -d "$BFME_ROOT/ahk"
fi

# ---- 4. the Wine fixes
step "Wine fixes"
lib=$(LIBDIR)
for f in i386-windows/d3dx9_27.dll i386-windows/wined3d.dll; do
  [[ -f "$lib/$f.orig-w10" ]] || cp "$lib/$f" "$lib/$f.orig-w10"
  cp "$REL/wine/$f" "$lib/$f"
done
so="$lib/x86_64-unix/wined3d.so"
[[ -f "$so" && ! -f "$so.added-w10" ]] && die "$so exists and is not ours; not replacing it"
touch "$so.added-w10"; cp "$REL/wine/x86_64-unix/wined3d.so" "$so"
echo "d3dx9_27.dll, wined3d.dll, wined3d.so ($(grep -m1 '^Built from' "$REL/SOURCES.md"))"

# ---- 5. the prefix
step "Wine prefix (prefixes/w10)"
. "$BFME_ROOT/env.sh"
command -v wine >/dev/null || die "no wine in engines/w10"
mkdir -p "${WINEPREFIX:h}"   # wine creates the prefix, but not its parent
wine wineboot -u >/dev/null 2>&1 || true
wineserver -w   # the registry files are written when the wineserver exits
[[ -f "$WINEPREFIX/system.reg" ]] || die "wineboot did not create $WINEPREFIX (try: WINE_BUILD=w10 . ./env.sh; wine wineboot -u)"
wine winecfg -v win10 >/dev/null 2>&1 || true
wreg() { wine reg add "$@" /f >/dev/null 2>&1; }
wreg 'HKCU\Software\Wine\DllOverrides' /v '*d3dx9_27' /t REG_SZ /d builtin
wreg 'HKCU\Software\Wine\WineDbg' /v ShowCrashDialog /t REG_DWORD /d 0
wreg 'HKCU\Software\Wine\Direct3D' /v VideoMemorySize /t REG_SZ /d 4096
wreg 'HKCU\Software\Wine\Mac Driver' /v UsePreciseScrolling /t REG_SZ /d n
wineserver -w

# ---- 6. the games
cd_key() {  # cd_key <label> <preset>: the key, typed or generated
  local k="$2"
  if [[ -z "$k" && -t 0 ]]; then read -s "k?$1 CD key (Enter to generate one): "; echo; fi
  k=${${k:u}//[^A-Z0-9]/}
  [[ -n "$k" ]] || k=$(LC_ALL=C tr -dc 'A-Z0-9' </dev/urandom | head -c 20)
  print -r -- "$k"
}
options_ini() {  # options_ini <user data dir> <HeatEffects yes|no>
  local d="$PFX/drive_c/users/$USER/AppData/Roaming/$1"
  [[ -f "$d/Options.ini" ]] && return 0
  mkdir -p "$d"
  local res; res=$(system_profiler SPDisplaysDataType 2>/dev/null | awk '/UI Looks like:/ {print $4, $6; exit}')
  [[ "$res" == <->' '<-> ]] || res="1512 982"
  printf '%s\r\n' "AllHealthBars = yes" "AlternateMouseSetup = no" "AmbientVolume = 50.000000" \
    "AudioLOD = High" "Brightness = 50" "FixedStaticGameLOD = UltraHigh" "FlashTutorial = 0" \
    "HasGotOnline = yes" "HasSeenLogoMovies = yes" "HeatEffects = $2" "IdealStaticGameLOD = UltraHigh" \
    "IsThreadedLoad = yes" "MovieVolume = 70.000000" "MusicVolume = 70.000000" "Resolution = $res" \
    "SFXVolume = 70.000000" "ScrollFactor = 50" "StaticGameLOD = UltraHigh" "UnitDecals = yes" \
    "UseEAX3 = no" "VoiceVolume = 70.000000" > "$d/Options.ini"
  echo "Options.ini: UltraHigh, $res"
}
install_game() {  # install_game <dir name> <source> <reg file> <registry key name> <on|off: 4 GB> <exes...>
  local name=$1 src=$2 reg=$3 key=$4 laa=$5; shift 5
  local dst="$PFX/$EA/$name"
  step "$name"
  if [[ ! -d "$dst" ]]; then
    echo "copying $src ($(du -sh "$src" | cut -f1); instant on the same APFS volume)"
    rm -rf "$dst.part"; mkdir -p "${dst:h}"
    cp -cR "$src" "$dst.part" 2>/dev/null || { rm -rf "$dst.part"; cp -R "$src" "$dst.part"; }
    find "$dst.part" -maxdepth 1 -name '*.dmp' -delete   # crash dumps from the source install
    mv "$dst.part" "$dst"
  fi
  for b in "$dst"/(ini|INI|__patch202).big(N); do python3 "$BFME_ROOT/tools/neuter_gamelod.py" "$b" | tail -1; done
  local e; for e in "$@"; do python3 "$BFME_ROOT/tools/pe_laa.py" --$laa "$dst/$e" | sed "s|$dst/||"; done
  wine regedit /S "$BFME_ROOT/config/$reg"
  local kvar="${name:u}_KEY" k
  k=$(cd_key "$name" "${(P)kvar:-}")
  wreg "HKLM\\SOFTWARE\\WOW6432Node\\Electronic Arts\\Electronic Arts\\$key\\ergc" /ve /t REG_SZ /d "$k"
  wineserver -w
}
if [[ -n "$SRC_BFME2" ]]; then
  install_game BFME2 "$SRC_BFME2" bfme2.reg "The Battle for Middle-earth II" off lotrbfme2.exe game.dat
  options_ini "My Battle for Middle-earth II Files" yes
fi
if [[ -n "$SRC_ROTWK" ]]; then
  install_game RotWK "$SRC_ROTWK" rotwk.reg "The Lord of the Rings, The Rise of the Witch-king" on lotrbfme2ep1.exe game.dat
  options_ini "My Rise of the Witch-king Files" no
  [[ -f "$PFX/$EA/RotWK/__patch202.big" ]] || echo "note: no __patch202.big; the game patch and all measurements are for RotWK 2.02"
fi

# ---- 7. the game patch (RotWK 2.02)
G="$PFX/$EA/RotWK"
if [[ -d "$G" ]]; then
  step "Game patch"
  exe="Z:${G//\//\\}\\lotrbfme2ep1.exe"   # t_misc.exe only reads the exe's bytes
  chk=$(WINEDEBUG=-all wine "$REL/gamepatch/t_misc.exe" "$exe" sites 2>&1 | grep '^\[1\]' || true)
  if [[ "$chk" == *"8 of 8"* ]]; then
    [[ -f "$G/dinput8.dll" ]] && ! grep -aq "gamepatch proxy dinput8.dll for RotWK" "$G/dinput8.dll" && cp -p "$G/dinput8.dll" "$G/dinput8.dll.orig"
    cp "$REL/gamepatch/dinput8.dll" "$G/dinput8.dll"
    [[ -f "$G/gamepatch.ini" ]] || cp "$REL/gamepatch/gamepatch.ini" "$G/gamepatch.ini"
    echo "installed (scripts/game-patch.sh --revert removes it)"
  else
    echo "skipped: this lotrbfme2ep1.exe does not match every patch site (${chk:-check did not run})"
  fi
  wineserver -w
fi

# ---- 8. extras
if (( GROUP )) && [[ -d "$G" ]]; then
  step "Group pack"
  python3 "$BFME_ROOT/tools/make_group_pack.py" rotwk
  "$BFME_ROOT/scripts/install-mod.sh" rotwk "$BFME_ROOT/build/group-pack/rotwk/install"
fi
buildings
(( APPS )) && { step "App bundles"; "$BFME_ROOT/scripts/make-apps.sh"; }

step "Done"
status
[[ -d "$PFX/$EA/RotWK" ]] && echo "play: scripts/play-rotwk.sh" || echo "play: scripts/play-bfme2.sh"
echo "Before playing, set Energy Mode to High Power (System Settings > Battery). Guide: docs/PLAYING.md"
