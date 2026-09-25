/* t_anim: animdedup against the game's own animation code. The exe's .text runs at its address +
 * offset (two copies: A original, B patched; their two jump tables relocated after the patch has
 * checked the bytes), .rdata/.data at their own addresses. A small world is built in a fixed arena:
 * HLod objects with the real HLod vtable (relocated copy), their HTrees and pivots, compressed
 * animations (fake HAnim vtable: frame count, rate, pivot count, class id) with real AdaptiveDelta
 * channels (4- and 8-bit, random deltas, a quarter of them shorter than their animation, so frames
 * past a channel's end occur), and sub-meshes on two LODs plus an additional model (fake mesh
 * vtable that stores what it is given). Every frame
 * advances WW3D::SyncTime (sometimes by 0) and does, per object and at random: move it
 * (Set_Transform 0x59ae20, or with the same matrix), switch animation / mode (Set_Animation
 * 0x5a4340 with every animation mode, or 0x5a4320), overwrite a sub-mesh's transform / fade /
 * hidden (other code writing there), write the object's translation, frame, speed or last sync
 * time directly (code that would bypass the valid flag; each such write must defeat the skip),
 * query a bone (Get_Bone_Transform 0x5a4e30, what
 * Visibility_Check's bounding sphere does), and Render (0x5a4dd0) one to three times (main,
 * shadow-map and reflection passes). World A runs the original code, world B the same script
 * after gp_patch_animdedup() rewrote the three call sites exactly as in the game; the arena
 * (objects, HTrees, pivots, decode streams, sub-meshes, bone query results) is hashed after every
 * frame and must be identical, and B must actually have skipped evaluations.
 * usage: t_anim.exe <path to lotrbfme2ep1.exe 2.02> [frames] */
#include "orig.h"
#include "gp.h"
#include "gp_render.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <xmmintrin.h>

#define TC __attribute__((thiscall))
static uint32_t OFF;
static uint32_t reloc(uint32_t v) { return v >= 0x401000 && v < 0xbd0000 ? v + OFF : v; }

static uint8_t *arena; static uint32_t used, dyn_start;
static void *alloc(uint32_t n) { void *p = arena + used; used += (n + 15) & ~15u; return p; }
static uint32_t rng;
static uint32_t rnd(void) { rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5; return rng; }
static float frand(float lo, float hi) { return lo + (hi - lo) * (float)(rnd() & 0xffffff) / 16777216.0f; }
#define U32(p, o) (*(uint32_t *)((uint8_t *)(p) + (o)))
#define F32(p, o) (*(float *)((uint8_t *)(p) + (o)))
#define SYNC (*(volatile uint32_t *)0xdd1e0c)

/* ---- fakes ---- */
static int TC an_frames(uint8_t *a) { return *(int *)(a + 8); }
static float TC an_fps(uint8_t *a) { return *(float *)(a + 0xc); }
static int TC an_pivots(uint8_t *a) { return *(int *)(a + 0x10); }
static int TC an_class(uint8_t *a) { (void)a; return 1; }
static void TC trap(void *a) { printf("unexpected virtual call on %p\n", a); exit(3); }
static void TC me_set_tf(uint8_t *m, const float *t) { memcpy(m + 0x18, t, 48); U32(m, 0x8c)++; }
static void TC me_hidden(uint8_t *m, int h) { U32(m, 0x94) = h & 0xff; U32(m, 0x8c)++; }
static void TC me_fade(uint8_t *m, int i, float f) { F32(m, 0x90) = f; U32(m, 0x98) = i; U32(m, 0x8c)++; }
static void TC me_usot(uint8_t *m) { U32(m, 0x8c)++; }

typedef void (TC *render_t)(void *, void *);
typedef void (TC *settf_t)(void *, const float *);
typedef void (TC *setanim_t)(void *, void *, float, int);
typedef void (TC *setbase_t)(void *);
typedef void *(TC *getbone_t)(void *, float *, int);

/* ---- the world ---- */
#define NOBJ 8
#define MAXP 24
typedef struct { int npiv; int parent[MAXP]; uint8_t *anims[4]; int nanims; } skel_t;
static uint8_t *hlod_vt, *mesh_vt, *anim_vt, *chan_vt[2];
static uint8_t *obj[NOBJ], *outm[NOBJ];
static skel_t sk[2];
static int obj_sk[NOBJ];

