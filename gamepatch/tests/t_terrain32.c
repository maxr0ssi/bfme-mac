/* t_terrain32: terrain32 (p_terrain32.c) on the game's own terrain code: the TileData loader's
 * averaging (0x5113b2), the cell fetch and blends (0x4ae772, 0x4ac284, 0x4ad85f, 0x4ac035) and the
 * A1R5G5B5 tile bake (0x4eec82), on a fake WorldHeightMap (t_terrain_scene.c): a synthetic map, and
 * map mp eastfarthing hills' real terrain when build/terrain-preview/eastfarthing.scene (or $T_SCENE)
 * exists.
 *   [0] the patch on a relocated copy of the exe: TileData allocations grow by the shadow, the fill,
 *       tile expansion and bake calls go to terrain32, the near tiles' formats are X8R8G8B8
 *   [1] every TileData's 8-bit shadow (widths 64, 32, 16), put through the game's 5-bit step, is the
 *       16-bit plane the game made: the shadow is the game's box average without that step
 *   [2] with shadows made from the 16-bit pixels (as the game expands them), terrain32's X8R8G8B8
 *       bake truncated back to A1R5G5B5 is byte for byte the game's own bake of the same tiles, colour
 *       and normal map, near (32 px a cell) and far (16) sizes: same layout, cells, blends
 *   [3] a shadow that does not match its 16-bit pixels is not used (the game's expansion runs)
 *   [4] the real 8-bit shadows: how many texels change and by how much, the colours kept, ms per bake
 * usage: t_terrain32.exe <lotrbfme2ep1.exe 2.02> */
#include "t_terrain.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

static int fails;
static void verdict(int bad, const char *fmt, ...)
{
    va_list ap; va_start(ap, fmt); vprintf(fmt, ap); va_end(ap);
    fails += bad != 0;
}
static uint32_t call_target(uint32_t va) { return va + 5 + *(int32_t *)(uintptr_t)(va + 1); }
static uint32_t q16(uint32_t p)
{
    return ((p >> 16 & 255) + 1) * 31 >> 8 << 10 | ((p >> 8 & 255) + 1) * 31 >> 8 << 5 | ((p & 255) + 1) * 31 >> 8;
}
#define TDW(td, w) ((const uint16_t *)((uint8_t *)(td) + ((w) == 64 ? 8 : (w) == 32 ? 0x2008 : 0x2808)))

/* [1] */
static long shadow_check(void *hm, long *n)
{
    long bad = 0;
    void **src = (void **)((uint8_t *)hm + 0xb0);
    for (int i = 0; i < 0x1000; i++)
        for (int c = 0; src[i] && c < 2; c++) {
            void *td = c ? *(void **)((uint8_t *)src[i] + 0x2ab4) : src[i];
            if (!td) continue;
            const uint32_t *l = (const uint32_t *)((uint8_t *)td + 0x2ac0) + 4;
            for (int w = 64; w >= 16; l += w * w, w /= 2)
                for (int k = 0; k < w * w; k++) { bad += q16(l[k]) != (TDW(td, w)[k] & 0x7fffu); (*n)++; }
        }
    return bad;
}

/* [2]: terrain32's bake truncated to A1R5G5B5 against the game's bake, level 0 */
static long compare16(gp_fake_tex *a16, gp_fake_tex *b32)
{
    UINT w, h, pa, pb;
    uint8_t *a = gp_fake_bits(a16, 0, &w, &h, &pa), *b = gp_fake_bits(b32, 0, NULL, NULL, &pb);
    long bad = 0;
    for (UINT y = 0; y < h; y++)
        for (UINT x = 0; x < w; x++) {
            uint32_t v = ((uint32_t *)(b + y * pb))[x];
            uint16_t t = (uint16_t)((v >> 19 & 31) << 10 | (v >> 11 & 31) << 5 | (v >> 3 & 31));
            uint16_t g = ((uint16_t *)(a + y * pa))[x];
            if (t != (g & 0x7fff) && getenv("T_DEBUG") && bad < 6)
                printf("    texel (%u,%u) cell (%u,%u) row-in-cell %u: game %04x, terrain32 %06x -> %04x\n", x, y, x / (w / 16),
                       15 - y / (w / 16), y % (w / 16), g, v & 0xffffff, t);
            bad += t != (g & 0x7fff);   /* (the game's alpha bit: 1 in blended cells only) */
        }
    return bad;
}

