/* The smaller patches: installers for invsqrt / normtail (code in p_invsqrt.S), floor (p_floor.S),
 * and the shutdown crash and frame limiter replacements. */
#include "gp.h"
#include <string.h>
#include <cpuid.h>

void gp_norm_4f1710(void);
void gp_norm_b2b875(void);

/* ---- invsqrt: jmp from 0x441c56 to gp_invsqrt ------------------------------------------ */
int gp_patch_invsqrt(void)
{
    static const uint8_t head[] = {0xb8,0x08,0xb5,0x6e,0xbe};   /* mov eax, 0xbe6eb508 */
    gp_site s[2];
    gp_site_hash(&s[0], 0x441c56, 0x52, GP_FNV_441C56);
    gp_site_init(&s[1], 0x441c56, head, sizeof head);
    gp_rel32(&s[1], 0, 0xe9, (void *)gp_invsqrt);
    return gp_apply("invsqrt", s, 2);
}

/* ---- normtail: the x87 multiplies after the two hottest invsqrt calls -------------------- */
int gp_patch_normtail(void)
{
    static const uint8_t pre1[] = {0x0f,0x2e,0x05,0x94,0xb5,0xc1,0x00, 0x9f, 0xf6,0xc4,0x44,
                                   0xf3,0x0f,0x11,0x1e, 0xf3,0x0f,0x11,0x45,0x08, 0x7b,0x20};
    static const uint8_t t1[] = {0xd9,0x45,0x08, 0x51, 0xd9,0x1c,0x24, 0xe8,0x3a,0x05,0xf5,0xff,
                                 0xd9,0xc0, 0xd8,0x0e, 0xd9,0x1e, 0xd9,0xc0, 0xd8,0x4e,0x04, 0xd9,0x5e,0x04,
                                 0xd8,0x4e,0x08, 0xd9,0x5e,0x08};
    static const uint8_t post1[] = {0x8b,0xc6, 0x5e, 0xc9, 0xc2,0x08,0x00};
    static const uint8_t t2[] = {0x8b,0x44,0x24,0x08, 0x50, 0xe8,0xdb,0x63,0x91,0xff,
                                 0xd9,0xc0, 0xd8,0x0e, 0xd9,0x1e, 0xd9,0xc0, 0xd8,0x4e,0x04, 0xd9,0x5e,0x04,
                                 0xd9,0xc0, 0xd8,0x4e,0x08, 0xd9,0x5e,0x08, 0xd8,0x4e,0x0c, 0xd9,0x5e,0x0c,
                                 0x5e, 0xc3};
    gp_site s[4];
    gp_site_init(&s[0], 0x4f16fa, pre1, sizeof pre1); s[0].wlen = 0;
    gp_site_init(&s[1], 0x4f1710, t1, sizeof t1);
    memset(s[1].repl, 0xcc, sizeof t1);
    gp_rel32(&s[1], 0, 0xe8, (void *)gp_norm_4f1710);
    s[1].repl[5] = 0xeb; s[1].repl[6] = 0x4f1730 - 0x4f1717;
    gp_site_init(&s[2], 0x4f1730, post1, sizeof post1); s[2].wlen = 0;
    gp_site_init(&s[3], 0xb2b871, t2, sizeof t2);
    memset(s[3].repl + 4, 0xcc, sizeof t2 - 6);          /* keep mov eax,[esp+8] and pop esi; ret */
    gp_rel32(&s[3], 4, 0xe8, (void *)gp_norm_b2b875);
    s[3].repl[9] = 0xeb; s[3].repl[10] = 0xb2b897 - 0xb2b87c;
    return gp_apply("normtail", s, 4);
}

/* ---- floor/ceil imports -> SSE4.1 --------------------------------------------------------- */
int gp_patch_floor(void)
{
    static uint32_t of, oc;
    unsigned a, b, c, d;
    if (!__get_cpuid(1, &a, &b, &c, &d) || !(c & bit_SSE4_1)) {
        gp_log("floor: CPU has no SSE4.1; patch skipped");
        return 0;
    }
    HMODULE crt = GetModuleHandleA("msvcr71.dll");
    FARPROC f = crt ? GetProcAddress(crt, "floor") : NULL, g = crt ? GetProcAddress(crt, "ceil") : NULL;
    if (!f || !g) { gp_log("floor: msvcr71 floor/ceil not found; patch skipped"); return 0; }
    of = (uint32_t)(uintptr_t)f; oc = (uint32_t)(uintptr_t)g;
    gp_floor_orig = of; gp_ceil_orig = oc;
    gp_site s[2];
    gp_site_init(&s[0], 0xbd0580, (const uint8_t *)&of, 4);
    uint32_t nf = (uint32_t)(uintptr_t)gp_floor, nc = (uint32_t)(uintptr_t)gp_ceil;
    memcpy(s[0].repl, &nf, 4);
    gp_site_init(&s[1], 0xbd0588, (const uint8_t *)&oc, 4);
    memcpy(s[1].repl, &nc, 4);
    return gp_apply("floor", s, 2);
}

