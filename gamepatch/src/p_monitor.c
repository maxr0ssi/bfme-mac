/* monitor: per-frame session data for scripts/monitor.sh (counters and reads only; no game result
 * changes). On only while GAMEPATCH_MONITOR names an output file (scripts/play-rotwk.sh sets it to
 * logs/sessions/<id>/game.txt); [patches] monitor=0 turns it off.
 *
 * What it records:
 *  - every drawn frame (renderstats' render-helper hook, p_rstats.c gp_rst_frame, so renderstats must be
 *    on; it is by default): the time (QueryPerformanceCounter), the logic frame (TheGameLogic
 *    0xde412c +0x40) and the D3DX calls since the previous frame, by kind, with the time spent in them:
 *      load    D3DXCreateTextureFromFileInMemoryEx (0x530ef3, 0x53117e: every texture file the
 *              game loads, PERFORMANCE.md §13), D3DXLoadSurfaceFromFileInMemory (0x530ec2), the cube
 *              (0x531515) and volume (0x53147c) loaders
 *      create  D3DXCreateTexture (0x5200d6, 0x520112, 0x530e8c, 0x531100), D3DXCreateVolumeTexture (0x53132e)
 *      fx      D3DXCreateEffect (0x551356), D3DXCreateEffectFromFileA (0x5513a3)
 *    Each site is a 5-byte `call thunk`; it becomes a call to a wrapper with the import's exact
 *    stdcall signature (Wine's d3dx9_27.spec), which calls the thunk with the same arguments.
 *  - once a second, on the main thread inside the frame hook (logic is not running then): the objects
 *    in TheGameLogic's list (+0xac first, Object +0x8c next; every pointer is checked against a
 *    committed, readable region before it is read, so a wrong guess ends the walk instead of
 *    faulting) and the game mode (+0x110).
 *  - every monitor_vm_secs (default 2) on the writer thread: the 32-bit address space by VirtualQuery
 *    (committed, reserved, free, largest free block), what decides the 2 / 4 GB limit.
 * A writer thread drains the frame ring every 250 ms into the output file; the main thread only
 * stores one record per frame. It also names the main thread "bfme_main" (SetThreadDescription;
 * under Wine the macOS thread gets the name), so the host sampler can tell it from the others.
 * Output (text, one record per line; us = microseconds since the monitor started):
 *   t us unix_ms tick_ms              clock pairs, every second (tick = GetTickCount, the clock of
 *                                     WINEDEBUG=+timestamp)
 *   f us logic load_n load_us create_n create_us fx_n fx_us     one per drawn frame
 *   s us objects mode logic walk_us
 *   m us committed_mb reserved_mb free_mb largest_free_mb regions walk_us total_mb
 *   d dropped_frames                  (only if the writer fell behind)
 * Test: gamepatch/tests/t_monitor.c. */
#include "gp.h"
#include "gp_render.h"
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <stdlib.h>

#define GAMELOGIC 0xde412c

enum { K_LOAD, K_CREATE, K_FX, K_N };
static volatile LONG cnt[K_N];
static volatile LONGLONG tim[K_N];
uint32_t gp_mon_fn[8];                  /* the thunks the patched sites called (tests replace them) */
int gp_mon_on, gp_mon_start_writer = 1;
static LONGLONG freq, q0;
static HANDLE out = INVALID_HANDLE_VALUE;
static int vm_secs = 2;

static LONGLONG qpc(void) { LARGE_INTEGER x; QueryPerformanceCounter(&x); return x.QuadPart; }
static LONGLONG us(LONGLONG dq) { return dq * 1000000 / freq; }
static void acct(int k, LONGLONG t0)
{
    LONGLONG d = qpc() - t0;
    __atomic_fetch_add(&cnt[k], 1, __ATOMIC_RELAXED);
    __atomic_fetch_add(&tim[k], d, __ATOMIC_RELAXED);
}

/* ---- the wrappers: same arguments and stdcall pop count as the import -------------------- */
typedef void *P; typedef UINT U;
#define WRAP(name, idx, kind, PARAMS, ARGS) \
    __attribute__((force_align_arg_pointer)) HRESULT WINAPI gp_mon_##name PARAMS \
    { typedef HRESULT (WINAPI *f_t) PARAMS; LONGLONG t0 = qpc(); \
      HRESULT r = ((f_t)(uintptr_t)gp_mon_fn[idx]) ARGS; acct(kind, t0); return r; }
WRAP(texload, 0, K_LOAD, (P a, P b, U c, U d, U e, U f, U g, U h, U i, U j, U k, U l, P m, P n, P o),
     (a, b, c, d, e, f, g, h, i, j, k, l, m, n, o))
