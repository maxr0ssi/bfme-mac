/* perfmarker entry: replaces the first 6 bytes of PerfTimer begin 0x517690 (thiscall, 3 args,
 * ret 12; 30 call sites, one per render pass and one per mesh draw). The original copies the name
 * into the object (strncpy of 256 bytes, zero-padded, plus a second padded 64-byte strncpy) and
 * calls the D3DPERF_BeginEvent wrapper 0x51ece0, which reads nothing but the D3DPERF pointer
 * 0xdd361c and returns at once while it is null; nothing else reads the object's buffers (the end
 * marker 0x517740 -> 0x51ed60 only reads 0xdd3620). So while the pointer is null this returns
 * `this` right away, as the original does for a null name; ebx esi edi ebp are untouched, eax is
 * `this` either way, ecx and edx keep their values (the original clobbers them). The pointer is
 * read on every call: with passtimers (or PIX) installed the original runs unchanged. */
        .intel_syntax noprefix
        .data
        .globl _gp_perfmark_cont
        .balign 4
_gp_perfmark_cont:
        .long 0x00517696

        .text
        .globl _gp_perfmark
        .balign 16
_gp_perfmark:
        cmp     dword ptr ds:0xdd361c, 0
        je      1f
        mov     eax, dword ptr [esp+4]      /* the two instructions the jmp replaced */
        test    eax, eax
        jmp     dword ptr [_gp_perfmark_cont]
1:      mov     eax, ecx
        ret     12

/* The callers build the per-draw name before calling begin: MeshDX8Render 0x543150 / 0x543290
 * ("Rendering mesh\tDX8Render\t" + mesh name, rep movs + strlen + copy), MeshFXShader 0x573d3a
 * (_mbscpy + _mbscat) and 0x573dc6 (sprintf "Rendering %d meshes\tFXShader\t%s"). While the pointer
 * is null the whole block up to and including the begin call is skipped: it writes only the name
 * buffer and the timer object on the caller's stack (read by nothing then; the end marker only reads
 * 0xdd3620), calls only the pure getter 0x569ec0, the CRT string functions and begin, and leaves the
 * stack as it found it. At each resume point the registers the block changed are dead: 0x5431e7 and
 * 0x543326 redefine eax ecx (edx by mull or a load, esi before use; edi is only popped), 0x573d9a
 * redefines eax and pushes ecx only as a placeholder it overwrites, 0x573e1d redefines eax ebx ecx;
 * ebx esi edi ebp are not written by the FX blocks, and no flags are live. With the pointer set the
 * replaced instructions run and the original continues. */
        .data
        .globl _gp_pm_addr
        .balign 4
_gp_pm_addr:                    /* continue / skip-to addresses (+ test offset), set by the installer */
        .long 0x00543175, 0x005431e7, 0x005432b5, 0x00543326
        .long 0x00573d40, 0x00573d9a, 0x00573dce, 0x00573e1d

        .text
        .globl _gp_pm_dx8a, _gp_pm_dx8b, _gp_pm_fx1, _gp_pm_fxn
        .balign 16
_gp_pm_dx8a:                    /* 0x543170: mov ecx, 6 */
        cmp     dword ptr ds:0xdd361c, 0
        je      1f
        mov     ecx, 6
        jmp     dword ptr [_gp_pm_addr]
1:      jmp     dword ptr [_gp_pm_addr+4]
        .balign 16
_gp_pm_dx8b:                    /* 0x5432b0: mov ecx, 8 */
        cmp     dword ptr ds:0xdd361c, 0
        je      1f
        mov     ecx, 8
        jmp     dword ptr [_gp_pm_addr+8]
1:      jmp     dword ptr [_gp_pm_addr+12]
        .balign 16
_gp_pm_fx1:                     /* 0x573d3a: lea eax, [ebp-0x134] */
        cmp     dword ptr ds:0xdd361c, 0
        je      1f
        lea     eax, [ebp-0x134]
        jmp     dword ptr [_gp_pm_addr+16]
1:      jmp     dword ptr [_gp_pm_addr+20]
        .balign 16
_gp_pm_fxn:                     /* 0x573dc6: mov eax, [edi]; mov ecx, [eax+0xc4] */
        cmp     dword ptr ds:0xdd361c, 0
        je      1f
        mov     eax, dword ptr [edi]
        mov     ecx, dword ptr [eax+0xc4]
        jmp     dword ptr [_gp_pm_addr+24]
1:      jmp     dword ptr [_gp_pm_addr+28]
