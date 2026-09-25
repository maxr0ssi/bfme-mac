/* t_perf: perfmarker and passtimers against the game's own marker code, run in place: PerfTimer
 * begin 0x517690, end 0x517740 and the D3DPERF wrappers 0x51ece0/0x51ed60 at their addresses +
 * offset, .rdata/.data at their own addresses (strncpy's IAT slot filled from msvcr71, as the
 * loader does).
 *   [1] perfmarker: begin called with every combination of name (none, short, 300 chars), suffix
 *       (none, "Frame") and D3DPERF pointer (null, a recording BeginEvent), original vs patched:
 *       with a pointer everything must be identical (return value, registers, the object's bytes,
 *       the recorded events); without one the patched begin must return `this` at once, keep
 *       every register the original keeps, and call nothing;
 *   [3] the four callers' name-building blocks (MeshDX8Render x2, MeshFXShader x2) run from their
 *       entry to their resume point, original vs patched, pointer null and set, with and without a
 *       mesh name: with the pointer everything is identical (registers, stack bytes, events);
 *       without it the patched block writes nothing, leaves esp where the original does and keeps
 *       ebx ebp (and esi edi in the FX blocks);
 *   [2] passtimers: installed into the real pointers, a scripted frame (nested passes with known
 *       sleeps, 20 mesh draws with per-mesh names) runs 10 times through the original markers;
 *       the summary must count 10 frames, the right calls per frame, one bucket for all mesh
 *       draws, inclusive >= self >= the sleeps, and ignore events from another thread; events of a
 *       second top-level pass (UpdateShadowMap) go to "UpdateShadowMap/<name>" buckets.
 * usage: t_perf.exe <path to lotrbfme2ep1.exe 2.02> */
#include "orig.h"
#include "gp.h"
#include "gp_render.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stddef.h>

static uint32_t OFF;
#define BEGIN_PTR (*(volatile uint32_t *)0xdd361c)
#define END_PTR (*(volatile uint32_t *)0xdd3620)

/* ---- register harness (as t_regs) ---- */
typedef struct {
    uint32_t fn, nargs, args[6];   /*  0, 4, 8 */
    uint32_t in[7], out[7];        /* 32, 60: eax ebx ecx edx esi edi ebp */
    uint8_t xin[128], xout[128];   /* 88, 216 */
    int32_t esp_delta;             /* 344 */
} ctx_t;
_Static_assert(offsetof(ctx_t, esp_delta) == 344, "layout");
ctx_t *cur_ctx; uint32_t saved_esp, target;
__asm__(".text\n"
"_regcall:\n"
"  pushl %ebp\n  pushl %ebx\n  pushl %esi\n  pushl %edi\n"
"  movl 20(%esp), %eax\n  movl %eax, _cur_ctx\n  movl %esp, _saved_esp\n"
"  movups 88(%eax), %xmm0\n  movups 104(%eax), %xmm1\n  movups 120(%eax), %xmm2\n  movups 136(%eax), %xmm3\n"
"  movups 152(%eax), %xmm4\n  movups 168(%eax), %xmm5\n  movups 184(%eax), %xmm6\n  movups 200(%eax), %xmm7\n"
"  movl 4(%eax), %ecx\n"
"1: testl %ecx, %ecx\n  jz 2f\n  pushl 4(%eax,%ecx,4)\n  decl %ecx\n  jmp 1b\n"
"2: movl (%eax), %ecx\n  movl %ecx, _target\n"
"  movl 36(%eax), %ebx\n  movl 40(%eax), %ecx\n  movl 44(%eax), %edx\n  movl 48(%eax), %esi\n"
"  movl 52(%eax), %edi\n  movl 56(%eax), %ebp\n  movl 32(%eax), %eax\n"
"  call *_target\n"
"  pushl %eax\n  movl _cur_ctx, %eax\n  popl 60(%eax)\n"
"  movl %ebx, 64(%eax)\n  movl %ecx, 68(%eax)\n  movl %edx, 72(%eax)\n  movl %esi, 76(%eax)\n"
"  movl %edi, 80(%eax)\n  movl %ebp, 84(%eax)\n"
"  movups %xmm0, 216(%eax)\n  movups %xmm1, 232(%eax)\n  movups %xmm2, 248(%eax)\n  movups %xmm3, 264(%eax)\n"
"  movups %xmm4, 280(%eax)\n  movups %xmm5, 296(%eax)\n  movups %xmm6, 312(%eax)\n  movups %xmm7, 328(%eax)\n"
"  movl %esp, %ecx\n  subl _saved_esp, %ecx\n  movl %ecx, 344(%eax)\n"
"  movl _saved_esp, %esp\n"
"  popl %edi\n  popl %esi\n  popl %ebx\n  popl %ebp\n  ret\n");
void regcall(ctx_t *c);
static const char *rn[7] = {"eax", "ebx", "ecx", "edx", "esi", "edi", "ebp"};