static uint8_t *make_channel(int ncomp, int frames, int bits8)
{
    if (frames > 20 && rnd() % 4 == 0) frames -= 1 + rnd() % 19;   /* shorter than the animation */
    uint8_t *c = alloc(0x30);
    U32(c, 0) = (uint32_t)(uintptr_t)chan_vt[bits8]; U32(c, 4) = 1;
    U32(c, 0xc) = frames; U32(c, 0x10) = ncomp; F32(c, 0x14) = frand(0.05f, 2.0f);
    for (int i = 0; i < ncomp; i++) F32(c, 0x18 + 4 * i) = ncomp == 4 ? frand(-1, 1) : frand(-3, 3);
    int per = bits8 ? 17 : 9, blocks = (frames + 15) / 16 + 1;
    uint8_t *d = alloc(blocks * per * ncomp + 64);
    for (int i = 0; i < blocks * per * ncomp + 64; i++) d[i] = (uint8_t)rnd();
    for (int b = 0; b < blocks * ncomp; b++) d[b * per] = (uint8_t)(3 + rnd() % 6);   /* scale index 1e-5..1 */
    U32(c, 0x28) = (uint32_t)(uintptr_t)d;
    return c;
}

static uint8_t *make_anim(skel_t *s, int frames)
{
    uint8_t *a = alloc(0x60);
    U32(a, 0) = (uint32_t)(uintptr_t)anim_vt; U32(a, 4) = 1000000;
    U32(a, 8) = frames; F32(a, 0xc) = frand(10, 40); U32(a, 0x10) = s->npiv;
    uint8_t *t = alloc(s->npiv * 0x18);
    for (int p = 1; p < s->npiv; p++) {
        int b8 = rnd() % 2;
        for (int k = 0; k < 3; k++) if (rnd() % 3) U32(t, p * 0x18 + 4 * k) = (uint32_t)(uintptr_t)make_channel(1, frames, b8);
        if (rnd() % 5) U32(t, p * 0x18 + 0xc) = (uint32_t)(uintptr_t)make_channel(4, frames, b8);
        if (rnd() % 4 == 0) U32(t, p * 0x18 + 0x10) = (uint32_t)(uintptr_t)make_channel(1, frames, b8);
    }
    U32(a, 0x58) = (uint32_t)(uintptr_t)t;
    return a;
}

static void random_matrix(float *m)
{
    float x = frand(-1, 1), y = frand(-1, 1), z = frand(-1, 1), w = frand(-1, 1);
    float l = x * x + y * y + z * z + w * w; l = l > 1e-6f ? 1.0f / __builtin_sqrtf(l) : 1; x *= l; y *= l; z *= l; w *= l;
    float r[9] = {1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y),
                  2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x),
                  2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)};
    for (int i = 0; i < 3; i++) { m[4 * i] = r[3 * i]; m[4 * i + 1] = r[3 * i + 1]; m[4 * i + 2] = r[3 * i + 2]; m[4 * i + 3] = frand(-500, 500); }
}

static uint8_t *make_mesh(void)
{
    uint8_t *m = alloc(0x100);
    U32(m, 0) = (uint32_t)(uintptr_t)mesh_vt; U32(m, 0x7c) = 1;   /* a sub-object: container set */
    return m;
}