WRAP(surfload, 1, K_LOAD, (P a, P b, P c, P d, U e, P f, U g, U h, P i), (a, b, c, d, e, f, g, h, i))
WRAP(cubeload, 2, K_LOAD, (P a, P b, U c, U d, U e, U f, U g, U h, U i, U j, U k, P l, P m, P n),
     (a, b, c, d, e, f, g, h, i, j, k, l, m, n))
WRAP(volload, 3, K_LOAD, (P a, P b, U c, U d, U e, U f, U g, U h, U i, U j, U k, U l, U m, P n, P o, P p),
     (a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p))
WRAP(create, 4, K_CREATE, (P a, U b, U c, U d, U e, U f, U g, P h), (a, b, c, d, e, f, g, h))
WRAP(volcreate, 5, K_CREATE, (P a, U b, U c, U d, U e, U f, U g, U h, P i), (a, b, c, d, e, f, g, h, i))
WRAP(fx, 6, K_FX, (P a, P b, U c, P d, P e, U f, P g, P h, P i), (a, b, c, d, e, f, g, h, i))
WRAP(fxfile, 7, K_FX, (P a, P b, P c, P d, U e, P f, P g, P h), (a, b, c, d, e, f, g, h))

void *const gp_mon_wrappers[8] = {gp_mon_texload, gp_mon_surfload, gp_mon_cubeload, gp_mon_volload,
                                  gp_mon_create, gp_mon_volcreate, gp_mon_fx, gp_mon_fxfile};   /* tests */

/* ---- reads of game memory: only from committed, readable regions ------------------------- */
static struct { uintptr_t lo, hi; } rc[8];
static unsigned rc_next;
static int region_ok(uintptr_t p, uint32_t len)
{
    for (unsigned i = 0; i < 8; i++)
        if (p >= rc[i].lo && p + len <= rc[i].hi && p + len > p) return 1;
    MEMORY_BASIC_INFORMATION mi;
    if (!VirtualQuery((void *)p, &mi, sizeof mi) || mi.State != MEM_COMMIT ||
        (mi.Protect & (PAGE_NOACCESS | PAGE_GUARD)) || !(mi.Protect & 0xee)) return 0;  /* any readable */
    uintptr_t lo = (uintptr_t)mi.BaseAddress, hi = lo + mi.RegionSize;
    rc[rc_next & 7].lo = lo; rc[rc_next & 7].hi = hi; rc_next++;
    return p + len <= hi && p + len > p;
}
static uint8_t *logic(void)
{
    uint8_t *gl = *(uint8_t *volatile *)GAMELOGIC;
    return gl && region_ok((uintptr_t)gl, 0x114) ? gl : NULL;
}

/* ---- per frame (main thread) -------------------------------------------------------------- */
typedef struct { LONGLONG q; uint32_t logic; LONG n[K_N]; LONGLONG t[K_N]; } frec;
#define RN 4096
static frec ring[RN];
static volatile LONG wpos, rpos, dropped;
static struct { LONGLONG q; LONG objects, mode, walk_us; uint32_t logic; } os_;
static volatile LONG os_seq;
static LONGLONG last_os;

static void objects_sample(LONGLONG q)
{
    uint8_t *gl = logic();
    LONG n = -1, mode = -1;
    if (gl) {
        mode = *(LONG *)(gl + 0x110);
        uintptr_t o = *(uintptr_t *)(gl + 0xac);
        for (n = 0; o && n < 200000; n++) {
            if (!region_ok(o + 0x8c, 4)) { n = -2; break; }
            o = *(uintptr_t *)(o + 0x8c);
        }
    }
    os_.q = q; os_.objects = n; os_.mode = mode; os_.logic = gl ? *(uint32_t *)(gl + 0x40) : 0;
    os_.walk_us = (LONG)us(qpc() - q);
    __atomic_add_fetch(&os_seq, 1, __ATOMIC_RELEASE);
}

void gp_mon_frame(void)
{
    LONG w = wpos;
    LONGLONG q = qpc();
    if (w - __atomic_load_n(&rpos, __ATOMIC_ACQUIRE) >= RN) { dropped++; return; }
    frec *r = &ring[w & (RN - 1)];
    uint8_t *gl = logic();
    r->q = q; r->logic = gl ? *(uint32_t *)(gl + 0x40) : 0;
    for (int k = 0; k < K_N; k++) {
        r->n[k] = __atomic_load_n(&cnt[k], __ATOMIC_RELAXED);
        r->t[k] = __atomic_load_n(&tim[k], __ATOMIC_RELAXED);
    }
    __atomic_store_n(&wpos, w + 1, __ATOMIC_RELEASE);
    if (q - last_os >= freq) { last_os = q; objects_sample(q); }
}

/* ---- writer ------------------------------------------------------------------------------- */
static char buf[RN * 96 + 4096];
static frec prev;
static int have_prev;
static LONG seen_os;
static LONGLONG last_t, last_m;

