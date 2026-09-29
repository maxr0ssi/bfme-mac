# Draft Wine bug report: WoW64 `syscall_32to64` executed in 32-bit mode on macOS/Apple Silicon (Rosetta)

Status: not filed. Both games avoid the bug by running on Sikarugir's Wine 10.0 build.

**Summary.** In WoW64 mode on macOS 26.3 (Apple M3 Max, Rosetta 2), a 32-bit game (SAGE engine:
*LOTR: Battle for Middle-earth II / Rise of the Witch-king*, 2006) reliably kills its main thread at
one specific `NtWaitForSingleObject` call: the 64-bit `wow64cpu!syscall_32to64` entry is executed
**as 32-bit code**. Reproduced on wine-11.0 and wine-11.17 (Gcenx macOS builds, WoW64 mode).

**Evidence.** With `WINEDEBUG=+seh`, the first exception on the thread is
```
dispatch_exception code=c0000005 addr=000000007BF21139 info[0]=0 info[1]=0000000000004ECD
rip=7bf21110 rsp=1001ff5c0 rbp=22ddf0 rax=4 rbx=22dde0 rcx=3d6 rdx=f4d09000 rsi=22ddcb rdi=22de54 cs=002b ss=0000
```
`0x7BF20000` is the 64-bit `wow64cpu.dll` image mapped below 4 GB; `0x7BF21110` is `syscall_32to64`.
The 64-bit instruction stream there is

```
49 87 f4                 xchg  %r14,%rsp
41 89 bd 9c 00 00 00     movl  %edi,0x9c(%r13)
41 89 b5 a0 00 00 00     movl  %esi,0xa0(%r13)
41 89 9d a4 00 00 00     movl  %ebx,0xa4(%r13)
41 89 ad b4 00 00 00     movl  %ebp,0xb4(%r13)
41 8b 16                 movl  (%r14),%edx
41 89 95 b8 00 00 00     movl  %edx,0xb8(%r13)
8b 15 cd 4e 00 00        movl  cs32_sel(%rip),%edx      <- 0x7BF21139
```
Decoded as **32-bit** code the same bytes are `dec ecx; xchg esp,esi; inc ecx; mov [ebp+0x9c],edi;
... ; mov edx,[esi]; ... ; mov edx,[0x4ECD]`, which reproduces the dump exactly: `esi` = the old
ESP (0x22ddcb, unaligned), `edx` = bytes read from `[esi]` (0xf4d09000), `ecx` bumped by the
prefix bytes, and the fault is a read of the *displacement* `0x4ECD` (RotWK 2.02: same site;
Wine 11.17: `0x2DC1`/`0x2EC5`, its `cs32_sel` displacement). `rax=4` = NtWaitForSingleObject; in
another instance `rax=0x34` = NtDelayExecution.

Wine then dispatches the fault with the 64-bit context; `BTCpuResetToConsistentState` sees
`SegCs == cs64_sel` and does nothing; `call_seh_handlers` walks the 32-bit chain with a wrong
frame ("invalid frame ... not in stack limits" or a null handler), the game's handler recurses until
`stack overflow` and the thread is aborted. If it is a worker thread the process lingers.

**Trigger.** Deterministic per call site: right after ~15,000 64→32 user callbacks
(`KiUserCallbackDispatcher` / `RtlUnwindEx code=80000026 target_ip=<KiUserCallbackDispatcher>` /
`RtlRestoreContext` pairs from window-procedure calls while the game pumps messages on its loading
screen), the next syscall from 32-bit code enters `syscall_32to64` without the mode switch.
A worker thread of the same game dies the same way seconds after launch. The game also handles
thousands of its own access violations per load (lazy-commit memory pools), i.e. the exception
path is exercised heavily.

**Ruled out** (each tested with a hands-free harness): resolution/Retina, LARGEADDRESSAWARE,
Windows version (XP breaks wined3d init separately), `IsThreadedLoad`, shader-log printing,
executable-memory (`NX_COMPAT` on all 47 modules → no change), game data (BFME2 vanilla and RotWK
2.02 identical), `WINE_CPU_TOPOLOGY` (no effect in these builds). Wine Staging 11.17: same fault.
CrossOver 24 engine (Wine 9.0 base): different failure (32-bit RtlUnwind loop on the game's SEH
handlers), never reaches the site.

**Environment.** macOS 26.3.1 (Darwin 25.3.0), Apple M3 Max, Rosetta 2; Gcenx wine-stable 11.0_1
and wine-staging 11.17 osx64; game 32-bit, no NX_COMPAT (also tested with); wined3d/OpenGL.

**Reproducer without the game.** Wine's own 32-bit d3d9 test suite hits it:
`wine dlls/d3d9/tests/i386-windows/d3d9_test.exe visual` (WoW64, `WINEDEBUG=-all,err+seh`) aborts
within 1–3 s with no test output and `err:seh:NtRaiseException Exception frame is not in stack
limits`, in 2 to 4 runs out of 12 on wine-11.0 built from source. The other runs complete all
211,245 checks, so this is a race.

**Bisect.** Not a 10.0→11.0 regression. The oldest commit in `wine-10.0..wine-11.0` that runs at all
on macOS 26.3 is `8fd49c4d8e9` ("ntdll: Don't use private writable mappings on macOS"; everything
older fails with `could not load kernel32.dll`), and it already aborts in 9 of 12 runs; wine-10.5
3/12, wine-11.0 4/12. The defect predates the bisectable window; its rate drifts with the macOS
GSBASE-swap rework (`3a16aabbf55`, `928eb3a9b70`, `245e8cedf05`).

**Logs.** Excerpts attached: the `+seh` log from the first fault (above) and the `+seh +virtual` log
showing the fault right after the callback unwinds.
(Local copies, not for the report: `logs/rotwk-20260922-141331.log`, first fault at line 987715;
`logs/rotwk-20260922-150149.log`, line 87500.)
