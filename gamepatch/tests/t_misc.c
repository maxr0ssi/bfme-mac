/* t_misc: the smaller patches.
 *   [1] every patch applies to the original bytes: the pages holding all patch sites are copied
 *       from the exe to their original addresses and each gp_patch_* is run (byte checks included);
 *   [2] floor/ceil: gp_floor/gp_ceil vs msvcr71's floor/ceil, 80-bit st0 results compared;
 *   [3] shutdown: gp_safe_release calls Release normally, and skips it only when the game's D3D9
 *       handle is gone and the vtable is no longer in a loaded module (a DLL really unloaded);
 *   [4] limiter: gp_limiter_wait vs the original Sleep(0) loop, exit time and CPU time.
 * usage: t_misc.exe <path to lotrbfme2ep1.exe 2.02> [sites]   (sites: only [1]) */
#include "orig.h"
#include "gp.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>

__asm__(".text\n"
"_call_d80:\n"            /* cdecl (fn, double x, void *out10): cdecl double -> st0 */
"  movl 4(%esp), %eax\n"
"  pushl 12(%esp)\n  pushl 12(%esp)\n"
"  call *%eax\n"
"  addl $8, %esp\n"
"  movl 16(%esp), %eax\n"
"  fstpt (%eax)\n"
"  ret\n");
void call_d80(void *fn, double x, void *out);

static uint32_t rng = 4242;
static uint32_t rnd(void) { rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5; return rng; }

/* ---- [3] fake COM objects ---- */
static LONG released;
static ULONG WINAPI fake_release(IUnknown *p) { (void)p; return (ULONG)InterlockedIncrement(&released); }
static void *fake_vtbl[3] = {NULL, NULL, (void *)fake_release};

/* ---- [4] the original limiter loop, as in the exe ---- */
static DWORD orig_wait(DWORD target, DWORD last)
{
    DWORD now;
    do { Sleep(0); now = timeGetTime(); } while (now - last < target);
    return now;
}
static double thread_cpu_ms(void)
{
    FILETIME c, e, k, u; GetThreadTimes(GetCurrentThread(), &c, &e, &k, &u);
    return (((uint64_t)k.dwHighDateTime << 32 | k.dwLowDateTime) + ((uint64_t)u.dwHighDateTime << 32 | u.dwLowDateTime)) / 1e4;
}