static void build(uint32_t seed)
{
    memset(arena, 0, used); used = 0; rng = seed;
    hlod_vt = alloc(0x300);
    for (int i = 0; i < 0x300; i += 4) U32(hlod_vt, i) = reloc(*(uint32_t *)(uintptr_t)(0xbec7f0 + i));
    for (int b = 0; b < 2; b++) {
        chan_vt[b] = alloc(0x20);
        for (int i = 0; i < 0x1c; i += 4) U32(chan_vt[b], i) = reloc(*(uint32_t *)(uintptr_t)((b ? 0xbecd5c : 0xbecd40) + i));
    }
    anim_vt = alloc(0x100); mesh_vt = alloc(0x200);
    for (int i = 0; i < 0x100; i += 4) U32(anim_vt, i) = (uint32_t)(uintptr_t)trap;
    for (int i = 0; i < 0x200; i += 4) U32(mesh_vt, i) = (uint32_t)(uintptr_t)trap;
    U32(anim_vt, 0x14) = (uint32_t)(uintptr_t)an_frames; U32(anim_vt, 0x18) = (uint32_t)(uintptr_t)an_fps;
    U32(anim_vt, 0x34) = (uint32_t)(uintptr_t)an_pivots; U32(anim_vt, 0x54) = (uint32_t)(uintptr_t)an_class;
    U32(mesh_vt, 0x54) = (uint32_t)(uintptr_t)me_set_tf; U32(mesh_vt, 0x19c) = (uint32_t)(uintptr_t)me_hidden;
    U32(mesh_vt, 0x5c) = (uint32_t)(uintptr_t)me_fade; U32(mesh_vt, 0xa8) = (uint32_t)(uintptr_t)me_usot;
    for (int s = 0; s < 2; s++) {
        sk[s].npiv = s ? MAXP : 9;
        for (int p = 1; p < sk[s].npiv; p++) sk[s].parent[p] = rnd() % p;
        static const int fr[4] = {1, 30, 97, 300};
        sk[s].nanims = 4;
        for (int k = 0; k < 4; k++) sk[s].anims[k] = make_anim(&sk[s], fr[k]);
    }
    dyn_start = used;
    for (int o = 0; o < NOBJ; o++) {
        skel_t *s = &sk[obj_sk[o] = o % 2];
        uint8_t *h = obj[o] = alloc(0x160), *t = alloc(0x40), *pv = alloc(s->npiv * 0x58);
        outm[o] = alloc(48);
        U32(h, 0) = (uint32_t)(uintptr_t)hlod_vt; U32(h, 4) = 1; U32(h, 0x10) = 0x6000;   /* not hidden */
        random_matrix((float *)(h + 0x18));
        U32(h, 0xf8) = (uint32_t)(uintptr_t)t; U32(h, 0x100) = 1; F32(h, 0x118) = 1; F32(h, 0x11c) = 1;
        U32(t, 0x10) = s->npiv; U32(t, 0x14) = (uint32_t)(uintptr_t)pv; F32(t, 0x18) = frand(0.8f, 1.25f);
        U32(t, 0x2c) = (uint32_t)(uintptr_t)alloc(0x2000); U32(t, 0x30) = 0x2000;
        for (int p = 0; p < s->npiv; p++) {
            uint8_t *q = pv + p * 0x58;
            if (p) U32(q, 0x10) = (uint32_t)(uintptr_t)(pv + s->parent[p] * 0x58);
            float x = frand(-1, 1), y = frand(-1, 1), z = frand(-1, 1), w = frand(0.2f, 1);
            float l = 1.0f / __builtin_sqrtf(x * x + y * y + z * z + w * w);
            F32(q, 0x14) = x * l; F32(q, 0x18) = y * l; F32(q, 0x1c) = z * l; F32(q, 0x20) = w * l;
            for (int k = 0; k < 3; k++) F32(q, 0x24 + 4 * k) = frand(-10, 10);
            F32(q, 0x3c) = 1;                                   /* identity pose until evaluated */
        }
        /* two LODs with 2..4 meshes each, one additional model */
        uint8_t *lods = alloc(2 * 0x28);
        U32(h, 0x120) = 2; U32(h, 0x128) = (uint32_t)(uintptr_t)lods;
        for (int l = 0; l < 2; l++) {
            int n = 2 + rnd() % 3; uint8_t *ms = alloc(n * 0x14);
            U32(lods, l * 0x28 + 4) = (uint32_t)(uintptr_t)ms; U32(lods, l * 0x28 + 0x10) = n;
            for (int i = 0; i < n; i++) { U32(ms, i * 0x14) = (uint32_t)(uintptr_t)make_mesh(); U32(ms, i * 0x14 + 4) = rnd() % s->npiv; }
        }
        uint8_t *add = alloc(0x14);
        U32(add, 0) = (uint32_t)(uintptr_t)make_mesh(); U32(add, 4) = rnd() % s->npiv;
        U32(h, 0x13c) = (uint32_t)(uintptr_t)add; U32(h, 0x148) = 1;
    }
}

static uint64_t hash_dyn(void)
{
    uint64_t h = 0xcbf29ce484222325ull;
    for (uint32_t i = dyn_start; i < used; i += 4) { h ^= U32(arena, i); h *= 0x100000001b3ull; }
    return h;
}