/* ---- shutdown: texture wrapper destructor 0x538580 releasing into an unloaded d3d9.dll -------
 * DX8Wrapper::Shutdown (0x5257a0) releases the device and FreeLibrary()s D3D9.DLL (handle kept at
 * 0xdd3610, zeroed afterwards). Texture wrappers that are static objects are destroyed later by
 * the CRT's atexit list, and 0x5385bd calls Release through a vtable that pointed into d3d9.dll:
 * the read at vtable+8 faults (13 of 15 RotWK crash dumps). The call is redirected here: while
 * D3D9.DLL is loaded (the game's handle is set) this is exactly p->Release(); after the game freed
 * it, the Release is skipped when the vtable is no longer inside any loaded module (the process is
 * exiting; nothing is left to free it into). */
volatile LONG gp_safe_release_skipped;
uint32_t gp_d3d9_handle_va = 0xdd3610;

ULONG WINAPI gp_safe_release(IUnknown *p)
{
    if (!p) return 0;
    if (!*(void *volatile *)(uintptr_t)gp_d3d9_handle_va) {
        HMODULE m;
        void *vt = *(void **)p;
        if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
                                GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT, (LPCWSTR)vt, &m)) {
            InterlockedIncrement(&gp_safe_release_skipped);
            return 0;
        }
    }
    return p->lpVtbl->Release(p);
}

int gp_patch_shutdown(void)
{
    static const uint8_t o[] = {0x8b,0x46,0x14, 0x8b,0x08, 0x50, 0xc6,0x44,0x24,0x18,0x01, 0xff,0x51,0x08};
    static const uint8_t n[] = {0x8b,0x46,0x14, 0x50, 0xc6,0x44,0x24,0x18,0x01};
    static const uint8_t ctx[] = {0xe8,0x0e,0x69,0xfe,0xff}; /* call 0x51eec0 (DX lock) just before */
    gp_site s[2];
    gp_site_init(&s[0], 0x5385ad, ctx, sizeof ctx); s[0].wlen = 0;
    gp_site_init(&s[1], 0x5385b2, o, sizeof o);
    memcpy(s[1].repl, n, sizeof n);
    gp_rel32(&s[1], 9, 0xe8, (void *)gp_safe_release);
    return gp_apply("shutdown", s, 2);
}

/* ---- limiter: GameEngine frame limiter spin 0x63a1dc-0x63a1f3 --------------------------------
 * Original: do { Sleep(0); now = timeGetTime(); } while (now - last < target); (edi = now)
 * Replacement: the same loop and exit test on timeGetTime, but Sleep(1) while more than `margin`
 * ms remain (default 2), Sleep(0) for the rest. The loop still ends at the first timeGetTime()
 * value with now - last >= target, so pacing changes only if a Sleep(1) overshoots by more than
 * the margin; a Sleep(1) seen taking longer than 2 ms widens the margin (up to 10 ms), and it
 * narrows again after 1024 normal sleeps. Off by default (main.c): a Sleep(1) can wake up late. */
DWORD gp_limiter_margin = 2;
static DWORD margin_now;
static unsigned calm;

DWORD WINAPI gp_limiter_wait(DWORD target, DWORD last)
{
    DWORD now = timeGetTime();
    if (margin_now < gp_limiter_margin) margin_now = gp_limiter_margin;
    while (now - last < target) {
        if (target - (now - last) > margin_now) {
            Sleep(1);
            DWORD t = timeGetTime(), took = t - now;
            if (took > 2 && took + 1 > margin_now) { margin_now = took + 1 < 10 ? took + 1 : 10; calm = 0; }
            else if (++calm >= 1024) { calm = 0; if (margin_now > gp_limiter_margin) margin_now--; }
            now = t;
        } else {
            Sleep(0);
            now = timeGetTime();
        }
    }
    return now;
}

int gp_patch_limiter(void)
{
    static const uint8_t pre[] = {0x3b,0xce, 0xa3,0x10,0x43,0xde,0x00, 0x73,0x19};
    static const uint8_t loop[] = {0x53, 0xff,0x15,0xb4,0x03,0xbd,0x00, 0xff,0x15,0x20,0x09,0xbd,0x00,
                                   0x8b,0xf8, 0x2b,0x05,0x18,0x43,0xde,0x00, 0x3b,0xc6, 0x72,0xe7};
    static const uint8_t post[] = {0x8b,0x75,0xe0, 0x89,0x3d,0x18,0x43,0xde,0x00};
    static const uint8_t n[] = {0xff,0x35,0x18,0x43,0xde,0x00,  /* push dword [last] */
                                0x56};                          /* push esi (target) */
    gp_site s[3];
    gp_site_init(&s[0], 0x63a1d3, pre, sizeof pre); s[0].wlen = 0;
    gp_site_init(&s[1], 0x63a1dc, loop, sizeof loop);
    memset(s[1].repl, 0x90, sizeof loop);
    memcpy(s[1].repl, n, sizeof n);
    gp_rel32(&s[1], 7, 0xe8, (void *)gp_limiter_wait);
    s[1].repl[12] = 0x8b; s[1].repl[13] = 0xf8;              /* mov edi, eax */
    s[1].repl[14] = 0xeb; s[1].repl[15] = 25 - 16;           /* jmp 0x63a1f5 */
    gp_site_init(&s[2], 0x63a1f5, post, sizeof post); s[2].wlen = 0;
    if (!gp_apply("limiter", s, 3)) return 0;
    timeBeginPeriod(1);   /* the game does this too (0x63a507); harmless twice, matters on Windows */
    return 1;
}
