/* t_shadow: shadowpar (shadow volumes on the worker pool) and edgemap (O(n) edge chaining) against
 * the game's original code, read from the exe on disk and run at its address + OFF.
 *  [0] both patches accept the original bytes
 *  [1] edgemap: constructVolume, original vs patched, on silhouettes from the game's
 *      buildSilhouette over real and synthetic meshes and on random edge sets (loops, chains,
 *      shared vertices, duplicates): volume vertices, volume indices and the permuted silhouette
 *      compared byte for byte; time per call
 *  [2] worlds: casters over shared geometries (skinned and rigid; dynamic and static volumes) run
 *      for many frames through the game's updateMeshVolume and a caster loop (the original loop
 *      bytes, or the patched one): every frame's full state (silhouettes, volumes, neighbor
 *      arrays, both scratch vectors) and the ordered record of every draw / static-volume build
 *      must equal the unpatched run; also in verify mode, and with deliberately corrupted worker
 *      results (verify must catch them, restore the reference and switch itself off)
 *  [3] A1: buildPolygonNormals with its triangle loop on the pool vs the original
 *  [4] the per-frame entry: worlds run through W3DShadowManager::renderShadows 0x499d6d (as Flush
 *      calls it) -> 0x4f43a6 with its own early-outs -> the caster loop (only its D3D render-state
 *      block and the camera/terrain calls before it are skipped), shadowstats installed: identical
 *      to [2]'s reference with and without edgemap + shadowpar; the loop (and shadowpar) runs once
 *      per frame; with volume shadows off, no device or no casters it never runs, and shadowstats
 *      counts each case; the two counting stubs hand every register and the stack on unchanged
 * usage: t_shadow.exe <path to lotrbfme2ep1.exe 2.02> [casters] [frames] */
#include "t_shadow.h"
#include "orig.h"
#include "parallel.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <io.h>
#include <fcntl.h>

uint32_t OFF;
DWORD main_tid;
volatile int corrupt_on_workers;
uint32_t loop_entry;
void loop_return(void);
__asm__(".intel_syntax noprefix\n.text\n"
        ".globl _run_caster_loop\n_run_caster_loop:\n"            /* a frame like renderShadows' */
        "  push ebp\n  mov ebp, esp\n  sub esp, 0x20\n  push ebx\n  push esi\n  push edi\n"
        "  xor ebx, ebx\n  mov eax, [ebp+12]\n  mov [ebp-0x10], eax\n  mov eax, [ebp+8]\n"
        "  jmp dword ptr [_loop_entry]\n"
        ".globl _loop_return\n_loop_return:\n  pop edi\n  pop esi\n  pop ebx\n  leave\n  ret\n"
        ".att_syntax\n");

static void *__cdecl t_alloc(size_t n, int type, int flag) { (void)type; (void)flag; return calloc(1, n ? n : 1); }
static void __cdecl t_free(void *p, int type) { (void)type; free(p); }

static void jmp_at(uint32_t va, const void *to)
{
    uint8_t *p = (uint8_t *)(uintptr_t)(va + OFF);
    int32_t rel = (int32_t)((uint32_t)(uintptr_t)to - (va + OFF + 5));
    p[0] = 0xe9; memcpy(p + 1, &rel, 4);
}
static void call_at(uint32_t va, const void *to) { jmp_at(va, to); *(uint8_t *)(uintptr_t)(va + OFF) = 0xe8; }

/* the negative test: a job on a worker writes one wrong vertex */
static void __attribute__((thiscall)) bad_construct(void *sh, const float *lp, float ext, int li, int mesh)
{
    typedef void (__attribute__((thiscall)) *cv_t)(void *, const float *, float, int, int);
    ((cv_t)(uintptr_t)(0x4ef790 + OFF))(sh, lp, ext, li, mesh);
    uint8_t *vol = AT(sh, SH_VOL + mesh * 4, uint8_t *);
    if (corrupt_on_workers && GetCurrentThreadId() != main_tid && AT(vol, V_NVERTS, int) > 0)
        AT(vol, V_VERTS, float *)[0] += 1.0f;
}

/* gp_log lines of the re-applied patches go to NUL (printed once, in [0]) */
static int saved_fd = -1;
static void quiet(int on)
{
    fflush(stdout);
    if (on) { saved_fd = _dup(1); int nul = _open("NUL", _O_WRONLY); _dup2(nul, 1); _close(nul); }
    else if (saved_fd >= 0) { _dup2(saved_fd, 1); _close(saved_fd); saved_fd = -1; }
}