int main(int argc, char **argv)
{
    int fail = 0;
    setvbuf(stdout, NULL, _IONBF, 0);
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    HMODULE crt = LoadLibraryA("msvcr71.dll");
    void *crt_floor = GetProcAddress(crt, "floor"), *crt_ceil = GetProcAddress(crt, "ceil");

    /* [1] */
    static const uint32_t pages[][2] = {{0x441000, 0x1000}, {0x4f1000, 0x1000}, {0xb2b000, 0x1000},
        {0xb0d000, 0x2000}, {0xb26000, 0x1000}, {0x538000, 0x1000}, {0x63a000, 0x1000}, {0x51e000, 0x3000},
        {0x525000, 0x1000}, {0xbd0000, 0x1000}};
    uint32_t off = orig_reserve_image();
    if (!off) return 2;
    for (unsigned i = 0; i < sizeof pages / sizeof pages[0]; i++)
        if (orig_map_at(pages[i][0], pages[i][1], off)) return 2;
    gp_va_offset = off;
    *(void **)(0xbd0580 + off) = crt_floor;                           /* what the loader writes */
    *(void **)(0xbd0588 + off) = crt_ceil;
    int ok = gp_patch_dxlock() + gp_patch_invsqrt() + gp_patch_normtail() + gp_patch_hittest() +
             gp_patch_quatmat() + gp_patch_shutdown() + gp_patch_limiter() + gp_patch_floor();
    printf("[1] %d of 8 patches applied to the original bytes\n", ok);
    gp_va_offset = 0;
    fail |= ok != 8;
    if (argc > 2 && !strcmp(argv[2], "sites")) { printf("%s\n", fail ? "FAIL" : "PASS"); return fail; }

    /* [2] floor / ceil */
    uint64_t n = 0, bad = 0;
    for (int which = 0; which < 2; which++) {
        void *ref = which ? crt_ceil : crt_floor, *mine = which ? (void *)gp_ceil : (void *)gp_floor;
        for (int i = 0; i < 3000000; i++) {
            union { uint64_t u; double d; } x;
            switch (i % 6) {
            case 0: x.u = (uint64_t)rnd() << 32 | rnd(); break;                         /* any bits */
            case 1: x.d = ((int)(rnd() % 20001) - 10000) * 0.5; break;                  /* halves */
            case 2: x.d = ((int)(rnd() % 2001) - 1000) + ((int)(rnd() % 3) - 1) * 1e-9; break;
            case 3: x.d = ldexp((double)(int)rnd(), (int)(rnd() % 120) - 60); break;
            case 4: { static const uint64_t s[] = {0, 0x8000000000000000ull, 0x7ff0000000000000ull,
                        0xfff0000000000000ull, 0x7ff8000000000000ull, 0x7ff0000000000001ull, 1,
                        0x800fffffffffffffull, 0x4330000000000000ull, 0xc330000000000001ull,
                        0x3fe0000000000000ull, 0xbfe0000000000000ull, 0x3ff0000000000000ull};
                      x.u = s[rnd() % (sizeof s / 8)]; break; }
            default: x.d = (float)((int)(rnd() % 100000) - 50000) / 7.0f; break;       /* float-derived */
            }
            uint8_t a[16], b[16];
            call_d80(ref, x.d, a); call_d80(mine, x.d, b);
            n++;
            if (memcmp(a, b, 10)) { if (bad < 5) printf("  MISMATCH %s(%016llx)\n", which ? "ceil" : "floor", x.u); bad++; }
        }
    }
    printf("[2] floor/ceil: %llu inputs, %llu mismatches\n", n, bad);
    fail |= bad != 0;

    /* [3] safe release */
    static void *handle = (void *)1;
    gp_d3d9_handle_va = (uint32_t)(uintptr_t)&handle;
    IUnknown obj = { (IUnknownVtbl *)fake_vtbl };
    released = 0;
    gp_safe_release(&obj);                               /* d3d9 "loaded": always Release */
    handle = NULL;
    gp_safe_release(&obj);                               /* freed, but vtable in a loaded module */
    int normal = released == 2;
    HMODULE d = LoadLibraryA("d3d9.dll");
    void *inside_d3d9 = (void *)GetProcAddress(d, "Direct3DCreate9");
    FreeLibrary(d);
    MEMORY_BASIC_INFORMATION mbi; VirtualQuery(inside_d3d9, &mbi, sizeof mbi);
    IUnknown dangling = { (IUnknownVtbl *)inside_d3d9 };
    LONG sk = gp_safe_release_skipped;
    gp_safe_release(&dangling);
    printf("[3] shutdown: Release called while loaded / vtable in a live module: %s; d3d9.dll after "
           "FreeLibrary is %s; Release through it skipped: %s\n", normal ? "yes" : "NO",
           mbi.State == MEM_FREE ? "unmapped" : "still mapped", gp_safe_release_skipped == sk + 1 ? "yes" : "NO");
    fail |= !normal || (mbi.State == MEM_FREE && gp_safe_release_skipped != sk + 1);

    /* [4] limiter */
    timeBeginPeriod(1);
    {   /* how long Sleep(1) really takes here */
        int hist[8] = {0}; uint64_t mx = 0;
        for (int i = 0; i < 200; i++) {
            uint64_t a = now_us(); Sleep(1); uint64_t d = now_us() - a;
            if (d > mx) mx = d;
            hist[d / 1000 < 7 ? d / 1000 : 7]++;
        }
        printf("[4] Sleep(1) took <1/1-2/2-3/3-4/4+ ms: %d/%d/%d/%d/%d of 200 (max %.1f ms)\n", hist[0], hist[1],
               hist[2], hist[3], hist[4] + hist[5] + hist[6] + hist[7], mx / 1000.0);
    }
    static const DWORD targets[] = {33, 16, 10, 5};
    for (unsigned t = 0; t < sizeof targets / 4; t++) {
        for (int method = 0; method < 2; method++) {
            int over[8] = {0}; double cpu = 0, wall = 0; int frames = targets[t] > 20 ? 300 : 150;
            for (int f = 0; f < frames; f++) {
                DWORD last = timeGetTime();
                DWORD work = rnd() % (targets[t] - 1);            /* the frame's own work, busy */
                while (timeGetTime() - last < work) ;
                double c0 = thread_cpu_ms(); uint64_t w0 = now_us();
                DWORD now = method ? gp_limiter_wait(targets[t], last) : orig_wait(targets[t], last);
                cpu += thread_cpu_ms() - c0; wall += (now_us() - w0) / 1000.0;
                DWORD o = now - last - targets[t]; over[o < 7 ? o : 7]++;
                if (o > 2) printf("    (%s, frame %d: own work %lu ms, exit at target+%lu)\n",
                                  method ? "replacement" : "original", f, work, o);
            }
            printf("[4] target %2lu ms, %s: exit at target+0/+1/+2/+3..: %d/%d/%d/%d frames; waiting used "
                   "%.0f%% CPU\n", targets[t], method ? "replacement" : "original   ", over[0], over[1], over[2],
                   frames - over[0] - over[1] - over[2], wall > 0 ? 100 * cpu / wall : 0);
        }
    }
    printf("%s\n", fail ? "FAIL" : "PASS");
    return fail;
}