void gp_mon_vm(LONG v[7])   /* committed, reserved, free, largest free (MB), regions, walk us, total MB */
{
    LONGLONG t0 = qpc();
    SYSTEM_INFO si; GetSystemInfo(&si);
    uintptr_t a = (uintptr_t)si.lpMinimumApplicationAddress, top = (uintptr_t)si.lpMaximumApplicationAddress;
    uint64_t c = 0, r = 0, f = 0, big = 0; LONG n = 0;
    MEMORY_BASIC_INFORMATION mi;
    while (a < top && VirtualQuery((void *)a, &mi, sizeof mi)) {
        uint64_t s = mi.RegionSize;
        if (mi.State == MEM_FREE) { f += s; if (s > big) big = s; }
        else if (mi.State == MEM_RESERVE) r += s; else c += s;
        n++;
        uintptr_t next = (uintptr_t)mi.BaseAddress + mi.RegionSize;
        if (next <= a) break;
        a = next;
    }
    v[0] = (LONG)(c >> 20); v[1] = (LONG)(r >> 20); v[2] = (LONG)(f >> 20); v[3] = (LONG)(big >> 20);
    v[4] = n; v[5] = (LONG)us(qpc() - t0); v[6] = (LONG)((top - (uintptr_t)si.lpMinimumApplicationAddress + 1) >> 20);
}

static int put(int n, const char *fmt, ...)
{
    va_list ap; va_start(ap, fmt);
    int k = vsnprintf(buf + n, sizeof buf - n, fmt, ap);
    va_end(ap);
    return k > 0 && n + k < (int)sizeof buf ? n + k : n;
}

void gp_mon_flush(int final)
{
    int n = 0;
    LONGLONG q = qpc();
    if (q - last_t >= freq || final) {
        FILETIME ft; GetSystemTimeAsFileTime(&ft);
        ULONGLONG unix_ms = ((ULONGLONG)ft.dwHighDateTime << 32 | ft.dwLowDateTime) / 10000 - 11644473600000ull;
        n = put(n, "t %lld %llu %lu\n", us(q - q0), unix_ms, GetTickCount());
        last_t = q;
    }
    LONG w = __atomic_load_n(&wpos, __ATOMIC_ACQUIRE), r = rpos;
    for (; r != w && n < (int)sizeof buf - 200; r++) {
        const frec *f = &ring[r & (RN - 1)];
        if (have_prev)
            n = put(n, "f %lld %lu %ld %lld %ld %lld %ld %lld\n", us(f->q - q0), (unsigned long)f->logic,
                    f->n[0] - prev.n[0], us(f->t[0] - prev.t[0]), f->n[1] - prev.n[1], us(f->t[1] - prev.t[1]),
                    f->n[2] - prev.n[2], us(f->t[2] - prev.t[2]));
        prev = *f; have_prev = 1;
    }
    __atomic_store_n(&rpos, r, __ATOMIC_RELEASE);
    LONG s = __atomic_load_n(&os_seq, __ATOMIC_ACQUIRE);
    if (s != seen_os) {
        seen_os = s;
        n = put(n, "s %lld %ld %ld %lu %ld\n", us(os_.q - q0), os_.objects, os_.mode, (unsigned long)os_.logic, os_.walk_us);
    }
    if (q - last_m >= vm_secs * freq || final) {
        LONG v[7]; gp_mon_vm(v);
        n = put(n, "m %lld %ld %ld %ld %ld %ld %ld %ld\n", us(q - q0), v[0], v[1], v[2], v[3], v[4], v[5], v[6]);
        last_m = q;
    }
    if (dropped) { n = put(n, "d %ld\n", dropped); dropped = 0; }
    if (n && out != INVALID_HANDLE_VALUE) { DWORD wr; WriteFile(out, buf, n, &wr, NULL); }
}

static void name_thread(HANDLE h, const WCHAR *name);
static DWORD WINAPI writer(void *arg)
{
    (void)arg;
    name_thread(GetCurrentThread(), L"gp_monitor");
    for (;;) { Sleep(250); gp_mon_flush(0); }
    return 0;
}

static void name_thread(HANDLE h, const WCHAR *name)
{
    typedef HRESULT (WINAPI *f_t)(HANDLE, const WCHAR *);
    HMODULE k = GetModuleHandleA("kernelbase.dll");
    f_t f = k ? (f_t)(void *)GetProcAddress(k, "SetThreadDescription") : NULL;
    if (!f && (k = GetModuleHandleA("kernel32.dll"))) f = (f_t)(void *)GetProcAddress(k, "SetThreadDescription");
    if (f) f(h, name);
}