/* fresh original code, then the requested patches, then the test's stand-ins */
enum { P_ISQRT = 1, P_EDGE = 2, P_PAR = 4, P_STATS = 8, P_ENTRY = 16 };
static void prepare_entry(void);
static void map_raw(void)
{
    static const uint32_t pages[][2] = {{0x401000, 0x1000}, {0x42f000, 0x1000}, {0x441000, 0x1000},
        {0x475000, 0x1000}, {0x499000, 0x1000}, {0x4ef000, 0x7000}, {0x947000, 0x1000},
        {0xa3c000, 0x3000}, {0xb2b000, 0x1000}, {0xb2d000, 0x1000}, {0x8ce000, 0x1000},
        {0x449000, 0x1000}, {0x47d000, 0x1000}};
    for (unsigned i = 0; i < sizeof pages / sizeof pages[0]; i++)
        if (orig_map_at(pages[i][0], pages[i][1], OFF)) exit(2);
}

/* the vector constructor iterator is handed the element constructor 0x8cef91 as an absolute
 * address (push imm32): point those at the copy */
static void reloc_ctor(void)
{
    static const uint32_t at[] = {0x475fcd, 0x4ef56f, 0x4f0581, 0x4f220c};
    for (unsigned i = 0; i < sizeof at / sizeof at[0]; i++) {
        uint8_t *p = (uint8_t *)(uintptr_t)(at[i] + OFF);
        uint32_t v = 0x8cef91 + OFF;
        if (p[0] != 0x68 || memcmp(p + 1, "\x91\xef\x8c\x00", 4)) { printf("no push 0x8cef91 at %x\n", at[i]); exit(2); }
        memcpy(p + 1, &v, 4);
    }
}

static int map_code(int patches)
{
    map_raw();
    gp_va_offset = OFF;
    int ok = 1;
    quiet(1);
    if (patches & P_ISQRT) {
        gp_invsqrt_cont = 0x441c5b + OFF; gp_invsqrt_fn = 0x441c56 + OFF;
        ok &= gp_patch_invsqrt() && gp_patch_normtail();
    }
    if (patches & P_EDGE) ok &= gp_patch_edgemap();
    if (patches & P_PAR) {
        ok &= gp_patch_shadowpar();
        gp_sp.update = (gpf_update)fake_update;
        gp_sp.render = (gpf_render)fake_render;
        if (corrupt_on_workers) gp_sp.construct = (gpf_construct)bad_construct;
    }
    if (patches & P_STATS) ok &= gp_patch_shadowstats();
    quiet(0);
    gp_va_offset = 0;
    if (!ok) { printf("a patch refused the original bytes\n"); exit(2); }
    reloc_ctor();
    memcpy((void *)(uintptr_t)(0xb2dbf0 + OFF), "\xb8\x02\x00\x00\x00\xc3", 6);  /* frustum: inside */
    jmp_at(0x4efbeb, (void *)fake_construct_vb);
    call_at(0x4f4fbf, (void *)fake_update);
    call_at(0x4f4fd6, (void *)fake_render);
    jmp_at(0x4f4fef, (void *)loop_return);
    loop_entry = 0x4f4fe8 + OFF;
    if (patches & P_ENTRY) prepare_entry();
    return 0;
}

/* ---- [1] edgemap ------------------------------------------------------------------------------ */
typedef struct { uint16_t *sil; int count, group, real; uint8_t *sh; } scase;
static scase *cases; static int ncases;
static uint64_t *case_out;

static void add_case(uint8_t *sh, int group, int real, const uint16_t *s, int count)
{
    cases = realloc(cases, (ncases + 1) * sizeof *cases);
    cases[ncases] = (scase){malloc(count * 2 + 4), count, group, real, sh};
    memcpy(cases[ncases].sil, s, count * 2);
    cases[ncases].sil[count] = (uint16_t)(rnd() % 64); cases[ncases++].sil[count + 1] = (uint16_t)(rnd() % 64);
}

/* digest of volume + permuted silhouette per case, through constructVolume at +OFF; returns the
 * time per group (real cases only) */