/* runs a block of game code from its entry with the given registers and stack until the resume
 * point, where a jmp to rb_exit was written: rb_t = in eax ebx ecx edx esi edi ebp, out (same), esp */
typedef struct { uint32_t in[7], out[7], esp; } rb_t;
uint32_t rb_saved_esp, rb_entry, rb_tmp; rb_t *rb_cur;
__asm__(".text\n"
"_run_block:\n"                          /* cdecl run_block(entry, rb_t *r, stack pointer) */
"  pushl %ebp\n  pushl %ebx\n  pushl %esi\n  pushl %edi\n"
"  movl %esp, _rb_saved_esp\n"
"  movl 20(%esp), %eax\n  movl %eax, _rb_entry\n  movl 24(%esp), %edx\n  movl %edx, _rb_cur\n"
"  movl 28(%esp), %esp\n"
"  movl 4(%edx), %ebx\n  movl 8(%edx), %ecx\n  movl 16(%edx), %esi\n  movl 20(%edx), %edi\n"
"  movl 24(%edx), %ebp\n  movl 0(%edx), %eax\n  movl 12(%edx), %edx\n"
"  jmp *_rb_entry\n"
"_rb_exit:\n"                              /* writes nothing to the block's stack */
"  movl %eax, _rb_tmp\n  movl _rb_cur, %eax\n"
"  movl %ebx, 32(%eax)\n  movl %ecx, 36(%eax)\n  movl %edx, 40(%eax)\n  movl %esi, 44(%eax)\n"
"  movl %edi, 48(%eax)\n  movl %ebp, 52(%eax)\n  movl %esp, 56(%eax)\n"
"  movl _rb_tmp, %ecx\n  movl %ecx, 28(%eax)\n"
"  movl _rb_saved_esp, %esp\n"
"  popl %edi\n  popl %esi\n  popl %ebx\n  popl %ebp\n  ret\n");
void run_block(uint32_t entry, rb_t *r, void *sp);
static uint32_t norm(uint32_t v, uint32_t off) { return v >= 0x401000 + off && v < 0xbd0000 + off ? v - off : v; }
void rb_exit(void);

/* a recording D3DPERF_BeginEvent */
static char events[8192];
static int WINAPI rec_begin(DWORD color, const WCHAR *name)
{
    char l[300]; int n = snprintf(l, sizeof l, "begin %08lx '", (unsigned long)color);
    for (int i = 0; name[i] && n < 290; i++) l[n++] = (char)name[i];
    l[n++] = '\''; l[n++] = '\n'; l[n] = 0;
    if (strlen(events) + n < sizeof events) strcat(events, l);
    return 0;
}

typedef struct { ctx_t c; uint8_t obj[0x140]; char ev[8192]; } result_t;
static void call_begin(result_t *r, const char *name, const char *suffix, int with_ptr)
{
    static uint8_t obj[0x140];
    memset(obj, 0xab, sizeof obj); events[0] = 0;
    memset(&r->c, 0, sizeof r->c);
    for (int i = 0; i < 7; i++) r->c.in[i] = 0x01010101u * (i + 3);
    r->c.in[2] = (uint32_t)(uintptr_t)obj;
    for (int i = 0; i < 128; i++) r->c.xin[i] = (uint8_t)(0x3c ^ i * 11);
    r->c.fn = 0x517690 + OFF; r->c.nargs = 3;
    r->c.args[0] = (uint32_t)(uintptr_t)name; r->c.args[1] = (uint32_t)(uintptr_t)suffix; r->c.args[2] = 0x00ff8000;
    BEGIN_PTR = with_ptr ? (uint32_t)(uintptr_t)rec_begin : 0;
    regcall(&r->c);
    BEGIN_PTR = 0;
    memcpy(r->obj, obj, sizeof obj); strcpy(r->ev, events);
}

