#!/bin/zsh
# Inspect a hung/zombie RotWK process without killing it: is wow64cpu's page range still mapped,
# what protection does it have, and what do the faulting instruction and its data target contain.
P=$(pgrep -f 'lotrbfme2ep1.exe -win' | head -1)
[ -z "$P" ] && { echo "no game process"; exit 1; }
echo "pid $P  cpu $(ps -o pcpu= -p $P)  elapsed $(ps -o etime= -p $P)"
echo "--- mappings 0x7bf20000-0x7bf2ffff (wow64cpu.dll image):"
vmmap -wide $P 2>/dev/null | grep -iE "\b7bf2[0-9a-f]{4}-" | cut -c1-120
echo "--- data target 0x7bf2600c and code at the two fault sites:"
lldb --batch -p $P \
  -o "memory read --force -c 32 0x7bf26000" \
  -o "memory region 0x7bf2600c" \
  -o "disassemble --arch x86_64 -s 0x7bf21130 -c 4" \
  -o "disassemble --arch x86_64 -s 0x7bf21236 -c 4" \
  -o "detach" 2>&1 | grep -vE "^\(lldb\)|Process .* (stopped|detached)|^$|frame #|thread #|warning:|Executing|Target 0|^\*|Architecture set|Executable binary|libsystem|mach_msg|macx_"