static void run_cases(int reps, double *us)
{
    typedef void (__attribute__((thiscall)) *cv_t)(void *, const float *, float, int, int);
    cv_t cv = (cv_t)(uintptr_t)(0x4ef790 + OFF);
    const float lp[3] = {-2000, 1500, 3000};
    for (int i = 0; i < ncases; i++) {
        uint8_t *sh = cases[i].sh, *vol = AT(sh, SH_VOL, uint8_t *);
        uint16_t *sil = AT(sh, SH_SIL, uint16_t *);
        AT(sh, SH_SILD, int) = cases[i].count;
        AT(sh, SH_SILN, short) = (short)cases[i].count;
        int n = cases[i].real ? reps : 1;
        uint64_t t0 = now_us();
        for (int r = 0; r < n; r++) {
            memcpy(sil, cases[i].sil, cases[i].count * 2 + 4);   /* an odd count reads one past */
            cv(sh, lp, 3.5f, 0, 0);
        }
        if (cases[i].real) us[cases[i].group] += now_us() - t0;
        uint64_t h = fnv(0xcbf29ce484222325ull, sil, cases[i].count * 2 + 4);
        h = fnv(h, vol + V_NPOLYS, 8);
        h = fnv(h, AT(vol, V_VERTS, void *), AT(vol, V_NVERTS, int) * 12);
        case_out[i] = fnv(h, AT(vol, V_POLYS, void *), AT(vol, V_NPOLYS, int) * 6);
    }
}

static void random_silhouette(uint8_t *sh, int group, int nverts, int maxcount)
{
    int E = 2 + rnd() % (maxcount / 2 - 2), n = 0;
    uint16_t *s = malloc(E * 4 + 8);
    int pool = 3 + rnd() % (nverts - 3);        /* small pools: many shared starts */
    while (n < E) {
        int len = 1 + rnd() % 40, closed = rnd() % 3 != 0, first = rnd() % pool, a = first;
        for (int k = 0; k < len && n < E; k++) {
            int b = (closed && k == len - 1) ? first : (int)(rnd() % pool);
            s[2 * n] = (uint16_t)a; s[2 * n + 1] = (uint16_t)b; n++; a = b;
        }
    }
    for (int i = n - 1; i > 0; i--) {             /* shuffle the edges */
        int j = rnd() % (i + 1);
        uint32_t x, y; memcpy(&x, s + 2 * i, 4); memcpy(&y, s + 2 * j, 4);
        memcpy(s + 2 * i, &y, 4); memcpy(s + 2 * j, &x, 4);
    }
    add_case(sh, group, 0, s, 2 * n - (rnd() % 16 == 0));   /* now and then an odd count */
    free(s);
}

/* a shadow with one rigid mesh and a CPU volume, for constructVolume on its own */
static uint8_t *single_mesh_shadow(tmesh *tm)
{
    typedef char (__attribute__((thiscall)) *al_t)(void *, int, int, int);
    uint8_t *g = calloc(1, GEO_SIZE), *m = g + GEO_MESH, *obj = calloc(1, 16), *sh = calloc(1, 0x4a00);
    AT(obj, 0xc, void *) = tm->tris; AT(m, 0, void *) = obj;
    AT(m, 0x14, int) = AT(m, M_NVERTS, int) = tm->nverts; AT(m, M_NPOLYS, int) = tm->ntris;
    AT(m, 0x20, void *) = tm->remap; AT(m, M_VERTS, float *) = tm->verts;
    AT(g, GEO_NMESH, int) = 1;
    AT(sh, SH_GEOM, uint8_t *) = g;
    AT(sh, SH_SIL, void *) = calloc(32000 + 8, 2);
    AT(sh, 0x4540, short) = 32000;
    ((al_t)(uintptr_t)(0x4f114e + OFF))(sh, 0, 0, 1);
    return sh;
}