/* ---- [2] ---- */
static char report[16][512]; static int nrep;
static void sink(const char *line) { if (nrep < 16) snprintf(report[nrep++], 512, "%s", line); }
typedef struct { uint8_t b[0x140]; } timer_t_;
static void begin(timer_t_ *t, const char *name, const char *suffix)
{
    typedef void *(__attribute__((thiscall)) *fn_t)(void *, const char *, const char *, DWORD);
    ((fn_t)(uintptr_t)(0x517690 + OFF))(t, name, suffix, 0);
}
static void end(timer_t_ *t)
{
    typedef int (__attribute__((thiscall)) *fn_t)(void *);
    ((fn_t)(uintptr_t)(0x517740 + OFF))(t);
}
static void busy_us(unsigned us) { uint64_t t = now_us(); while (now_us() - t < us) ; }
static DWORD WINAPI other_thread(LPVOID p) { (void)p; timer_t_ t; begin(&t, "RenderViews", "Frame"); end(&t); return 0; }
static double field(const char *line, const char *name, int which)    /* incl (0), self (1), calls (2) */
{
    const char *p = line;                    /* a whole item: after "  " or "| ", followed by a space */
    size_t n = strlen(name);
    while ((p = strstr(p, name)) && !(p - line >= 2 && p[-1] == ' ' && (p[-2] == ' ' || p[-2] == '|') && p[n] == ' ')) p++;
    if (!p) return -1;
    double a, b, c;
    if (sscanf(p + strlen(name), " %lf/%lf (%lf)", &a, &b, &c) != 3) return -1;
    return which == 0 ? a : which == 1 ? b : c;
}