/* one scripted run: returns the number of frames; hashes[f] after every frame */
static int run(uint32_t seed, int frames, uint64_t *hashes, uint8_t *final_copy)
{
    build(seed);
    render_t render = (render_t)(uintptr_t)reloc(0x5a4dd0);
    settf_t settf = (settf_t)(uintptr_t)reloc(0x59ae20);
    setanim_t setanim = (setanim_t)(uintptr_t)reloc(0x5a4340);
    setbase_t setbase = (setbase_t)(uintptr_t)reloc(0x5a4320);
    getbone_t getbone = (getbone_t)(uintptr_t)reloc(0x5a4e30);
    static const uint32_t steps[] = {0, 0, 16, 16, 33, 33, 33, 50, 100, 250, 1000, 5000};
    SYNC = 1000;
    for (int o = 0; o < NOBJ; o++) {
        skel_t *s = &sk[obj_sk[o]];
        setanim(obj[o], s->anims[1 + o % 3], frand(0, 20), 1 + o % 6);
    }
    for (int f = 0; f < frames; f++) {
        SYNC += steps[rnd() % 12];
        for (int o = 0; o < NOBJ; o++) {
            uint8_t *h = obj[o]; skel_t *s = &sk[obj_sk[o]];
            uint32_t ev = rnd() % 1000;
            if (ev < 350) {                                    /* moves (every third frame or so) */
                float m[12]; memcpy(m, h + 0x18, 48);
                m[3] += frand(-2, 2); m[11] += frand(-2, 2);
                if (ev < 60) random_matrix(m);
                settf(h, m);
            } else if (ev < 420) {
                float m[12]; memcpy(m, h + 0x18, 48); settf(h, m);   /* same matrix: no change */
            } else if (ev < 435) {
                setanim(h, s->anims[rnd() % s->nanims], frand(-5, 400), rnd() % 7);
            } else if (ev < 438) {
                setbase(h);
            } else if (ev < 450) {
                uint8_t *ms = (uint8_t *)(uintptr_t)U32(U32(h, 0x128), 4);
                uint8_t *m = (uint8_t *)(uintptr_t)U32(ms, 0);
                F32(m, 0x90) = frand(0, 1); U32(m, 0x94) ^= 1; F32(m, 0x20) = frand(-9, 9);
            } else if (ev < 452) {
                U32(h, 0x10) ^= 0x200000;                       /* sub-objects dirty */
            } else if (ev < 456) {                              /* writes that bypass the valid flag: */
                F32(h, 0x24) += 1.0f;                           /* translation */
            } else if (ev < 460) {
                F32(h, 0x108) = frand(0, 3);                    /* frame */
            } else if (ev < 470) {
                F32(h, 0x11c) = rnd() % 2 ? 0.0f : 1.0f;        /* speed (0: the frame stands still) */
            } else if (ev < 474) {
                U32(h, 0x114) -= rnd() % 40;                    /* last sync time */
            }
        }
        for (int o = 0; o < NOBJ; o++)                          /* visibility: the bounding sphere */
            if (rnd() % 10 < 7) getbone(obj[o], (float *)outm[o], rnd() % sk[obj_sk[o]].npiv);
        int passes = 1 + (rnd() % 4 == 0) + (rnd() % 8 == 0);
        for (int p = 0; p < passes; p++)
            for (int o = 0; o < NOBJ; o++) if (rnd() % 10 < 8 || p == 0) render(obj[o], NULL);
        hashes[f] = hash_dyn();
    }
    if (final_copy) memcpy(final_copy, arena, used);
    return frames;
}

/* a private copy of .text at its address + offset (and the .rdata page with the HLod vtable,
 * which the patch checks) */
static uint32_t map_code(void)
{
    uint32_t off = orig_reserve_image();
    if (!off || orig_map_at(0x401000, 0x7cf000, off) || orig_map_at(0xbec000, 0x1000, off)) return 0;
    return off;
}
/* the two jump tables the executed code uses (jmp *table(,%eax,4)): the jmp's absolute table
 * address and the table's entries move with the code; done after the patch checked the bytes */
static void fix_tables(uint32_t off)
{
    static const uint32_t jt[][3] = {{0x5a4813, 0x5a4a54, 6}, {0x5a50ea, 0x5a5198, 4}};
    for (int t = 0; t < 2; t++) {
        *(uint32_t *)(uintptr_t)(jt[t][0] + off + 3) += off;
        for (uint32_t i = 0; i < jt[t][2]; i++) *(uint32_t *)(uintptr_t)(jt[t][1] + off + 4 * i) += off;
    }
}