static int test_edgemap(void)
{
    typedef void (__attribute__((thiscall)) *bs_t)(void *, int, const float *);
    printf("[1] edgemap: constructVolume original vs patched\n");
    map_code(0);
    tmesh *gm[8]; int ngr = 0;
    for (int i = 0; i < nmodels && ngr < 8; i++) {          /* the largest mesh of each model */
        tmesh *b = models[i].mesh[0];
        for (int j = 1; j < models[i].nmesh; j++) if (models[i].mesh[j]->ntris > b->ntris) b = models[i].mesh[j];
        gm[ngr++] = b;
    }
    for (int gi = 0; gi < ngr; gi++) {
        uint8_t *sh = single_mesh_shadow(gm[gi]);
        for (int i = 0; i < 100; i++) {                     /* what the game's buildSilhouette makes */
            float lp[3] = {frnd(-3000, 3000), frnd(-3000, 3000), frnd(-500, 3000)};
            AT(sh, SH_SILN, short) = 0;
            ((bs_t)(uintptr_t)(0x4f2614 + OFF))(sh, 0, lp);
            add_case(sh, gi, 1, AT(sh, SH_SIL, uint16_t *), AT(sh, SH_SILD, int));
        }
        for (int i = 0; i < 400; i++) random_silhouette(sh, gi, gm[gi]->nverts, i % 10 == 0 ? 8000 : 400);
    }
    case_out = malloc(ncases * 8);
    uint64_t *ref = malloc(ncases * 8);
    double t_orig[8] = {0}, t_new[8] = {0};
    run_cases(20, t_orig);
    memcpy(ref, case_out, ncases * 8);
    map_code(P_EDGE);
    run_cases(20, t_new);
    int bad = 0, nreal = 0, maxc = 0;
    long long edges = 0;
    for (int i = 0; i < ncases; i++) {
        if (case_out[i] != ref[i]) { if (bad < 5) printf("  MISMATCH case %d (count %d)\n", i, cases[i].count); bad++; }

        edges += cases[i].count / 2; nreal += cases[i].real;
        if (cases[i].count > maxc) maxc = cases[i].count;
    }
    printf("    %d silhouettes from the game's buildSilhouette on %d meshes + %d random edge sets; %lld edges, "
           "up to %d indices: %d mismatches\n", nreal, ngr, ncases - nreal, edges, maxc, bad);
    for (int gi = 0; gi < ngr; gi++) {
        long long e = 0; int n = 0;
        for (int i = 0; i < ncases; i++) if (cases[i].real && cases[i].group == gi) { e += cases[i].count / 2; n++; }
        printf("    %-12s %5d triangles, silhouettes of %4lld edges: original %7.1f us, edgemap %6.1f us per volume (%.1fx)\n",
               gm[gi]->name, gm[gi]->ntris, e / n, t_orig[gi] / (20.0 * n), t_new[gi] / (20.0 * n), t_orig[gi] / t_new[gi]);
    }
    int pbad = 0;                                           /* index vs linear permutation */
    for (int i = 0; i < ncases; i++) {
        int n = cases[i].count;
        uint16_t *a = malloc(n * 2 + 4), *b = malloc(n * 2 + 4);
        memcpy(a, cases[i].sil, n * 2 + 4); memcpy(b, cases[i].sil, n * 2 + 4);
        gp_cv_permute(a, n, 0); gp_cv_permute(b, n, -1);
        pbad += memcmp(a, b, n * 2 + 4) != 0;
        free(a); free(b);
    }
    printf("    permutation with the index == linear search on all %d cases: %d differ\n", ncases, pbad);
    return bad + pbad;
}

/* ---- [2] worlds ------------------------------------------------------------------------------- */
static void via_entry(uint8_t *first, uint8_t *list);
static int compare_world(const char *label, const world_cfg *c, world_out *ref, world_out *o)
{
    int bad = ref->draws != o->draws || ref->builds != o->builds || ref->ncalls != o->ncalls, first = -1;
    for (int f = 0; f < c->frames; f++) if (ref->frame_digest[f] != o->frame_digest[f]) { bad = 1; if (first < 0) first = f; }
    printf("    %-44s %s  (%lld draws/builds; caster loop %.0f us/frame", label,
           bad ? "DIFFERS" : "identical", o->ncalls, o->loop_us / (c->frames - 1));
    if (first >= 0) printf("; first differing frame %d", first);
    printf(")\n");
    return bad;
}

static void run_world(const world_cfg *c, int patches, world_out *o)
{
    map_code(patches);
    world_runner = patches & P_ENTRY ? via_entry : run_caster_loop;
    world_build(c);
    world_run(c, o);
    world_free();
}

