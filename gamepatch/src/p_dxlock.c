/* dxlock: the game's DirectX lock without the Win32 mutex.
 *
 * The lock (DX8Wrapper, created in its Init at 0x525062/0x52506b) is a recursive Win32 mutex
 * (handle at 0xdd1fd8) plus a critical section (0xdd1f80) that only guards the owner/count pair
 * (0xdd34c8/0xdd34cc):
 *   acquire  0x51eec0: WaitForSingleObject(mutex, 20000); on timeout log (debug builds) and carry
 *                      on unlocked; Enter(cs); owner = tid; count++; Leave(cs)
 *   try      0x51ef50: WaitForSingleObject(mutex, ms) == WAIT_TIMEOUT -> return 0; else as above
 *   release  0x5208d0: Enter(cs); if (--count == 0) owner = 0; Leave(cs); ReleaseMutex(mutex)
 *   inline release at the end of Init (0x525291), same sequence.
 * The mutex exists for the movie player's decode thread (thread proc 0x65ce28), which takes the
 * lock with a 1 ms try (0x65cd0c) to upload frames while the main thread renders.
 *
 * Under Wine each WaitForSingleObject/ReleaseMutex is a wineserver round trip (NtWaitFor... and
 * NtReleaseMutant were ~34 % of the main thread in a big battle). This patch replaces exactly
 * those four calls with a process-local recursive lock (our own CRITICAL_SECTION, separate from
 * the game's, so the game's owner/count bookkeeping runs unchanged):
 *   wait(h, ms)  -> WAIT_OBJECT_0 once our CS is entered, WAIT_TIMEOUT after ms (polled), and the
 *                   real WaitForSingleObject when h is NULL (before Init, as the original fails)
 *   release(h)   -> TRUE after leaving our CS if this thread holds it; FALSE (ERROR_NOT_OWNER),
 *                   like ReleaseMutex, if it does not (e.g. after a 20 s timeout)
 * Mutual exclusion and recursion are the CRITICAL_SECTION's; see gamepatch/tests/t_dxlock.c. */
#include "gp.h"

static CRITICAL_SECTION dxcs;
static LONG dxcs_ready;
static LARGE_INTEGER qpf;

void gp_dx_init(void)
{
    if (InterlockedCompareExchange(&dxcs_ready, 1, 0) == 0) {
        InitializeCriticalSection(&dxcs);
        QueryPerformanceFrequency(&qpf);
    }
}

static DWORD slow_wait(DWORD ms)
{
    LARGE_INTEGER t0, t;
    QueryPerformanceCounter(&t0);
    LONGLONG limit = (LONGLONG)ms * qpf.QuadPart / 1000;
    for (unsigned n = 1;; n++) {
        if (TryEnterCriticalSection(&dxcs)) return WAIT_OBJECT_0;
        QueryPerformanceCounter(&t);
        LONGLONG el = t.QuadPart - t0.QuadPart;
        if (el >= limit) return WAIT_TIMEOUT;
        if (n < 64) YieldProcessor();                     /* ~microseconds: holder is mid-call */
        else if (el * 1000 < qpf.QuadPart * 2) Sleep(0);  /* first 2 ms: yield */
        else Sleep(1);
    }
}

DWORD WINAPI gp_dx_wait(HANDLE h, DWORD ms)
{
    if (!h) return WaitForSingleObject(h, ms);   /* not created yet: original fails the same way */
    if (TryEnterCriticalSection(&dxcs)) return WAIT_OBJECT_0;
    if (ms == 0) return WAIT_TIMEOUT;
    if (ms == INFINITE) { EnterCriticalSection(&dxcs); return WAIT_OBJECT_0; }
    return slow_wait(ms);
}

BOOL WINAPI gp_dx_release(HANDLE h)
{
    if (!h) return ReleaseMutex(h);
    if (dxcs.OwningThread == (HANDLE)(ULONG_PTR)GetCurrentThreadId() && dxcs.RecursionCount > 0) {
        LeaveCriticalSection(&dxcs);
        return TRUE;
    }
    SetLastError(ERROR_NOT_OWNER);
    return FALSE;
}

/* call dword ptr [WaitForSingleObject] / [ReleaseMutex] in the IAT */
static const uint8_t acq[]  = {0xa1,0xd8,0x1f,0xdd,0x00, 0x68,0x20,0x4e,0x00,0x00, 0x50, 0xff,0x15,0x34,0x02,0xbd,0x00};
static const uint8_t try_[] = {0x8b,0x44,0x24,0x04, 0x8b,0x0d,0xd8,0x1f,0xdd,0x00, 0x50, 0x51, 0xff,0x15,0x34,0x02,0xbd,0x00};
static const uint8_t rel[]  = {0x8b,0x15,0xd8,0x1f,0xdd,0x00, 0x52, 0xff,0x15,0x24,0x02,0xbd,0x00};
static const uint8_t rel2[] = {0xa1,0xd8,0x1f,0xdd,0x00, 0x50, 0xff,0x15,0x24,0x02,0xbd,0x00};
/* context: CreateMutexA result stored to 0xdd1fd8 right after InitializeCriticalSection(0xdd1f80) */
static const uint8_t init[] = {0x68,0x80,0x1f,0xdd,0x00, 0xa3,0xb0,0x34,0xdd,0x00, 0xff,0x15,0x5c,0x01,0xbd,0x00,
                               0x53, 0x53, 0x53, 0xff,0x15,0x1c,0x02,0xbd,0x00, 0xa3,0xd8,0x1f,0xdd,0x00};

int gp_patch_dxlock(void)
{
    gp_site s[5];
    gp_dx_init();
    gp_site_init(&s[0], 0x51eec0, acq, sizeof acq);
    gp_rel32(&s[0], 11, 0xe8, (void *)gp_dx_wait);  s[0].repl[16] = 0x90;
    gp_site_init(&s[1], 0x51ef50, try_, sizeof try_);
    gp_rel32(&s[1], 12, 0xe8, (void *)gp_dx_wait);  s[1].repl[17] = 0x90;
    gp_site_init(&s[2], 0x520919, rel, sizeof rel);
    gp_rel32(&s[2], 7, 0xe8, (void *)gp_dx_release); s[2].repl[12] = 0x90;
    gp_site_init(&s[3], 0x52528b, rel2, sizeof rel2);
    gp_rel32(&s[3], 6, 0xe8, (void *)gp_dx_release); s[3].repl[11] = 0x90;
    gp_site_init(&s[4], 0x525058, init, sizeof init); s[4].wlen = 0;
    return gp_apply("dxlock", s, 5);
}
