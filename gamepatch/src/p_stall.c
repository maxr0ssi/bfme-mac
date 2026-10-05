/* stall sampler (part of monitor; [patches] stalls=0 or GAMEPATCH_STALLS=0 turns it off): names the code
 * a long frame spends its time in, for scripts/monitor.sh. No game code is patched and nothing runs on
 * the game's threads.
 *
 * A watchdog thread checks every 10 ms how long ago the main thread finished its last frame (the
 * monitor's frame hook stores the time in gp_stall_last_q). Past stall_ms (default 150) it samples the
 * main thread every every_ms (2) until the frame ends, at most max_ms (4000) per stall: SuspendThread,
 * GetThreadContext (EIP, ESP), a copy of the top 32 KB of its stack, ResumeThread; the thread is held
 * for the context call and the copy only (the exit log and the report give the mean). Between the
 * suspend and the resume the watchdog calls nothing that takes a lock, so the main thread cannot be
 * holding one it waits for. After the resume it keeps the stack's return addresses into the exe's
 * code, innermost first: the dwords that point just after a CALL (E8 into the exe or into this DLL, or
 * FF /2), as tools/eipsample.c does; tools/callstacks.py drops the stale ones when it chains them.
 *
 * Lines (gp_stall_drain, us since the caller's q0, addresses hex):
 *   X image_base code_lo code_hi exe_name                     once
 *   M base size module_name                                   the first time a sample's EIP is in it
 *   e us since_us logic eip held_us phase ret1 ret2 ...       one per sample; since = the last frame's
 *                                                             time, the same for every sample of a stall
 * Tested by gamepatch/tests/t_stall.c and end to end by scripts/monitor.sh stalltest (d3d9bench). */
#include "p_stall.h"
#include <stdio.h>
#include <string.h>

#define RING 2048
#define NRET 48
#define STACK_MAX (32 * 1024)

typedef struct {
    LONGLONG q, since;
    uint32_t logic, eip, ret[NRET];
    uint16_t held_us;
    int8_t phase;
    uint8_t nret;
} srec;

volatile LONGLONG gp_stall_last_q;
volatile uint32_t gp_stall_last_logic;
int (*gp_stall_phase)(void);

static srec ring[RING];
static volatile LONG wpos, rpos, lost, n_stalls, n_samples;
static LONGLONG held_sum, held_max;
static HANDLE main_th;
static uintptr_t stack_top, img_lo, img_hi, code_lo, code_hi, self_lo, self_hi;
static LONGLONG s_q0, s_freq, s_stall, s_every_ms, s_max;
static uint32_t stk[STACK_MAX / 4];
static char exe_name[MAX_PATH];
static int header_done;
static struct { uintptr_t base; } mods[48];
static int nmods;
typedef DWORD (WINAPI *mapped_t)(HANDLE, void *, char *, DWORD);
static mapped_t mapped_name;

static LONGLONG qpc(void) { LARGE_INTEGER x; QueryPerformanceCounter(&x); return x.QuadPart; }
static LONGLONG us(LONGLONG dq) { return dq * 1000000 / s_freq; }

static int in_code(uintptr_t a) { return (a >= code_lo && a < code_hi) || (a >= self_lo && a < self_hi); }

/* does a (inside the exe's code) follow a CALL? (tools/eipsample.c is_ret) */
static int is_ret(uint32_t a)
{
    if (a < code_lo + 7 || a >= code_hi) return 0;
    const uint8_t *p = (const uint8_t *)(uintptr_t)a;
    if (p[-5] == 0xE8 && in_code((uint32_t)(a + *(const int32_t *)(p - 4)))) return 1;
    uint8_t m;
    m = p[-1]; if (p[-2] == 0xFF && (m & 0x38) == 0x10 && ((m >> 6) == 3 || ((m >> 6) == 0 && (m & 7) != 4 && (m & 7) != 5))) return 1;
    m = p[-2]; if (p[-3] == 0xFF && (m & 0x38) == 0x10 && (((m >> 6) == 1 && (m & 7) != 4) || ((m >> 6) == 0 && (m & 7) == 4 && (p[-1] & 7) != 5))) return 1;
    m = p[-3]; if (p[-4] == 0xFF && (m & 0x38) == 0x10 && (m >> 6) == 1 && (m & 7) == 4) return 1;
    m = p[-5]; if (p[-6] == 0xFF && (m & 0x38) == 0x10 && (((m >> 6) == 2 && (m & 7) != 4) || ((m >> 6) == 0 && (m & 7) == 5))) return 1;
    m = p[-6]; if (p[-7] == 0xFF && (m & 0x38) == 0x10 && (((m >> 6) == 2 && (m & 7) == 4) || ((m >> 6) == 0 && (m & 7) == 4 && (p[-5] & 7) == 5))) return 1;
    return 0;
}