static int test_worlds(int ncasters, int frames)
{
    world_cfg c = {ncasters, frames, 25, 777};
    world_out o[8];
    for (int i = 0; i < 8; i++) o[i].frame_digest = calloc(frames, 8);
    printf("[2] worlds: %d casters over %d models (skinned, and rigid copies with CPU or static volumes), %d frames\n",
           ncasters, nmodels, frames);
    int bad = 0;
    gp_spc.verify = 0; gp_spc.sample = 0; gp_spc.log_every = 0;
    run_world(&c, 0, &o[0]);
    printf("    %-44s reference  (%lld draws/builds; caster loop %.0f us/frame)\n", "original code", o[0].ncalls, o[0].loop_us / (frames - 1));
    run_world(&c, P_ISQRT, &o[1]);
    bad += compare_world("+ invsqrt/normtail (the game's other patches)", &c, &o[0], &o[1]);
    run_world(&c, P_ISQRT | P_EDGE, &o[2]);
    bad += compare_world("+ edgemap", &c, &o[0], &o[2]);
    gp_sp_stats_t s0 = gp_sp_stats;
    run_world(&c, P_ISQRT | P_PAR, &o[3]);
    bad += compare_world("+ shadowpar", &c, &o[0], &o[3]);
    run_world(&c, P_ISQRT | P_EDGE | P_PAR, &o[4]);
    bad += compare_world("+ edgemap + shadowpar", &c, &o[0], &o[4]);
    printf("      (pool: %d workers + main; %lld volumes built on the pool in %lld items, %lld blocks inline, %lld faults)\n",
           gp_sp_nslots - 1, gp_sp_stats.jobs - s0.jobs, gp_sp_stats.items - s0.items,
           gp_sp_stats.inline_blocks - s0.inline_blocks, gp_sp_stats.faults - s0.faults);
    if (gp_sp_stats.jobs == s0.jobs) { printf("    no job ran on the pool\n"); bad++; }
    gp_spc.verify = 1 << 30;
    s0 = gp_sp_stats;
    run_world(&c, P_ISQRT | P_EDGE | P_PAR, &o[5]);
    bad += compare_world("+ edgemap + shadowpar, verify mode", &c, &o[0], &o[5]);
    printf("      (verified %lld volumes, %lld mismatches; serial %.0f us vs parallel %.0f us in total)\n",
           gp_sp_stats.verified_jobs - s0.verified_jobs, gp_sp_stats.mismatches - s0.mismatches,
           gp_sp_stats.ref_us - s0.ref_us, gp_sp_stats.par_us - s0.par_us);
    bad += gp_sp_stats.mismatches != s0.mismatches || gp_sp_disabled;
    corrupt_on_workers = 1;
    s0 = gp_sp_stats;
    run_world(&c, P_ISQRT | P_EDGE | P_PAR, &o[6]);
    corrupt_on_workers = 0;
    int caught = gp_sp_disabled && gp_sp_stats.mismatches > s0.mismatches;
    bad += compare_world("verify mode, workers' results corrupted", &c, &o[0], &o[6]);
    printf("      (verify caught it: %s; %lld mismatches, shadowpar switched itself off)\n", caught ? "yes" : "NO",
           gp_sp_stats.mismatches - s0.mismatches);
    bad += !caught;
    gp_sp_disabled = 0;
    gp_spc.verify = 0;
    printf("    caster loop after frame 0 (which builds the neighbor arrays): with invsqrt/normtail %.0f us/frame, "
           "+ edgemap %.0f, + edgemap + shadowpar %.0f (%.2fx)\n", o[1].loop_us / (frames - 1),
           o[2].loop_us / (frames - 1), o[4].loop_us / (frames - 1), o[1].loop_us / o[4].loop_us);
    return bad;
}

/* ---- [3] A1 ---------------------------------------------------------------------------------- */
static int test_a1(void)
{
    typedef void (__attribute__((thiscall)) *bn_t)(void *);
    int bad = 0, n = 0;
    long long tris = 0;
    double us[2] = {0, 0};
    uint8_t *g = calloc(1, GEO_SIZE), *m = g + GEO_MESH, *obj = calloc(1, 16);
    for (int pass = 0; pass < 2; pass++) {
        static uint64_t ref[64];
        map_code(pass ? P_ISQRT | P_PAR : P_ISQRT);
        gp_spc.a1_min = 64;
        n = 0;
        for (int i = 0; i < nmodels; i++)
            for (int j = 0; j < models[i].nmesh && n < 64; j++, n++) {
                tmesh *tm = models[i].mesh[j];
                memset(m, 0, MESH_SIZE);
                AT(obj, 0xc, void *) = tm->tris; AT(m, 0, void *) = obj;
                AT(m, 0x14, int) = AT(m, M_NVERTS, int) = tm->nverts; AT(m, M_NPOLYS, int) = tm->ntris;
                AT(m, 0x20, void *) = tm->remap; AT(m, M_VERTS, float *) = tm->verts; m[M_SKINNED] = 1;
                uint64_t t0 = now_us();
                for (int r = 0; r < 20; r++) { AT(m, M_NORMALS, void *) = NULL; ((bn_t)(uintptr_t)(0x4f21b2 + OFF))(m); }
                us[pass] += now_us() - t0;
                uint64_t h = fnv(0xcbf29ce484222325ull, AT(m, M_NORMALS, void *), tm->ntris * 12);
                if (!pass) { ref[n] = h; tris += tm->ntris; }
                else bad += h != ref[n];
            }
    }
    gp_spc.a1_min = 1024;
    printf("[3] A1: buildPolygonNormals, triangle loop on the pool vs original: %d meshes, %lld triangles, %d differ;\n"
           "    %.0f vs %.0f ns per triangle (pool from 64 triangles here; the game default is 1024)\n",
           n, tris, bad, us[0] * 1000 / (20.0 * tris), us[1] * 1000 / (20.0 * tris));
    return bad;
}

