/* fxparamused: a material's FX parameter block recorded without asking d3dx9 again, per parameter,
 * whether the technique uses it.
 *
 * Every W3D mesh of RotWK draws with an FX material (legacy W3D materials become DefaultW3D.fx
 * materials with ~15 parameters: ColorAmbient ... NumTextures, Texture_0/1; 0x5997f0). A material
 * keeps its parameters as a D3DX parameter block, and every change re-records the whole block:
 * 0x551f8f (material, parameter list) deletes the old block (effect vt+0x130), merges the list into
 * the effect's defaults, then BeginParameterBlock (vt+0x124) and, per parameter,
 * GetParameterByName (vt+0x24), IsParameterUsed(param, technique) (vt+0xf8, call at 0x55207f) and
 * the setter, then EndParameterBlock (vt+0x128).
 * The RenderObject particle draw module (0x964c00: particles that are W3D models, ~160 systems:
 * rocks of Earthquake, Avalanche, Balrog, Wyrm, Citadel; light shafts of Rallying Call, Army of the
 * Dead, Balrog; Taint vapour...) sets one colour per particle per pass, by the system's shader
 * (0x965240: 0x50e040 ColorEmissive, 0x50e244 Opacity or 0x50e413 ColorDiffuse), each one such
 * re-record, in the main view and in the shadow-map pass. Wine's d3dx9 IsParameterUsed walks every
 * state of every pass of the technique through its shader inputs and preshaders (is_parameter_used, dlls/d3dx9_36/effect.c): 6-33 us per
 * call on DefaultW3D.fxo's "Default" technique, 0.1-0.3 ms per re-record. The 10-05 session: 37-52 ms
 * per pass in RenderParticles for 1-8 s at a time (frames of 100-130 ms), 41 of 48 stall samples
 * under the module returning to 0x552085 (docs/PERFORMANCE.md §25).
 *
 * The answer depends only on the effect's structure: which parameters the states of the
 * technique's passes reference, fixed when the effect is created (Wine: pass states, their
 * referenced parameters and shader / preshader inputs; no parameter value is read). So the call at
 * 0x55207f goes to a cache keyed by (effect, parameter handle, technique handle); a miss asks the
 * effect as before. Effects are never changed after creation, but a freed effect's address can come
 * back for a new effect: every effect the game creates goes through the two IAT slots of
 * D3DXCreateEffect / D3DXCreateEffectFromFileA (0xbd09f4/8, thunks 0xa3ed20/0xa3ed1a, called from
 * 0x551356/0x5513a3 only; the game never calls CloneEffect on them), whose wrappers clear the cache
 * (a generation count) before creating. The recorded blocks, the material and every other call are
 * the original's. Rendering only: no game logic, LAN-safe.
 * Test: t_spell2fx (every parameter x technique of every effect in Shaders.big, cached against
 * direct; the game's own 0x551f8f in an original and a patched copy on the real DefaultW3D effect,
 * the block, material and texture list compared after every call). */
#include "gp.h"
#include "p_spell2.h"

#define GP_FNV_551F8F 0x37a01112f3437941ull   /* material parameter-block record, 0x231 bytes */

enum { NE = 8192, PROBE = 16 };
typedef struct { void *fx, *p, *t; LONG gen, val; } ent_t;
static ent_t tab[NE];
static volatile LONG lock;
volatile LONG gp_fxu_gen = 1;              /* entries of another generation are empty */
volatile LONG gp_fxu_stats[4];             /* calls, hits, not cached (table full), creations */
uint32_t gp_fxu_create[2];

typedef BOOL (__attribute__((stdcall)) *used_fn)(void *fx, void *p, void *t);

static void take(void) { while (InterlockedExchange(&lock, 1)) YieldProcessor(); }
static void drop(void) { InterlockedExchange(&lock, 0); }
static uint32_t slot(void *fx, void *p, void *t)
{
    uint32_t h = (uint32_t)(uintptr_t)p * 0x9e3779b1u ^ (uint32_t)(uintptr_t)t * 0x85ebca6bu ^ (uint32_t)(uintptr_t)fx;
    return (h ^ h >> 15) * 0x2c1b3c6du >> 19;          /* 13 bits: NE */
}