static void sample(LONGLONG since)
{
    LONG w = wpos;
    if (w - __atomic_load_n(&rpos, __ATOMIC_ACQUIRE) >= RING) { lost++; return; }
    srec *r = &ring[w & (RING - 1)];
    CONTEXT c;
    memset(&c, 0, sizeof c);
    c.ContextFlags = CONTEXT_CONTROL;
    uint32_t n = 0;
    LONGLONG t0 = qpc();
    if (SuspendThread(main_th) == (DWORD)-1) return;
    BOOL ok = GetThreadContext(main_th, &c);
    if (ok && c.Esp < stack_top && stack_top - c.Esp <= (1u << 24)) {
        n = (uint32_t)(stack_top - c.Esp);
        if (n > STACK_MAX) n = STACK_MAX;
        memcpy(stk, (const void *)(uintptr_t)c.Esp, n);   /* from ESP up is committed */
    }
    ResumeThread(main_th);
    LONGLONG held = us(qpc() - t0);
    if (!ok) return;
    r->q = t0; r->since = since; r->logic = gp_stall_last_logic; r->eip = c.Eip;
    r->held_us = held > 65535 ? 65535 : (uint16_t)held;
    r->phase = gp_stall_phase ? (int8_t)gp_stall_phase() : -1;
    r->nret = 0;
    for (uint32_t i = 0; i < n / 4 && r->nret < NRET; i++)
        if (is_ret(stk[i])) r->ret[r->nret++] = stk[i];
    held_sum += held; if (held > held_max) held_max = held;
    n_samples++;
    __atomic_store_n(&wpos, w + 1, __ATOMIC_RELEASE);
}

static DWORD WINAPI stall_watchdog(void *arg)
{
    (void)arg;
    LONGLONG since = 0, taken = 0;
    for (;;) {
        LONGLONG last = __atomic_load_n(&gp_stall_last_q, __ATOMIC_RELAXED), now = qpc();
        if (!last || now - last < s_stall) { Sleep(10); continue; }
        if (last != since) { since = last; taken = 0; n_stalls++; }
        if (taken < s_max) { sample(last); taken++; Sleep((DWORD)s_every_ms); }
        else Sleep(10);
    }
    return 0;
}

static void image_range(uintptr_t base, uintptr_t *lo, uintptr_t *hi, uintptr_t *clo, uintptr_t *chi)
{
    const IMAGE_DOS_HEADER *d = (const IMAGE_DOS_HEADER *)base;
    const IMAGE_NT_HEADERS *nt = (const IMAGE_NT_HEADERS *)(base + d->e_lfanew);
    *lo = base; *hi = base + nt->OptionalHeader.SizeOfImage;
    if (!clo) return;
    const IMAGE_SECTION_HEADER *s = IMAGE_FIRST_SECTION(nt);
    for (int i = 0; i < nt->FileHeader.NumberOfSections; i++, s++)
        if (s->Characteristics & IMAGE_SCN_MEM_EXECUTE) {
            *clo = base + s->VirtualAddress; *chi = *clo + s->Misc.VirtualSize;
            return;
        }
}