/* ---- [4] the per-frame entry ------------------------------------------------------------------ */
static uint8_t scene_obj[8];                  /* TheW3DShadowManager as 0x499d6d sees it: byte 0 = shadow scene */
static uint8_t fake_gd[0x100];                /* TheGlobalData: +0x60 UseShadowVolumes, +0x62 mapping */
static uint32_t fake_cam[0x80], rinfo[4];
static int entry_cfg, flag_left;              /* 0 as in game; 1 volumes off; 2 no device; 3 no casters */
static void __attribute__((thiscall)) stub_ret0(void *t) { (void)t; }
static void __attribute__((thiscall)) stub_ret4(void *t, int a) { (void)t; (void)a; }
static void __attribute__((thiscall)) stub_ret12(void *t, int a, int b, int c) { (void)t; (void)a; (void)b; (void)c; }

/* the camera / terrain calls in 0x4f43a6's prologue become no-ops; the D3D render-state block
 * 0x4f4473..0x4f4f95 and the one after the loop are skipped (the loop's own frame setup at
 * 0x4f4f95 and the epilogue 0x4f53a9 run) */
static void prepare_entry(void)
{
    call_at(0x4f43c0, (void *)stub_ret0);     /* 0x533b70 camera */
    call_at(0x4f43d1, (void *)stub_ret4);     /* 0x4f123e */
    call_at(0x4f43e9, (void *)stub_ret12);    /* 0x46aa05 terrain */
    jmp_at(0x4f4473, (void *)(uintptr_t)(0x4f4f95 + OFF));
    jmp_at(0x4f4fef, (void *)(uintptr_t)(0x4f53a9 + OFF));
    *(uint8_t **)0xde4364 = fake_gd;
    *(void **)0xdd1d0c = NULL;
    rinfo[0] = (uint32_t)(uintptr_t)fake_cam;
}

static void via_entry(uint8_t *first, uint8_t *list)
{
    typedef void (__attribute__((thiscall)) *rs_t)(void *, void *);
    AT(list, 0, uint8_t *) = entry_cfg == 3 ? NULL : first;
    fake_gd[0x60] = entry_cfg != 1;
    *(void **)0xdd3474 = entry_cfg == 2 ? NULL : (void *)fake_gd;
    *(uint8_t **)0xdd1718 = list;             /* TheW3DVolumetricShadowManager: [0] casters, [4] tasks */
    scene_obj[0] = 1;
    ((rs_t)(uintptr_t)(0x499d6d + OFF))(scene_obj, rinfo);
    flag_left += scene_obj[0] != 0;           /* 0x499d6d clears the shadow-scene byte */
}

/* the counting stubs: registers and stack as the call left them, return to the call's next insn */
uint32_t stub_target, seen[5];
void stub_standin(void); uint32_t call_stub(void); void after_stub(void);
__asm__(".intel_syntax noprefix\n.text\n"
        ".globl _stub_standin\n_stub_standin:\n  mov [_seen], eax\n  mov [_seen+4], ecx\n  mov [_seen+8], edx\n"
        "  mov eax, [esp+4]\n  mov [_seen+12], eax\n  mov eax, [esp]\n  mov [_seen+16], eax\n  ret 4\n"
        ".globl _call_stub\n_call_stub:\n  push ebx\n  push esi\n  push edi\n  push ebp\n"
        "  mov eax, 0x11111111\n  mov ecx, offset _fake_gd\n  mov edx, 0x22222222\n  mov ebx, 0x33333333\n"
        "  mov esi, 0x55555555\n  mov edi, 0x66666666\n  mov ebp, 0x77777777\n  push 0x44444444\n"
        "  call dword ptr [_stub_target]\n.globl _after_stub\n_after_stub:\n"
        "  xor eax, eax\n  cmp ebx, 0x33333333\n  setne al\n  cmp esi, 0x55555555\n  setne ah\n"
        "  cmp edi, 0x66666666\n  jne 1f\n  cmp ebp, 0x77777777\n  je 2f\n1: or eax, 0x10000\n"
        "2: pop ebp\n  pop edi\n  pop esi\n  pop ebx\n  ret\n.att_syntax\n");