/* replaces `call [ecx+0xf8]` at 0x55207f: stdcall (effect, parameter, technique), as the original */
BOOL __attribute__((stdcall)) gp_fxu_isused(void *fx, void *p, void *t)
{
    uint32_t h = slot(fx, p, t);
    take();
    LONG g = gp_fxu_gen;
    gp_fxu_stats[0]++;
    for (int i = 0; i < PROBE; i++) {
        ent_t *e = &tab[(h + i) & (NE - 1)];
        if (e->gen != g) break;                        /* empty: not cached */
        if (e->fx == fx && e->p == p && e->t == t) {
            LONG v = e->val;
            gp_fxu_stats[1]++;
            drop();
            return v;
        }
    }
    drop();
    BOOL v = ((used_fn)(*(void ***)fx)[0xf8 / 4])(fx, p, t);
    take();
    if (g == gp_fxu_gen) {                             /* no effect created meanwhile */
        int i = 0;
        for (; i < PROBE; i++) {
            ent_t *e = &tab[(h + i) & (NE - 1)];
            if (e->gen != g) { e->fx = fx; e->p = p; e->t = t; e->val = v; e->gen = g; break; }
            if (e->fx == fx && e->p == p && e->t == t) break;   /* another thread was first */
        }
        if (i == PROBE) gp_fxu_stats[2]++;
    }
    drop();
    return v;
}

/* the IAT wrappers: a new effect may take a freed one's address, so the cache goes first */
__asm__(".text\n"
".globl _gp_fxu_create_mem\n_gp_fxu_create_mem:\n"
"  lock incl _gp_fxu_gen\n  lock incl _gp_fxu_stats+12\n  jmp *_gp_fxu_create\n"
".globl _gp_fxu_create_file\n_gp_fxu_create_file:\n"
"  lock incl _gp_fxu_gen\n  lock incl _gp_fxu_stats+12\n  jmp *_gp_fxu_create+4\n");

int gp_patch_fxparamused(void)
{
    static const uint8_t call[] = {0xff, 0x91, 0xf8, 0x00, 0x00, 0x00};   /* call [ecx+0xf8] */
    gp_site s[2];
    gp_site_hash(&s[0], 0x551f8f, 0x231, GP_FNV_551F8F);
    gp_site_init(&s[1], 0x55207f, call, 6);
    gp_rel32(&s[1], 0, 0xe8, (void *)gp_fxu_isused);
    s[1].repl[5] = 0x90;
    if (!gp_check("fxparamused", s, 2)) return 0;
    /* the cache is only safe if every effect creation clears it: both IAT slots must hold d3dx9_27's
     * own exports (the thunks 0xa3ed20 / 0xa3ed1a jump through them) */
    volatile uint32_t *iat = (volatile uint32_t *)(uintptr_t)GP_FXU_IAT;
    MEMORY_BASIC_INFORMATION mbi;
    if (!VirtualQuery((void *)(uintptr_t)GP_FXU_IAT, &mbi, sizeof mbi) || mbi.State != MEM_COMMIT ||
        (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD))) {
        gp_log("fxparamused: the IAT at %08x is not mapped; patch skipped", GP_FXU_IAT);
        return 0;
    }
    HMODULE x = GetModuleHandleA("d3dx9_27.dll");
    FARPROC c1 = x ? GetProcAddress(x, "D3DXCreateEffect") : NULL;
    FARPROC c2 = x ? GetProcAddress(x, "D3DXCreateEffectFromFileA") : NULL;
    if (!c1 || !c2 || iat[0] != (uint32_t)(uintptr_t)c1 || iat[1] != (uint32_t)(uintptr_t)c2) {
        gp_log("fxparamused: the effect-creation imports are not d3dx9_27's (%08x %08x, d3dx9_27 %p %p); patch skipped",
               iat[0], iat[1], (void *)c1, (void *)c2);
        return 0;
    }
    gp_fxu_create[0] = iat[0];
    gp_fxu_create[1] = iat[1];
    DWORD old;
    if (!VirtualProtect((void *)(uintptr_t)GP_FXU_IAT, 8, PAGE_READWRITE, &old)) {
        gp_log("fxparamused: cannot write the IAT (%lu); patch skipped", GetLastError());
        return 0;
    }
    iat[0] = (uint32_t)(uintptr_t)gp_fxu_create_mem;
    iat[1] = (uint32_t)(uintptr_t)gp_fxu_create_file;
    VirtualProtect((void *)(uintptr_t)GP_FXU_IAT, 8, old, &old);
    if (!gp_apply("fxparamused", s, 2)) {
        VirtualProtect((void *)(uintptr_t)GP_FXU_IAT, 8, PAGE_READWRITE, &old);
        iat[0] = gp_fxu_create[0]; iat[1] = gp_fxu_create[1];
        VirtualProtect((void *)(uintptr_t)GP_FXU_IAT, 8, old, &old);
        return 0;
    }
    gp_log("fxparamused: material parameter blocks ask d3dx9 once per effect, parameter and technique "
           "whether the technique uses the parameter (cleared at every effect creation)");
    return 1;
}

void gp_fxu_exit_log(void)
{
    if (gp_fxu_stats[0])
        gp_log("exit: fxparamused %ld parameter checks, %ld answered from the cache, %ld not cached (table full), "
               "%ld effect creations", gp_fxu_stats[0], gp_fxu_stats[1], gp_fxu_stats[2], gp_fxu_stats[3]);
}