/* a crash in the game code: say where (eip, the fault, return addresses on the stack as exe VAs) */
static LONG WINAPI on_fault(EXCEPTION_POINTERS *x)
{
    CONTEXT *c = x->ContextRecord;
    printf("CRASH %08lx at eip %08lx (exe %08lx), address %08lx; stack:", x->ExceptionRecord->ExceptionCode,
           (unsigned long)c->Eip, (unsigned long)(c->Eip - OFF), (unsigned long)x->ExceptionRecord->ExceptionInformation[1]);
    uint32_t *sp = (uint32_t *)(uintptr_t)c->Esp;
    for (int i = 0, n = 0; i < 400 && n < 12; i++)
        if (sp[i] >= 0x401000 + OFF && sp[i] < 0xbd0000 + OFF) { printf(" %08lx", (unsigned long)(sp[i] - OFF)); n++; }
    printf("\nFAIL\n");
    ExitProcess(3);
}

int main(int argc, char **argv)
{
    SetUnhandledExceptionFilter(on_fault);
    setvbuf(stdout, NULL, _IONBF, 0);
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    int frames = argc > 2 ? atoi(argv[2]) : 3000;
    if (orig_map_at(0xbd0000, 0x1b9000, 0) || orig_map_at(0xd89000, 0x81000, 0)) return 2;
    uint32_t off_a = map_code(), off_b = map_code();          /* A: original, B: to be patched */
    if (!off_a || !off_b) return 2;
    fix_tables(off_a);
    OFF = off_a;
    arena = VirtualAlloc(NULL, 16 << 20, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    unsigned short cw = 0x007f;
    __asm__ volatile("fninit\n fldcw %0" : : "m"(cw));
    _mm_setcsr(0x1f80);
    printf("code at +%08x, arena %p\n", OFF, arena);

    static const uint32_t seeds[] = {1, 2, 3, 77, 1234};
    enum { NS = sizeof seeds / sizeof seeds[0] };
    uint64_t *ha = malloc(sizeof(uint64_t) * frames * NS), *hb = malloc(sizeof(uint64_t) * frames * NS);
    uint8_t *fa = malloc(16 << 20), *fb = malloc(16 << 20);
    uint64_t t0 = now_us();
    for (int s = 0; s < NS; s++) run(seeds[s], frames, ha + s * frames, s == NS - 1 ? fa : NULL);
    uint64_t ta = now_us() - t0;
    printf("[1] world A (original code): %d scripts x %d frames, %.1f s\n", NS, frames, ta / 1e6);

    OFF = off_b;
    gp_va_offset = OFF;
    int ok = gp_patch_animdedup();                            /* checks the pristine bytes */
    gp_va_offset = 0;
    fix_tables(off_b);
    printf("[2] animdedup applied to the original bytes: %s\n", ok ? "yes" : "NO");
    if (!ok) { printf("FAIL\n"); return 1; }
    gp_ad_vt_hlod = (uint32_t)(uintptr_t)arena;               /* build() puts the HLod vtable first */
    int bad = 0;
    uint64_t tb = 0;
    for (int s = 0; s < NS; s++) {
        LONG st0 = gp_ad_stats[0], st1 = gp_ad_stats[1];
        t0 = now_us();
        run(seeds[s], frames, hb + s * frames, s == NS - 1 ? fb : NULL);
        tb += now_us() - t0;
        int first = -1;
        for (int f = 0; f < frames; f++) if (ha[s * frames + f] != hb[s * frames + f]) { first = f; break; }
        printf("[3] script %lu: %s; %ld Render progress calls, %ld evaluations skipped\n", (unsigned long)seeds[s],
               first < 0 ? "identical after every frame" : "DIFFERS", gp_ad_stats[0] - st0, gp_ad_stats[1] - st1);
        if (first >= 0) { printf("    first different frame %d\n", first); bad++; }
    }
    if (memcmp(fa + dyn_start, fb + dyn_start, used - dyn_start)) {   /* before it: vtables with code addresses */
        for (uint32_t i = dyn_start; i < used; i += 4)
            if (U32(fa, i) != U32(fb, i)) { printf("    final arena differs first at +%x\n", i); break; }
        bad++;
    }
    printf("[4] totals: %ld progress calls, %ld skipped, %ld snapshots, %ld with the frame still moving; "
           "world B took %.1f s (A %.1f s)\n", gp_ad_stats[0], gp_ad_stats[1], gp_ad_stats[2], gp_ad_stats[3],
           tb / 1e6, ta / 1e6);
    if (!gp_ad_stats[1]) { printf("    nothing was skipped: the test did not exercise the patch\n"); bad++; }
    printf("%s\n", bad ? "FAIL" : "PASS");
    return bad != 0;
}