void gp_mon_exit(void)
{
    if (!gp_mon_on) return;
    gp_mon_flush(1);
    LONG k[K_N]; for (int i = 0; i < K_N; i++) k[i] = cnt[i];
    gp_log("exit: monitor: D3DX texture loads %ld, texture creations %ld, effects %ld", k[0], k[1], k[2]);
    if (out != INVALID_HANDLE_VALUE) CloseHandle(out);
    out = INVALID_HANDLE_VALUE;
}

int gp_patch_monitor(void)
{
    char path[MAX_PATH], v[16];
    if (!GetEnvironmentVariableA("GAMEPATCH_MONITOR", path, sizeof path) || !path[0]) {
        gp_log("monitor: no output (GAMEPATCH_MONITOR is not set; scripts/play-rotwk.sh sets it)");
        return 0;
    }
    if (GetEnvironmentVariableA("GAMEPATCH_MONITOR_VM_SECS", v, sizeof v) && atoi(v) > 0) vm_secs = atoi(v);
    static const struct { uint32_t va, thunk; uint8_t idx; void *fn; } sites[] = {
        {0x530ef3, 0xa3ecea, 0, gp_mon_texload}, {0x53117e, 0xa3ecea, 0, gp_mon_texload},
        {0x530ec2, 0xa3ecf0, 1, gp_mon_surfload}, {0x531515, 0xa3ed0e, 2, gp_mon_cubeload},
        {0x53147c, 0xa3ed08, 3, gp_mon_volload}, {0x5200d6, 0xa3ece4, 4, gp_mon_create},
        {0x520112, 0xa3ece4, 4, gp_mon_create}, {0x530e8c, 0xa3ece4, 4, gp_mon_create},
        {0x531100, 0xa3ece4, 4, gp_mon_create}, {0x53132e, 0xa3ed02, 5, gp_mon_volcreate},
        {0x551356, 0xa3ed20, 6, gp_mon_fx}, {0x5513a3, 0xa3ed1a, 7, gp_mon_fxfile}};
    /* the thunks: jmp [IAT slot] of the expected import */
    static const struct { uint32_t va; uint8_t b[6]; } thunks[] = {
        {0xa3ecea, {0xff,0x25,0x18,0x0a,0xbd,0x00}}, {0xa3ecf0, {0xff,0x25,0x14,0x0a,0xbd,0x00}},
        {0xa3ed0e, {0xff,0x25,0x00,0x0a,0xbd,0x00}}, {0xa3ed08, {0xff,0x25,0x04,0x0a,0xbd,0x00}},
        {0xa3ece4, {0xff,0x25,0x28,0x0a,0xbd,0x00}}, {0xa3ed02, {0xff,0x25,0x08,0x0a,0xbd,0x00}},
        {0xa3ed20, {0xff,0x25,0xf4,0x09,0xbd,0x00}}, {0xa3ed1a, {0xff,0x25,0xf8,0x09,0xbd,0x00}}};
    enum { NS = sizeof sites / sizeof sites[0], NT = sizeof thunks / sizeof thunks[0] };
    static uint8_t orig[NS][5];
    gp_site s[NS + NT];
    int n = 0;
    for (int i = 0; i < NT; i++) { gp_site_init(&s[n], thunks[i].va, thunks[i].b, 6); s[n++].wlen = 0; }  /* check only */
    for (int i = 0; i < NS; i++) {
        int32_t rel = (int32_t)(sites[i].thunk - (sites[i].va + 5));
        orig[i][0] = 0xe8; memcpy(&orig[i][1], &rel, 4);
        gp_site_init(&s[n], sites[i].va, orig[i], 5);
        gp_rel32(&s[n++], 0, 0xe8, sites[i].fn);
        gp_mon_fn[sites[i].idx] = sites[i].thunk + gp_va_offset;
    }
    LARGE_INTEGER f; QueryPerformanceFrequency(&f);
    freq = f.QuadPart; q0 = qpc();
    if (!gp_apply("monitor", s, n)) return 0;
    out = CreateFileA(path, GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL, CREATE_ALWAYS,
                      FILE_ATTRIBUTE_NORMAL, NULL);
    if (out == INVALID_HANDLE_VALUE) gp_log("monitor: cannot create %s (%lu); counting only", path, GetLastError());
    else {
        char h[200]; DWORD wr;
        int k = snprintf(h, sizeof h, "# gamepatch monitor 1, pid %lu, qpc %lld Hz, vm every %d s\n",
                         GetCurrentProcessId(), freq, vm_secs);
        WriteFile(out, h, k, &wr, NULL);
    }
    gp_mon_on = 1;
    name_thread(GetCurrentThread(), L"bfme_main");
    if (gp_mon_start_writer) {
        HANDLE t = CreateThread(NULL, 0, writer, NULL, 0, NULL);
        if (t) CloseHandle(t);
    }
    gp_log("monitor: on, writing %s (needs renderstats for the frame records)", path);
    return 1;
}
