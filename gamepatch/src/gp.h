/* gamepatch: in-memory performance patches for Rise of the Witch-king 2.02 (lotrbfme2ep1.exe,
 * image base 0x400000, PE timestamp 0x460da09e). Loaded as a proxy dinput8.dll before WinMain;
 * the exe on disk is never touched. Every patch is a list of sites; a site is applied only if the
 * bytes in memory are exactly the expected original bytes, and a patch is applied only if all of
 * its sites match (so a different exe version is never written to). */
#ifndef GP_H
#define GP_H
#include <windows.h>
#include <stdint.h>

#define GP_EXE_TIMESTAMP 0x460da09eu
#define GP_EXE_BASE      0x00400000u
/* FNV-1a 64 of original functions that a patch replaces as a whole */
#define GP_FNV_441C56    0x45ae302b63df0439ull   /* invsqrt, 0x52 bytes */
#define GP_FNV_B0DFE0    0xd2aea0afd195ada4ull   /* shape hit test, 0x110 bytes */
#define GP_FNV_B0DEB0    0x2e0540e038412308ull   /* triangle test, 0x130 bytes */
#define GP_FNV_B26100    0x4eef97a630468a0full   /* quaternion -> matrix, 0xcd bytes */

typedef struct {
    uint32_t va;          /* address in the game image */
    uint32_t len;         /* bytes checked and written */
    const uint8_t *orig;  /* expected original bytes (len), or NULL: compare FNV-1a hash */
    uint64_t hash;        /* FNV-1a 64 of the original bytes when orig is NULL (check-only) */
    uint32_t wlen;        /* bytes written from repl (0 = check-only context) */
    uint8_t repl[40];     /* replacement bytes; starts as a copy of orig */
} gp_site;

/* main.c (the tests provide their own) */
void gp_log(const char *fmt, ...);
int  gp_enabled(const char *name);                  /* env GAMEPATCH_<NAME>, then gamepatch.ini */
/* patch.c */
int  gp_apply(const char *name, gp_site *s, int n); /* verify all sites, then write all; 1 = applied */
int  gp_check(const char *name, gp_site *s, int n); /* verify only */
void gp_site_init(gp_site *s, uint32_t va, const uint8_t *orig, uint32_t len); /* len > 40: check-only */
void gp_rel32(gp_site *s, uint32_t off, uint8_t opcode, const void *target); /* E8/E9 at va+off */
void gp_site_hash(gp_site *s, uint32_t va, uint32_t len, uint64_t fnv); /* check-only, by hash */
uint64_t gp_fnv1a(const void *p, uint32_t len);
extern uint32_t gp_va_offset;                       /* 0 in the game; tests relocate */

/* one entry point per patch; each returns 1 when applied */
int gp_patch_dxlock(void);
int gp_patch_invsqrt(void);
int gp_patch_hittest(void);
int gp_patch_shutdown(void);
int gp_patch_limiter(void);
int gp_patch_floor(void);
int gp_patch_quatmat(void);
int gp_highmem(unsigned slack_mb);                 /* diagnostic: fills the low 2 GB (p_highmem.c) */

/* replacement code, exported for the standalone tests (gamepatch/tests) */
DWORD WINAPI gp_dx_wait(HANDLE h, DWORD ms);
BOOL  WINAPI gp_dx_release(HANDLE h);
void  gp_dx_init(void);
void  gp_invsqrt(void);                  /* asm, stdcall float -> st0, replaces 0x441c56 */
extern uint32_t gp_invsqrt_cont;         /* where the x87 fallback continues (orig + 5) */
extern uint32_t gp_invsqrt_fn;           /* what the normtail shims call on their x87 path */
void  gp_norm_4f1710(void);
void  gp_norm_b2b875(void);
int   gp_patch_normtail(void);
extern uint32_t gp_d3d9_handle_va;
extern DWORD gp_limiter_margin;
void  gp_hittest(void);                  /* asm entry, stdcall 4 args, replaces 0xb0dfe0 */
extern uint32_t gp_hittest_cont;         /* orig + 7 */
extern volatile LONG gp_hittest_stats[4];/* calls, bbox rejects, full scans, x87 fallbacks */
int   WINAPI gp_hittest_c(const uint8_t *shape, const float *m, int ix, int iy);
void  gp_quat2mat(void);                 /* asm entry, thiscall 1 arg, replaces 0xb26100 */
extern uint32_t gp_quat2mat_cont;        /* orig + 7 */
extern volatile LONG gp_quat2mat_fallbacks;
int   WINAPI gp_quat2mat_c(float *m, const float *q);
ULONG WINAPI gp_safe_release(IUnknown *p);
extern volatile LONG gp_safe_release_skipped;
DWORD WINAPI gp_limiter_wait(DWORD target_ms, DWORD last);
void  gp_floor(void);                    /* asm, cdecl double -> st0 */
void  gp_ceil(void);
extern uint32_t gp_floor_orig, gp_ceil_orig; /* the CRT's functions, used for NaN */

#endif
