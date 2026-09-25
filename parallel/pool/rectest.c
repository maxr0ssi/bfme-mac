/* R5 recorder test: a job calls three "shared side effect" functions (cdecl, stdcall with a
 * pointer to a stack buffer, thiscall). Reference: the job run serially with direct calls.
 * Test: the job run with par_for, calls retargeted to recorder stubs, replayed on main.
 * The shared effect log (order + values) must be identical byte-for-byte. */
#include "parallel.h"
#include "recorder.h"
#include <windows.h>
#include <stdio.h>
#include <string.h>

static uint32_t effect[1 << 20]; static int neff;
static void effect_put(uint32_t a, uint32_t b) { effect[neff++] = a; effect[neff++] = b; }

static void __attribute__((cdecl)) list_push(uint32_t list, uint32_t v) { effect_put(list, v); }
static uint32_t __attribute__((stdcall)) add_vec(const float *v3, uint32_t tag)
{ uint32_t x; memcpy(&x, &v3[1], 4); effect_put(tag, x); return 0; }
typedef struct { uint32_t id; } obj_t;
static uint32_t __attribute__((thiscall)) obj_add(obj_t *o, uint32_t v) { effect_put(o->id, v); return 1; }

/* how the clone reaches its callees: direct in the reference, stubs in the parallel run */
static void (__attribute__((cdecl)) *p_push)(uint32_t, uint32_t);
static uint32_t (__attribute__((stdcall)) *p_vec)(const float *, uint32_t);
static uint32_t (__attribute__((thiscall)) *p_obj)(obj_t *, uint32_t);
static obj_t objs[4] = { {100}, {101}, {102}, {103} };
static int use_rec;

static void job(int b, int e, void *ctx, int w)
{
    (void)ctx; (void)w;
    for (int i = b; i < e; i++) {
        if (use_rec) rec_begin_item(i);
        float v[3] = { i * 0.5f, i * 0.25f + 1.0f, 3.0f };     /* worker-local (stack) */
        uint32_t k = (uint32_t)i * 2654435761u;
        if (k & 1) p_push(i & 7, k >> 8);
        p_vec(v, (uint32_t)i);
        if ((k >> 3) % 3 == 0) p_obj(&objs[i & 3], (uint32_t)i);
        p_push(9, (uint32_t)i);
    }
}

int main(void)
{
    setbuf(stdout, NULL);
    int N = 20000;
    /* reference: serial, direct calls */
    p_push = list_push; p_vec = add_vec; p_obj = obj_add; use_rec = 0; neff = 0;
    job(0, N, NULL, 0);
    static uint32_t ref[1 << 20]; int nref = neff; memcpy(ref, effect, nref * 4);

    /* recorded: stubs, parallel, replay */
    par_init(7);
    int s_push = rec_site_add((uint32_t)(uintptr_t)list_push, REC_CDECL, 2, 0, -1, 0);
    int s_vec  = rec_site_add((uint32_t)(uintptr_t)add_vec, REC_STDCALL, 2, 0, 0, 12);
    int s_obj  = rec_site_add((uint32_t)(uintptr_t)obj_add, REC_THISCALL, 1, 1, -1, 0);
    p_push = rec_site_stub(s_push); p_vec = rec_site_stub(s_vec); p_obj = rec_site_stub(s_obj);
    use_rec = 1;
    for (int round = 0; round < 3; round++) {
        neff = 0; rec_reset();
        LARGE_INTEGER f, t0, t1, t2; QueryPerformanceFrequency(&f); QueryPerformanceCounter(&t0);
        par_for(N, 512, job, NULL);
        QueryPerformanceCounter(&t1);
        uint64_t dp = rec_digest();
        int nrec = rec_replay();
        QueryPerformanceCounter(&t2);
        int same = neff == nref && !memcmp(effect, ref, nref * 4);
        /* the same job serially with the stubs gives the same record stream */
        rec_reset(); job(0, N, NULL, 0); uint64_t ds = rec_digest();
        printf("rectest round %d: %d records, overflow %d, replayed effects %s reference; "
               "record digest serial %s parallel; record %.0f us, replay %.0f us (%.3f us/record)\n",
               round, nrec, rec_overflowed(), same ? "==" : "!= (MISMATCH)", ds == dp ? "==" : "!=",
               (t1.QuadPart - t0.QuadPart) * 1e6 / f.QuadPart, (t2.QuadPart - t1.QuadPart) * 1e6 / f.QuadPart,
               (t2.QuadPart - t1.QuadPart) * 1e6 / f.QuadPart / nrec);
    }
    par_shutdown();
    return 0;
}
