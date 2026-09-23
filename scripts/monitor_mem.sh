#!/bin/zsh
# Sample the game's memory every 15 s: RSS, and dirty+swapped (i.e. committed private) memory
# mapped below 4 GB — the window a 32-bit game actually lives in.
export BFME_ROOT="${0:A:h:h}"
out="$BFME_ROOT/logs/mem-$(date +%Y%m%d-%H%M%S).log"
echo "time rss_mb committed32_mb regions32" > "$out"
while true; do
  pid=$(pgrep -f '^game.dat' | head -1)
  [ -z "$pid" ] && { echo "$(date +%T) game gone" >> "$out"; break; }
  rss=$(ps -o rss= -p $pid | tr -d ' ')
  va=$(vmmap -wide "$pid" 2>/dev/null | python3 -c '
import re,sys
tot=0; n=0
unit={"K":1<<10,"M":1<<20,"G":1<<30}
for line in sys.stdin:
    m=re.search(r"\b([0-9a-f]{6,16})-([0-9a-f]{6,16})\s+\[\s*([\d.]+)([KMG])\s+([\d.]+)([KMG])\s+([\d.]+)([KMG])\s+([\d.]+)([KMG])\s*\]", line)
    if not m: continue
    s=int(m.group(1),16)
    if s >= 1<<32: continue
    dirty=float(m.group(7))*unit[m.group(8)]; swap=float(m.group(9))*unit[m.group(10)]
    tot += dirty+swap; n+=1
print(int(tot)>>20, n)')
  echo "$(date +%T) $((rss/1024)) $va" >> "$out"
  sleep 15
done