int gp_stall_start(LONGLONG q0, LONGLONG freq, int stall_ms, int every_ms, int max_ms)
{
    s_q0 = q0; s_freq = freq;
    s_stall = freq * (stall_ms > 0 ? stall_ms : 150) / 1000;
    s_every_ms = every_ms > 0 ? every_ms : 2;
    s_max = (max_ms > 0 ? max_ms : 4000) / s_every_ms;
    if (!DuplicateHandle(GetCurrentProcess(), GetCurrentThread(), GetCurrentProcess(), &main_th,
                         THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT | THREAD_QUERY_INFORMATION, FALSE, 0))
        return 0;
    stack_top = (uintptr_t)((NT_TIB *)NtCurrentTeb())->StackBase;
    image_range((uintptr_t)GetModuleHandleA(NULL), &img_lo, &img_hi, &code_lo, &code_hi);
    MEMORY_BASIC_INFORMATION mi;
    if (VirtualQuery((void *)gp_stall_start, &mi, sizeof mi))
        image_range((uintptr_t)mi.AllocationBase, &self_lo, &self_hi, NULL, NULL);
    char path[MAX_PATH];
    DWORD k = GetModuleFileNameA(NULL, path, sizeof path);
    const char *b = path + k;
    while (b > path && b[-1] != '\\' && b[-1] != '/') b--;
    snprintf(exe_name, sizeof exe_name, "%s", k ? b : "?");
    HMODULE k32 = GetModuleHandleA("kernel32.dll");
    mapped_name = k32 ? (mapped_t)(void *)GetProcAddress(k32, "K32GetMappedFileNameA") : NULL;
    HANDLE t = CreateThread(NULL, 0, stall_watchdog, NULL, 0, NULL);
    if (!t) return 0;
    SetThreadPriority(t, THREAD_PRIORITY_ABOVE_NORMAL);
    CloseHandle(t);
    return 1;
}

/* the module holding a, as an M line the first time (no loader lock: VirtualQuery and the mapping) */
static int module_line(uint32_t a, char *buf, int cap)
{
    if (a >= img_lo && a < img_hi) return 0;
    MEMORY_BASIC_INFORMATION mi;
    if (!VirtualQuery((void *)(uintptr_t)a, &mi, sizeof mi) || mi.Type != MEM_IMAGE) return 0;
    uintptr_t base = (uintptr_t)mi.AllocationBase;
    for (int i = 0; i < nmods; i++) if (mods[i].base == base) return 0;
    if (nmods == (int)(sizeof mods / sizeof mods[0])) return 0;
    const IMAGE_DOS_HEADER *d = (const IMAGE_DOS_HEADER *)base;
    if (d->e_magic != IMAGE_DOS_SIGNATURE) return 0;
    uintptr_t lo, hi;
    image_range(base, &lo, &hi, NULL, NULL);
    char path[MAX_PATH] = "?";
    if (!mapped_name || !mapped_name(GetCurrentProcess(), (void *)base, path, sizeof path)) strcpy(path, "?");
    const char *b = path + strlen(path);
    while (b > path && b[-1] != '\\' && b[-1] != '/') b--;
    int k = snprintf(buf, cap, "M %08lx %08lx %s\n", (unsigned long)lo, (unsigned long)(hi - lo), b);
    if (k <= 0 || k >= cap) return 0;
    mods[nmods++].base = base;
    return k;
}

int gp_stall_drain(char *buf, int cap)
{
    int n = 0;
    if (cap < 800) return 0;
    if (!header_done && main_th) {
        int k = snprintf(buf, cap, "X %08lx %08lx %08lx %s\n", (unsigned long)img_lo, (unsigned long)code_lo,
                         (unsigned long)code_hi, exe_name);
        if (k <= 0 || k >= cap) return 0;
        n = k; header_done = 1;
    }
    LONG w = __atomic_load_n(&wpos, __ATOMIC_ACQUIRE), r = rpos;
    for (; r != w && cap - n > 700; r++) {
        const srec *s = &ring[r & (RING - 1)];
        n += module_line(s->eip, buf + n, cap - n);
        n += snprintf(buf + n, cap - n, "e %lld %lld %lu %08lx %u %d", us(s->q - s_q0), us(s->since - s_q0),
                      (unsigned long)s->logic, (unsigned long)s->eip, (unsigned)s->held_us, (int)s->phase);
        for (int i = 0; i < s->nret; i++) n += snprintf(buf + n, cap - n, " %lx", (unsigned long)s->ret[i]);
        buf[n++] = '\n';
    }
    __atomic_store_n(&rpos, r, __ATOMIC_RELEASE);
    return n;
}

void gp_stall_stats(LONG *stalls, LONG *samples, LONG *lost_, LONG *held_mean_us, LONG *held_max_us)
{
    *stalls = n_stalls; *samples = n_samples; *lost_ = lost;
    *held_mean_us = n_samples ? (LONG)(held_sum / n_samples) : 0;
    *held_max_us = (LONG)held_max;
}