static void run_scene(const char *name, const t_scene *s, void *hm, const int (*reg)[2], int nreg)
{
    long n1 = 0, b1 = shadow_check(hm, &n1);
    verdict(b1 != 0 || !n1, "[1] %s: %ld shadow texels (widths 64, 32, 16, colour and normal maps), %ld differ from the game's "
            "16-bit planes after its 5-bit step\n", name, n1, b1);

    /* [2] */
    long bad = 0, texels = 0, cells = 0;
    LONG r0 = gp_t32_stats[1], f0 = gp_t32_stats[5];
    for (int r = 0; r < nreg; r++)
        for (int layer = 0; layer < 2; layer++)
            for (int ppc = 32; ppc >= 16; ppc /= 2) {
                t_world_set_shadows(hm, 0);          /* the game alone */
                gp_fake_tex *a = t_bake(hm, D3DFMT_A1R5G5B5, reg[r][0], reg[r][1], 16, ppc, layer, NULL);
                t_world_shadows_from16(hm);
                gp_fake_tex *b = t_bake(hm, D3DFMT_X8R8G8B8, reg[r][0], reg[r][1], 16, ppc, layer, NULL);
                bad += compare16(a, b); texels += 256L * ppc * ppc; cells += 256;
                gp_fake_free(a); gp_fake_free(b);
            }
    verdict(bad || gp_t32_stats[1] == r0 || gp_t32_stats[5] != f0,
            "[2] %s: %d regions x colour, normal x 32 and 16 px a cell: terrain32's bake with 16-bit-derived shadows, truncated, "
            "%s the game's A1R5G5B5 bake (%ld of %ld texels differ; %ld 8-bit tile reads)\n", name, nreg,
            bad ? "DIFFERS from" : "identical to", bad, texels, (long)(gp_t32_stats[1] - r0));
    (void)cells;

    /* [3] */
    {
        void **src = (void **)((uint8_t *)hm + 0xb0);
        void *td = NULL;
        int x0 = reg[0][0], y0 = reg[0][1];
        int16_t *tile = *(int16_t **)((uint8_t *)hm + 0x98);
        int width = *(int *)((uint8_t *)hm + 0x08);
        td = src[tile[y0 * width + x0] / 4];
        t_world_set_shadows(hm, 0);
        gp_fake_tex *a = t_bake(hm, D3DFMT_A1R5G5B5, x0, y0, 16, 32, 0, NULL);
        t_world_shadows_from16(hm);
        uint32_t *l64 = (uint32_t *)((uint8_t *)td + 0x2ac0) + 4;
        for (int k = 0; k < 64 * 64; k++) l64[k] ^= 0x00404040;   /* wrong data, magic left on */
        LONG m0 = gp_t32_stats[5];
        gp_fake_tex *b = t_bake(hm, D3DFMT_X8R8G8B8, x0, y0, 16, 32, 0, NULL);
        long d = compare16(a, b);
        verdict(d || gp_t32_stats[5] == m0, "[3] %s: a shadow with wrong pixels is refused %ld times and the game's expansion "
                "runs: %s\n", name, (long)(gp_t32_stats[5] - m0), d ? "DIFFERENT" : "identical result");
        gp_fake_free(a); gp_fake_free(b);
    }

    /* [4] */
    {
        t_world_shadows_real(hm, s);
        long changed = 0, tex = 0; double sad = 0, ms16 = 0, ms32 = 0;
        static uint8_t seen16[1 << 15], seen32[1 << 21];  /* 32-bit colours folded to 21 bits */
        memset(seen16, 0, sizeof seen16); memset(seen32, 0, sizeof seen32);
        long c16 = 0, c32 = 0;
        for (int r = 0; r < nreg; r++) {
            double m;
            t_world_set_shadows(hm, 0);
            double best = 1e9;
            for (int k = 0; k < 4; k++) { gp_fake_free(t_bake(hm, D3DFMT_A1R5G5B5, reg[r][0], reg[r][1], 16, 32, 0, &m)); if (m < best) best = m; }
            gp_fake_tex *a = t_bake(hm, D3DFMT_A1R5G5B5, reg[r][0], reg[r][1], 16, 32, 0, &m); ms16 += m < best ? m : best;
            t_world_shadows_real(hm, s);
            best = 1e9;
            for (int k = 0; k < 4; k++) { gp_fake_free(t_bake(hm, D3DFMT_X8R8G8B8, reg[r][0], reg[r][1], 16, 32, 0, &m)); if (m < best) best = m; }
            gp_fake_tex *b = t_bake(hm, D3DFMT_X8R8G8B8, reg[r][0], reg[r][1], 16, 32, 0, &m); ms32 += m < best ? m : best;
            UINT w, h;
            uint32_t *pa = t_level_rgb(a, 0, &w, &h), *pb = t_level_rgb(b, 0, NULL, NULL);
            for (UINT i = 0; i < w * h; i++) {
                tex++;
                uint32_t x = pa[i], y = pb[i];
                for (int c = 0; c < 24; c += 8) sad += abs((int)(x >> c & 255) - (int)(y >> c & 255));
                changed += x != y;
                uint32_t k16 = (x >> 19 & 31) << 10 | (x >> 11 & 31) << 5 | (x >> 3 & 31);
                if (!seen16[k16]) { seen16[k16] = 1; c16++; }
                uint32_t k32 = (y >> 17 & 127) << 14 | (y >> 9 & 127) << 7 | (y >> 1 & 127);
                if (!seen32[k32]) { seen32[k32] = 1; c32++; }
            }
            free(pa); free(pb); gp_fake_free(a); gp_fake_free(b);
        }
        printf("[4] %s, real 8-bit shadows, %d near colour tiles (512x512): %.1f %% of texels change, mean |difference| %.2f "
               "of 255 per channel; distinct colours 16-bit %ld, 32-bit %ld (at 7 bits a channel); bake ms per tile (best of 5, with the mip levels) 16-bit %.2f, "
               "32-bit %.2f\n", name, nreg, 100.0 * changed / tex, sad / (3.0 * tex), c16, c32, ms16 / nreg, ms32 / nreg);
    }
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    uint32_t off = t_world_init(argc > 1 ? argv[1] : orig_default_path());
    if (!off) { printf("the world could not be set up\nFAIL\n"); return 2; }

    /* [0] */
    int ok = *(uint32_t *)(uintptr_t)(0x4ab99f + off + 1) > 0x2ac0 && *(uint32_t *)(uintptr_t)(0x4ab9db + off + 1) > 0x2ac0 &&
             call_target(0x4abbe7 + off) == (uint32_t)(uintptr_t)gp_t32_fill && call_target(0x4abc37 + off) == (uint32_t)(uintptr_t)gp_t32_fill &&
             call_target(0x4ad882 + off) == (uint32_t)(uintptr_t)gp_t32_tile && call_target(0x4ae8ae + off) == (uint32_t)(uintptr_t)gp_t32_tile &&
             call_target(0x4ae44d + off) == (uint32_t)(uintptr_t)gp_t32_bake && *(uint8_t *)(uintptr_t)(0x511fe2 + off) == 0x16 &&
             *(uint8_t *)(uintptr_t)(0x51204f + off) == 0x16 && *(uint8_t *)(uintptr_t)(0x51496a + off) == 0x19 &&
             *(uint8_t *)(uintptr_t)(0x4ae431 + off) == 0xe9;
    verdict(!ok, "[0] terrain32 (with mipfilter, terrainbox): %s (TileData +%u bytes, fill / expansion / bake calls, near "
            "formats X8R8G8B8, format check)\n", ok ? "applied" : "NOT applied", *(uint32_t *)(uintptr_t)(0x4ab99f + off + 1) - 0x2ac0);
    if (!ok) { printf("FAIL\n"); return 1; }

    t_scene syn;
    t_scene_synth(&syn, 0x5eed);
    void *hm = t_world_build(&syn);
    static const int sreg[4][2] = {{0, 0}, {16, 0}, {0, 16}, {32, 32}};
    run_scene("synthetic 64x64", &syn, hm, sreg, 4);

    char path[MAX_PATH];
    if (!GetEnvironmentVariableA("T_SCENE", path, sizeof path)) {
        GetModuleFileNameA(NULL, path, sizeof path);   /* build/gamepatch/x.exe -> build/terrain-preview/ */
        char *e = strrchr(path, '\\'); if (e) *e = 0;
        e = strrchr(path, '\\'); if (e) strcpy(e + 1, "terrain-preview\\eastfarthing.scene");
    }
    t_scene real;
    if (!t_scene_load(&real, path)) {
        void *hr = t_world_build(&real);
        static const int rreg[6][2] = {{48, 288}, {448, 208}, {352, 304}, {384, 288}, {144, 192}, {112, 224}};
        run_scene("eastfarthing hills", &real, hr, rreg, 6);
    } else printf("(no scene file %s: the real-map checks are skipped)\n", path);
    printf(fails ? "FAIL\n" : "PASS\n");
    return fails != 0;
}