static int test_stubs(void)
{
    int bad = 0;
    uint32_t cont[2] = {gp_shst_rs_cont, gp_shst_sm_cont};
    void (*stub[2])(void) = {gp_shst_rs_stub, gp_shst_sm_stub};
    memset(fake_gd, 0, sizeof fake_gd);        /* as a manager: no casters */
    for (int k = 0; k < 2; k++) {
        gp_shst_rs_cont = gp_shst_sm_cont = (uint32_t)(uintptr_t)stub_standin;
        stub_target = (uint32_t)(uintptr_t)stub[k];
        memset(seen, 0, sizeof seen);
        uint32_t r = call_stub();
        if (r || seen[0] != 0x11111111 || seen[1] != (uint32_t)(uintptr_t)fake_gd || seen[2] != 0x22222222 ||
            seen[3] != 0x44444444 || seen[4] != (uint32_t)(uintptr_t)after_stub) {
            printf("    %s stub: registers or stack changed (%x; eax %x ecx %x edx %x arg %x ret %x)\n", k ? "shadow-map" : "renderShadows",
                   r, seen[0], seen[1], seen[2], seen[3], seen[4]);
            bad++;
        }
    }
    gp_shst_rs_cont = cont[0]; gp_shst_sm_cont = cont[1];
    return bad;
}