int main(int argc, char **argv)
{
    int fail = 0;
    setvbuf(stdout, NULL, _IONBF, 0);
    if (orig_load(argc > 1 ? argv[1] : orig_default_path())) return 2;
    if (orig_map_at(0xbd0000, 0x1b9000, 0) || orig_map_at(0xd89000, 0x81000, 0)) return 2;
    OFF = orig_reserve_image();
    static const uint32_t pages[] = {0x517000, 0x51e000, 0x543000, 0x569000, 0x573000, 0xa3c000, 0xa3d000};
    for (unsigned i = 0; i < sizeof pages / 4; i++) if (!OFF || orig_map_at(pages[i], 0x1000, OFF)) return 2;
    HMODULE crt = LoadLibraryA("msvcr71.dll");
    *(void **)0xbd0624 = (void *)GetProcAddress(crt, "strncpy");   /* the IAT slot 0x517690 calls */
    BEGIN_PTR = END_PTR = 0;

    /* [1] */
    static char longname[301];
    memset(longname, 'x', 300); memcpy(longname, "Rendering mesh\tDX8Render\t", 25);
    const char *names[] = {NULL, "RenderViews", longname};
    const char *suffixes[] = {NULL, "Frame"};
    static result_t A[12], B[12];
    for (int i = 0; i < 12; i++) call_begin(&A[i], names[i % 3], suffixes[i / 3 % 2], i / 6);
    gp_va_offset = OFF;
    int ok = gp_patch_perfmarker();
    gp_va_offset = 0;
    printf("[1] perfmarker applied to the original bytes: %s\n", ok ? "yes" : "NO");
    if (!ok) { printf("FAIL\n"); return 1; }
    for (int i = 0; i < 12; i++) call_begin(&B[i], names[i % 3], suffixes[i / 3 % 2], i / 6);
    for (int i = 0; i < 12; i++) {
        int ptr = i / 6, bad = 0;
        if (ptr) {
            bad = memcmp(A[i].c.out, B[i].c.out, sizeof A[i].c.out) || memcmp(A[i].c.xout, B[i].c.xout, 128) ||
                  memcmp(A[i].obj, B[i].obj, sizeof A[i].obj) || strcmp(A[i].ev, B[i].ev) ||
                  A[i].c.esp_delta != B[i].c.esp_delta;
        } else {
            for (int r = 0; r < 7; r++) if (r && A[i].c.out[r] == A[i].c.in[r] && B[i].c.out[r] != B[i].c.in[r]) bad++;
            bad += A[i].c.out[0] != A[i].c.in[2] || B[i].c.out[0] != B[i].c.in[2];     /* returns this */
            bad += A[i].c.esp_delta != B[i].c.esp_delta || B[i].ev[0] || A[i].ev[0];
            for (int x = 0; x < 8; x++)                       /* xmm the original keeps (strncpy may not) */
                bad += !memcmp(A[i].c.xout + 16 * x, A[i].c.xin + 16 * x, 16) &&
                       memcmp(B[i].c.xout + 16 * x, B[i].c.xin + 16 * x, 16);
        }
        const char *nm = names[i % 3] ? (names[i % 3] == longname ? "300 chars" : names[i % 3]) : "none";
        printf("[1] name %-11s suffix %-5s pointer %-4s: %s%s", nm, suffixes[i / 3 % 2] ? "Frame" : "none",
               ptr ? "set" : "null", bad ? "DIFFERS" : ptr ? "identical (registers, object, events)" :
               "returns this at once, registers kept", ptr && A[i].ev[0] ? ", event " : "\n");
        if (ptr && A[i].ev[0]) {
            char e[64]; snprintf(e, sizeof e, "%s", A[i].ev + 15);
            for (char *p = e; *p; p++) if (*p == '\t' || *p == '\n') *p = ' ';
            printf("%.42s%s\n", e, strlen(A[i].ev) > 57 ? "..." : "");
        }
        fail |= bad != 0;
    }
    for (int r = 0; r < 7; r++) if (r != 0 && B[1].c.out[r] != B[1].c.in[r]) printf("    (patched, no pointer: %s changed)\n", rn[r]);
    {   /* cost of one mesh-draw marker without a pointer: the original bytes kept in a copy */
        uint8_t *orig = orig_copy(0x517690, 0xa7, 0);
        orig_fix_rel32(orig, 0x517690, 0x517727, (void *)(uintptr_t)(0x51ece0 + OFF));
        static uint8_t obj[0x140]; const int N = 200000; uint64_t t[2];
        typedef void *(__attribute__((thiscall)) *fn_t)(void *, const char *, const char *, DWORD);
        for (int k = 0; k < 2; k++) {
            fn_t f = (fn_t)(uintptr_t)(k ? 0x517690 + OFF : (uint32_t)(uintptr_t)orig);
            uint64_t t0 = now_us();
            for (int i = 0; i < N; i++) f(obj, "Rendering mesh\tDX8Render\tinfantry_skn", "MeshDX8Render", 0);
            t[k] = now_us() - t0;
        }
        printf("[1] one mesh-draw begin marker: original %.0f ns, patched %.0f ns\n", t[0] * 1000.0 / N, t[1] * 1000.0 / N);
    }

    /* [3] the callers' name-building blocks: a pristine copy (A) and the one patched in [1] (B),
     * each with a jmp back to the harness written at the four resume points */
    uint32_t offa = orig_reserve_image();
    for (unsigned i = 0; i < sizeof pages / 4; i++) if (!offa || orig_map_at(pages[i], 0x1000, offa)) return 2;
    static const uint32_t entry[4] = {0x543170, 0x5432b0, 0x573d3a, 0x573dc6}, resume[4] = {0x5431e7, 0x543326, 0x573d9a, 0x573e1d};
    for (int k = 0; k < 2; k++)
        for (int b = 0; b < 4; b++) {
            uint8_t *at = (uint8_t *)(uintptr_t)(resume[b] + (k ? OFF : offa));
            int32_t rel = (int32_t)((uint32_t)(uintptr_t)rb_exit - (uint32_t)(uintptr_t)(at + 5));
            at[0] = 0xe9; memcpy(at + 1, &rel, 4);
        }
    *(void **)0xbd06c0 = (void *)GetProcAddress(crt, "sprintf");
    *(void **)0xbd06d0 = (void *)GetProcAddress(crt, "_mbscpy");
    *(void **)0xbd05ec = (void *)GetProcAddress(crt, "_mbscat");
    static char meshname[] = "infantry_uruk_skn";
    static uint32_t namestruct[4], model[8], mesh[4], fxobj[64], cell[1];
    namestruct[3] = (uint32_t)(uintptr_t)meshname;
    model[4] = (uint32_t)(uintptr_t)namestruct;
    mesh[2] = (uint32_t)(uintptr_t)model;
    fxobj[0xc4 / 4] = (uint32_t)(uintptr_t)model; cell[0] = (uint32_t)(uintptr_t)fxobj;
    for (int b = 0; b < 4; b++)
        for (int named = 0; named < 2; named++)
            for (int ptr = 0; ptr < 2; ptr++) {
                static uint8_t stack[0x2000], stk[2][0x2000], init[0x2000];   /* one stack, saved per run */
                rb_t r[2]; char ev[2][1024];
                model[4] = named ? (uint32_t)(uintptr_t)namestruct : 0;   /* "(unnamed)" otherwise */
                for (int k = 0; k < 2; k++) {
                    memset(stack, 0x77, sizeof stack); events[0] = 0;
                    for (int i = 0; i < 7; i++) r[k].in[i] = 0x02020202u * (i + 5);
                    uint8_t *sp = stack + 0x800, *bp = stack + 0x1c00;
                    if (b < 2) r[k].in[1] = (uint32_t)(uintptr_t)mesh;               /* ebx = the mesh */
                    else {
                        sp = stack + 0x1000;
                        r[k].in[5] = (uint32_t)(uintptr_t)cell;                      /* edi */
                        r[k].in[6] = (uint32_t)(uintptr_t)bp;                        /* ebp */
                        *(int *)(bp - 0x10) = 7;                                     /* mesh count */
                    }
                    memcpy(init, stack, sizeof stack);
                    BEGIN_PTR = ptr ? (uint32_t)(uintptr_t)rec_begin : 0;
                    run_block(entry[b] + (k ? OFF : offa), &r[k], sp);
                    BEGIN_PTR = 0;
                    strcpy(ev[k], events);
                    /* return addresses into the two code copies: as exe addresses */
                    uint32_t o = k ? OFF : offa;
                    for (int i = 0; i < 7; i++) r[k].out[i] = norm(r[k].out[i], o);
                    for (unsigned i = 0; i < sizeof stack; i += 4) { uint32_t v; memcpy(&v, stack + i, 4); v = norm(v, o); memcpy(stk[k] + i, &v, 4); }
                }
                int bad;
                if (ptr) bad = memcmp(r[0].out, r[1].out, sizeof r[0].out) || r[0].esp != r[1].esp ||
                               memcmp(stk[0], stk[1], sizeof stk[0]) || strcmp(ev[0], ev[1]);
                else bad = r[0].esp != r[1].esp ||
                           r[1].out[1] != r[1].in[1] || r[1].out[6] != r[1].in[6] || ev[0][0] || ev[1][0] ||
                           memcmp(stk[1], init, sizeof init) ||
                           (b >= 2 && (r[1].out[4] != r[0].out[4] || r[1].out[5] != r[0].out[5]));
                printf("[3] block %06lx, %s, pointer %-4s: %s", (unsigned long)entry[b], named ? "named  " : "unnamed",
                       ptr ? "set" : "null", bad ? "DIFFERS\n" : ptr ? "identical (registers, stack, events)" :
                       "skipped: same esp and kept registers, nothing written\n");
                if (ptr && !bad) {
                    char e[64]; memcpy(e, ev[0] + 15, 63); e[63] = 0;
                    for (char *p = e; *p; p++) if (*p == '\t' || *p == '\n') *p = ' ';
                    printf(", event %.60s\n", e);
                }
                fail |= bad != 0;
            }
    for (int b = 0; b < 4; b++) {                           /* cost per draw without a pointer */
        static uint8_t stack[0x2000]; rb_t r; uint64_t t[2]; const int N = 100000;
        model[4] = (uint32_t)(uintptr_t)namestruct;
        for (int k = 0; k < 2; k++) {
            uint64_t t0 = now_us();
            for (int i = 0; i < N; i++) {
                memset(&r, 0, sizeof r);
                r.in[1] = (uint32_t)(uintptr_t)mesh; r.in[5] = (uint32_t)(uintptr_t)cell;
                r.in[6] = (uint32_t)(uintptr_t)(stack + 0x1c00); *(int *)(stack + 0x1c00 - 0x10) = 7;
                run_block(entry[b] + (k ? OFF : offa), &r, stack + (b < 2 ? 0x800 : 0x1000));
            }
            t[k] = now_us() - t0;
        }
        printf("[3] block %06lx per call: original %.0f ns, patched %.0f ns\n", (unsigned long)entry[b],
               t[0] * 1000.0 / N, t[1] * 1000.0 / N);
    }

    /* [2] */
    gp_pt_sink = sink;
    gp_pt_period_ms = 1000000;                                  /* report only when asked */
    gp_va_offset = OFF;
    ok = gp_patch_passtimers();
    gp_va_offset = 0;
    printf("[2] passtimers installed: %s (Begin %08lx, End %08lx)\n", ok ? "yes" : "NO",
           (unsigned long)BEGIN_PTR, (unsigned long)END_PTR);
    if (!ok) { printf("FAIL\n"); return 1; }
    gp_pt_report(); nrep = 0;                                   /* start a clean window */
    for (int f = 0; f < 10; f++) {
        timer_t_ rv, t, m, ui, sm;
        begin(&sm, "UpdateShadowMap", "Frame");                 /* the scene again, from the light */
        begin(&t, "RenderTerrain", "Frame"); Sleep(1); end(&t);
        for (int k = 0; k < 5; k++) {
            char mesh[64]; snprintf(mesh, sizeof mesh, "Rendering mesh\tDX8Render\tunit_%02d_skn", k);
            begin(&m, mesh, "MeshDX8Render"); busy_us(50); end(&m);
        }
        end(&sm);
        begin(&rv, "RenderViews", "Frame");
        begin(&t, "RenderTerrain", "Frame"); Sleep(3); end(&t);
        for (int k = 0; k < 20; k++) {
            char mesh[64]; snprintf(mesh, sizeof mesh, "Rendering mesh\tDX8Render\tunit_%02d_skn", k);
            begin(&m, mesh, "MeshDX8Render"); busy_us(50); end(&m);
        }
        begin(&t, "RenderWater", "Frame"); Sleep(2); end(&t);
        end(&rv);
        begin(&ui, "RenderUI", "Frame"); Sleep(1); end(&ui);
        HANDLE h = CreateThread(NULL, 0, other_thread, NULL, 0, NULL);  /* not counted */
        WaitForSingleObject(h, INFINITE); CloseHandle(h);
        end(&ui);                                               /* unmatched end: ignored */
    }
    gp_pt_report();
    for (int i = 0; i < nrep; i++) printf("    %s\n", report[i]);
    char all[4096] = "";
    for (int i = 1; i < nrep; i++) strcat(all, report[i]);
    double rv_i = field(all, "RenderViews", 0), rv_s = field(all, "RenderViews", 1), rv_n = field(all, "RenderViews", 2);
    double te = field(all, "RenderTerrain", 0), wa = field(all, "RenderWater", 0), ui = field(all, "RenderUI", 0);
    double me_n = field(all, "Rendering mesh DX8Render", 2), me_i = field(all, "Rendering mesh DX8Render", 0);
    int frames_ok = strstr(report[0], " 10 frames") != NULL;
    int bad = !frames_ok || rv_n != 1 || me_n != 20 || field(all, "RenderUI", 2) != 1 || te < 2.9 || wa < 1.9 ||
              ui < 0.9 || rv_i < te + wa + me_i - 0.01 || rv_s < 0 || rv_s > rv_i || me_i < 0.99 ||
              strstr(all, "unit_") != NULL || field(all, "RenderTerrain", 2) != 1;
    printf("[2] 10 frames counted: %s; RenderViews 1/frame %.2f ms incl, %.2f self; terrain %.2f, water %.2f, "
           "UI %.2f ms; 20 mesh draws/frame in one bucket, %.2f ms: %s\n", frames_ok ? "yes" : "NO", rv_i, rv_s,
           te, wa, ui, me_i, bad ? "WRONG" : "as scripted");
    fail |= bad;
    double sm_i = field(all, "UpdateShadowMap", 0), st_i = field(all, "UpdateShadowMap/RenderTerrain", 0);
    double st_n = field(all, "UpdateShadowMap/RenderTerrain", 2), sme_n = field(all, "UpdateShadowMap/Rendering mesh DX8Render", 2);
    double sme_i = field(all, "UpdateShadowMap/Rendering mesh DX8Render", 0);
    bad = field(all, "UpdateShadowMap", 2) != 1 || st_n != 1 || sme_n != 5 || st_i < 0.9 || sme_i < 0.24 ||
          sm_i < st_i + sme_i - 0.01;
    printf("[2] a second top-level pass (UpdateShadowMap) keeps its nested events apart: terrain %.2f ms (%g), "
           "5 mesh draws %.2f ms (%g), %.2f ms incl: %s\n", st_i, st_n, sme_i, sme_n, sm_i, bad ? "WRONG" : "as scripted");
    fail |= bad;
    printf("%s\n", fail ? "FAIL" : "PASS");
    return fail;
}