static int test_entry(void)
{
    world_cfg c = {60, 12, 25, 4242};
    world_out o[3];
    for (int i = 0; i < 3; i++) o[i].frame_digest = calloc(c.frames, 8);
    printf("[4] per-frame entry 0x499d6d -> 0x4f43a6 -> caster loop, %d casters, %d frames, shadowstats installed\n",
           c.ncasters, c.frames);
    int bad = 0;
    gp_spc.verify = 0; gp_spc.sample = 0; gp_spc.log_every = 0;
    entry_cfg = 0; flag_left = 0;
    run_world(&c, 0, &o[0]);
    printf("    %-44s reference  (%lld draws/builds)\n", "original caster loop, run directly", o[0].ncalls);
    gp_shst_t s0 = gp_shst;
    run_world(&c, P_ENTRY | P_STATS, &o[1]);
    bad += compare_world("original code through the entry", &c, &o[0], &o[1]);
    long long l0 = gp_sp_loops, j0 = gp_sp_stats.jobs;
    run_world(&c, P_ENTRY | P_STATS | P_ISQRT | P_EDGE | P_PAR, &o[2]);
    bad += compare_world("+ edgemap + shadowpar through the entry", &c, &o[0], &o[2]);
    long reach = gp_shst.rs_reach - s0.rs_reach, calls = gp_shst.rs_calls - s0.rs_calls;
    printf("      (renderShadows %ld calls, %ld reached the caster loop; shadowpar ran %lld loops, %lld volumes on "
           "the pool; shadow-scene byte left set %d times)\n", calls, reach, gp_sp_loops - l0, gp_sp_stats.jobs - j0, flag_left);
    bad += calls != 2 * c.frames || reach != 2 * c.frames || gp_sp_loops - l0 != c.frames || gp_sp_stats.jobs == j0 || flag_left;
    static const char *what[] = {"", "volume shadows off (UseShadowMapping)", "no device", "no casters"};
    for (entry_cfg = 1; entry_cfg <= 3; entry_cfg++) {
        world_cfg e = {20, 3, 25, 99};
        world_out w; w.frame_digest = calloc(e.frames, 8);
        s0 = gp_shst; l0 = gp_sp_loops;
        run_world(&e, P_ENTRY | P_STATS | P_EDGE | P_PAR, &w);
        LONG n = entry_cfg == 1 ? gp_shst.rs_voloff - s0.rs_voloff : entry_cfg == 2 ? gp_shst.rs_nodev - s0.rs_nodev
               : gp_shst.rs_empty - s0.rs_empty;
        int ok = w.ncalls == 0 && gp_sp_loops == l0 && n == e.frames && gp_shst.rs_reach == s0.rs_reach && !flag_left;
        printf("    %-44s %s  (%lld draws/builds, %lld caster loops, counted %ld of %d)\n", what[entry_cfg],
               ok ? "loop not run" : "WRONG", w.ncalls, gp_sp_loops - l0, n, e.frames);
        bad += !ok;
        free(w.frame_digest);
    }
    entry_cfg = 0;
    int sb = test_stubs();
    printf("    counting stubs: registers, argument and return address handed on unchanged: %s\n", sb ? "NO" : "yes");
    for (int i = 0; i < 3; i++) free(o[i].frame_digest);
    return bad + sb;
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    /* the game's data pages the code uses by absolute address: reserved before anything (the
     * 12 MB exe buffer of orig_load) can land on them, committed once the file is read */
    static const uint32_t data[][2] = {{0xbd0000, 0x9000}, {0xbe5000, 0x1000}, {0xc1b000, 0x1000},
        {0xdc3000, 0x1000}, {0xdc5000, 0x1000}, {0xdcb000, 0x1000}, {0xdd1000, 0x1000},
        {0xdc7000, 0x1000}, {0xdd3000, 0x1000}, {0xde4000, 0x1000}};
    for (unsigned i = 0; i < sizeof data / sizeof data[0]; i++) {
        uint32_t a = data[i][0] & ~0xffffu, e = (data[i][0] + data[i][1] + 0xffff) & ~0xffffu;
        for (; a < e; a += 0x10000) {
            MEMORY_BASIC_INFORMATION mi;
            VirtualQuery((void *)(uintptr_t)a, &mi, sizeof mi);
            if (mi.State == MEM_FREE && !VirtualAlloc((void *)(uintptr_t)a, 0x10000, MEM_RESERVE, PAGE_EXECUTE_READWRITE)) {
                printf("cannot reserve %08x\n", a); return 2;
            }
            if (mi.State == MEM_COMMIT) { printf("%08x is already in use in this process\n", a); return 2; }
        }
    }
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    for (unsigned i = 0; i < sizeof data / sizeof data[0]; i++)
        if (orig_map_at(data[i][0], data[i][1], 0)) return 2;
    int ncasters = argc > 2 ? atoi(argv[2]) : 160, frames = argc > 3 ? atoi(argv[3]) : 24;
    main_tid = GetCurrentThreadId();
    if (!(OFF = orig_reserve_image())) return 2;
    HMODULE crt = LoadLibraryA("msvcr71.dll"), dx = LoadLibraryA("d3dx9_27.dll");
    if (!crt || !dx) { printf("msvcr71.dll or d3dx9_27.dll not loadable\n"); return 2; }
    *(void **)0xbd06a8 = GetProcAddress(crt, "fabs");
    *(void **)0xbd06a0 = GetProcAddress(crt, "sqrt");
    *(void **)0xbd0574 = GetProcAddress(crt, "abs");
    *(void **)0xbd09c4 = GetProcAddress(dx, "D3DXMatrixInverse");
    *(void **)0xdc5e44 = (void *)t_alloc;
    *(void **)0xdc5e3c = (void *)t_free;
    *(float *)0xdd1848 = 0.9999f;                     /* cosAngleToCare (set at game start) */
    unsigned short cw = 0x007f;                       /* the game's FPU mode (0x440809) */
    __asm__ volatile("fninit\n fldcw %0" : : "m"(cw));

    int nw = load_w3d_models(argv[1]);
    add_synthetic_models();
    long long tris = 0; int nm = 0;
    for (int i = 0; i < nmodels; i++) for (int j = 0; j < models[i].nmesh; j++) { tris += models[i].mesh[j]->ntris; nm++; }
    printf("models: %d from the game's W3D.big, %d synthetic; %d meshes, %lld triangles:", nw, nmodels - nw, nm, tris);
    for (int i = 0; i < nmodels; i++) printf(" %s", models[i].name);
    printf("\n");

    int fail = 0;
    map_raw();
    gp_va_offset = OFF;
    int ok = gp_patch_edgemap() + gp_patch_shadowpar() + gp_patch_shadowstats();
    gp_va_offset = 0;
    printf("[0] %d of 3 patches applied to the original bytes\n", ok);
    fail |= ok != 3;
    fail |= test_edgemap() != 0;
    fail |= test_worlds(ncasters, frames) != 0;
    fail |= test_a1() != 0;
    fail |= test_entry() != 0;
    printf("%s\n", fail ? "FAIL" : "PASS");
    return fail;
}
