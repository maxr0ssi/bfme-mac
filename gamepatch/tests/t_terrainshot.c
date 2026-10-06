/* terrainshot: before/after pictures of the terrain switches (docs/PERFORMANCE.md §26), made with the
 * game's own tile bake (t_terrain_scene.c) on map mp eastfarthing hills' real terrain. Not a test.
 * usage: terrainshot.exe <lotrbfme2ep1.exe> <scene> <out dir> [x0 y0]  (`make -C gamepatch shots`)
 * Writes, left half before / right half after unless named otherwise:
 *   near_colour_16_vs_32.png       a near tile's colour texture, level 0, 16-bit vs terrain32 (512 + 512)
 *   near_colour_zoom.png           a 96 x 96 corner of it, x4: 16-bit | terrain32
 *   near_mips.png                  levels 1 and 2 (shown x2, x4): now (point) | terrainbox | both
 *   near_light.png                 the normal-map tile lit as terrain.fx does (N.L and the x1200 specular): 16 | 32-bit
 *   far_dxt1_mips.png              a far tile (DXT1 256) levels 0-2: now | terrainbox | both
 *   distance_frames.png            the far tile seen at RTS distance, one frame: now | terrainbox | both
 *   distance_flicker.png           frame-to-frame change over 16 frames of slow camera motion (x8): same order */
#include "t_terrain.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

static char outdir[MAX_PATH];
static void save(const char *name, const uint32_t *rgb, UINT w, UINT h)
{
    char p[MAX_PATH * 2];
    snprintf(p, sizeof p, "%s\\%s", outdir, name);
    printf("%s %s (%ux%u)\n", t_png(p, rgb, w, h) ? "FAILED" : "wrote", p, w, h);
}

/* a sheet of panels side by side (each scaled by an integer factor, nearest), 8 px dark gaps */
typedef struct { const uint32_t *p; UINT w, h, s; } panel;
static void sheet(const char *name, const panel *ps, int n)
{
    UINT W = 0, H = 0;
    for (int i = 0; i < n; i++) { W += ps[i].w * ps[i].s + (i ? 8 : 0); if (ps[i].h * ps[i].s > H) H = ps[i].h * ps[i].s; }
    uint32_t *o = calloc((size_t)W * H, 4);
    for (size_t i = 0; i < (size_t)W * H; i++) o[i] = 0x202020;
    UINT x0 = 0;
    for (int i = 0; i < n; i++) {
        for (UINT y = 0; y < ps[i].h * ps[i].s; y++)
            for (UINT x = 0; x < ps[i].w * ps[i].s; x++) o[y * W + x0 + x] = ps[i].p[(y / ps[i].s) * ps[i].w + x / ps[i].s];
        x0 += ps[i].w * ps[i].s + 8;
    }
    save(name, o, W, H);
    free(o);
}
static uint32_t *crop(const uint32_t *p, UINT w, UINT x0, UINT y0, UINT cw, UINT ch)
{
    uint32_t *o = malloc((size_t)cw * ch * 4);
    for (UINT y = 0; y < ch; y++) memcpy(o + y * cw, p + (y0 + y) * w + x0, cw * 4);
    return o;
}

/* ---- the normal map lit as terrain.fx's ps_2_0 does (the parts the normal map drives) -------- */
static uint32_t *light(const uint32_t *nrm, UINT n, int spec)
{
    uint32_t *o = malloc((size_t)n * n * 4);
    const double L[3] = {0.45, 0.35, 0.82}, V[3] = {0, -0.6, 0.8};
    double H[3] = {L[0] + V[0], L[1] + V[1], L[2] + V[2]}, hl = sqrt(H[0] * H[0] + H[1] * H[1] + H[2] * H[2]);
    for (int i = 0; i < 3; i++) H[i] /= hl;
    for (UINT i = 0; i < n * n; i++) {
        double x = (nrm[i] >> 16 & 255) / 255.0 * 2 - 1, y = (nrm[i] >> 8 & 255) / 255.0 * 2 - 1, z2 = 1 - x * x - y * y;
        double z = z2 > 0 ? sqrt(z2) : 0, d = x * L[0] + y * L[1] + z * L[2];
        double v = spec ? (d > 0 ? pow(fmax(0, x * H[0] + y * H[1] + z * H[2]), 1200.0) * 0.9 : 0) : fmax(0, d);
        int g = (int)(fmin(1, v) * 255 + 0.5);
        o[i] = (uint32_t)(g << 16 | g << 8 | g);
    }
    return o;
}

/* ---- a ground plane at RTS distance, sampled as a GPU does (trilinear, up to 8x anisotropic) --- */
typedef struct { uint32_t *l[3]; UINT w[3]; } chain;
static void bilerp(const chain *c, int L, double u, double v, double *rgb)
{
    UINT w = c->w[L];
    double x = u * w - 0.5, y = v * w - 0.5, fx = x - floor(x), fy = y - floor(y);
    int x0 = (int)floor(x), y0 = (int)floor(y);
    for (int k = 0; k < 3; k++) rgb[k] = 0;
    for (int j = 0; j < 2; j++)
        for (int i = 0; i < 2; i++) {
            uint32_t p = c->l[L][((y0 + j) & (w - 1)) * w + ((x0 + i) & (w - 1))];
            double wt = (i ? fx : 1 - fx) * (j ? fy : 1 - fy);
            for (int k = 0; k < 3; k++) rgb[k] += wt * (p >> (16 - 8 * k) & 255);
        }
}
static void render(const chain *c, double cx, double cy, uint32_t *out, UINT W, UINT Hh)
{
    /* camera 380 units up, pitched 40 degrees below the horizon, 45-degree vertical field; the far
     * tile is 160 world units (16 cells) across, wrapped */
    const double h = 380, pitch = 40 * M_PI / 180, f = 1 / tan(22.5 * M_PI / 180), tile = 160;
    for (UINT y = 0; y < Hh; y++)
        for (UINT x = 0; x < W; x++) {
            double uv[3][2];
            for (int k = 0; k < 3; k++) {
                double sx = ((x + (k == 1)) - W / 2.0) / (Hh / 2.0), sy = ((y + (k == 2)) - Hh / 2.0) / (Hh / 2.0);
                double dy = cos(pitch) * f + sin(pitch) * -sy, dz = -sin(pitch) * f + cos(pitch) * -sy;
                double t = dz < -1e-6 ? -h / dz : 1e6;
                uv[k][0] = (cx + t * sx) / tile; uv[k][1] = (cy + t * dy) / tile;
            }
            double ax = (uv[1][0] - uv[0][0]) * c->w[0], ay = (uv[1][1] - uv[0][1]) * c->w[0];
            double bx = (uv[2][0] - uv[0][0]) * c->w[0], by = (uv[2][1] - uv[0][1]) * c->w[0];
            double la = sqrt(ax * ax + ay * ay), lb = sqrt(bx * bx + by * by), maj = fmax(la, lb), mnr = fmax(fmin(la, lb), 1e-9);
            int N = (int)fmin(8, ceil(maj / mnr));
            double lod = log2(fmax(maj / N, 1e-9)), rgb[3] = {0, 0, 0};
            if (lod < 0) lod = 0;
            if (lod > 2) lod = 2;                  /* the tile textures have 3 levels */
            int L0 = (int)lod, L1 = L0 < 2 ? L0 + 1 : 2;
            double fr = lod - L0, mx = la > lb ? uv[1][0] - uv[0][0] : uv[2][0] - uv[0][0], my = la > lb ? uv[1][1] - uv[0][1] : uv[2][1] - uv[0][1];
            for (int s = 0; s < N; s++) {
                double o = (s + 0.5) / N - 0.5, u = uv[0][0] + o * mx, v = uv[0][1] + o * my, a[3], b[3];
                bilerp(c, L0, u, v, a); bilerp(c, L1, u, v, b);
                for (int k = 0; k < 3; k++) rgb[k] += (a[k] * (1 - fr) + b[k] * fr) / N;
            }
            out[y * W + x] = (uint32_t)((int)(rgb[0] + 0.5) << 16 | (int)(rgb[1] + 0.5) << 8 | (int)(rgb[2] + 0.5));
        }
}

static chain chain_of(gp_fake_tex *t)
{
    chain c;
    for (int l = 0; l < 3; l++) { UINT w; c.l[l] = t_level_rgb(t, l, &w, NULL); c.w[l] = w; }
    return c;
}

int main(int argc, char **argv)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    if (argc < 4) { printf("usage: terrainshot.exe <exe> <scene> <out dir> [x0 y0]\n"); return 2; }
    snprintf(outdir, sizeof outdir, "%s", argv[3]);
    int x0 = argc > 5 ? atoi(argv[4]) : 48, y0 = argc > 5 ? atoi(argv[5]) : 288;
    if (!t_world_init(argv[1])) return 2;
    t_scene s;
    if (t_scene_load(&s, argv[2])) { printf("cannot read %s\n", argv[2]); return 2; }
    void *hm = t_world_build(&s);
    printf("region (%d, %d), 16 x 16 cells\n", x0, y0);

    /* near tiles: 16-bit as now, 32-bit with terrain32; point mips (mipfilter = Wine 10) or box */
    gp_tb_state = -1;                      /* terrainbox off: mipfilter's point levels */
    t_world_set_shadows(hm, 0);
    gp_fake_tex *n16p = t_bake(hm, D3DFMT_A1R5G5B5, x0, y0, 16, 32, 0, NULL);
    gp_fake_tex *nrm16 = t_bake(hm, D3DFMT_A1R5G5B5, x0, y0, 16, 32, 1, NULL);
    gp_fake_tex *f16p = t_bake(hm, D3DFMT_DXT1, x0, y0, 16, 16, 0, NULL);
    gp_tb_state = 1; gp_tb_mode = 1;      /* terrainbox on */
    gp_fake_tex *n16b = t_bake(hm, D3DFMT_A1R5G5B5, x0, y0, 16, 32, 0, NULL);
    gp_fake_tex *f16b = t_bake(hm, D3DFMT_DXT1, x0, y0, 16, 16, 0, NULL);
    t_world_shadows_real(hm, &s);          /* terrain32 on */
    gp_fake_tex *n32b = t_bake(hm, D3DFMT_X8R8G8B8, x0, y0, 16, 32, 0, NULL);
    gp_fake_tex *nrm32 = t_bake(hm, D3DFMT_X8R8G8B8, x0, y0, 16, 32, 1, NULL);
    gp_fake_tex *f32b = t_bake(hm, D3DFMT_DXT1, x0, y0, 16, 16, 0, NULL);

    UINT w;
    uint32_t *a0 = t_level_rgb(n16p, 0, &w, NULL), *b0 = t_level_rgb(n32b, 0, NULL, NULL);
    sheet("near_colour_16_vs_32.png", (panel[]){{a0, w, w, 1}, {b0, w, w, 1}}, 2);
    uint32_t *ca = crop(a0, w, 208, 208, 96, 96), *cb = crop(b0, w, 208, 208, 96, 96);
    sheet("near_colour_zoom.png", (panel[]){{ca, 96, 96, 4}, {cb, 96, 96, 4}}, 2);

    uint32_t *m[3][2];
    gp_fake_tex *mt[3] = {n16p, n16b, n32b};
    for (int i = 0; i < 3; i++) for (int l = 0; l < 2; l++) m[i][l] = t_level_rgb(mt[i], l + 1, NULL, NULL);
    sheet("near_mips_level1.png", (panel[]){{m[0][0], 256, 256, 2}, {m[1][0], 256, 256, 2}, {m[2][0], 256, 256, 2}}, 3);
    sheet("near_mips_level2.png", (panel[]){{m[0][1], 128, 128, 4}, {m[1][1], 128, 128, 4}, {m[2][1], 128, 128, 4}}, 3);

    uint32_t *na = t_level_rgb(nrm16, 0, NULL, NULL), *nb = t_level_rgb(nrm32, 0, NULL, NULL);
    uint32_t *la = light(na, w, 0), *lb = light(nb, w, 0), *sa = light(na, w, 1), *sb = light(nb, w, 1);
    uint32_t *lac = crop(la, w, 128, 128, 192, 192), *lbc = crop(lb, w, 128, 128, 192, 192);
    uint32_t *sac = crop(sa, w, 128, 128, 192, 192), *sbc = crop(sb, w, 128, 128, 192, 192);
    sheet("near_light_diffuse.png", (panel[]){{lac, 192, 192, 2}, {lbc, 192, 192, 2}}, 2);
    sheet("near_light_specular.png", (panel[]){{sac, 192, 192, 2}, {sbc, 192, 192, 2}}, 2);

    gp_fake_tex *ft[3] = {f16p, f16b, f32b};
    for (int l = 0; l < 3; l++) {
        uint32_t *p[3]; UINT fw;
        for (int i = 0; i < 3; i++) p[i] = t_level_rgb(ft[i], l, &fw, NULL);
        char nm[64]; snprintf(nm, sizeof nm, "far_dxt1_level%d.png", l);
        UINT sc = 256 / fw;
        sheet(nm, (panel[]){{p[0], fw, fw, sc}, {p[1], fw, fw, sc}, {p[2], fw, fw, sc}}, 3);
    }

    /* distance: the far tile on a ground plane, 16 frames of slow camera motion */
    enum { W = 480, H = 270, F = 16 };
    for (int pass = 0; pass < 2; pass++) {
        gp_fake_tex *src[3] = {pass ? n16p : f16p, pass ? n16b : f16b, pass ? n32b : f32b};
        uint32_t *frame0[3], *flick[3];
        double mean[3];
        for (int i = 0; i < 3; i++) {
            chain c = chain_of(src[i]);
            uint32_t *prev = malloc(W * H * 4), *cur = malloc(W * H * 4);
            double *acc = calloc(W * H, sizeof *acc), tot = 0;
            for (int t = 0; t < F; t++) {
                render(&c, 3.0 * t / F * 10, 2.0 * t / F * 10, cur, W, H);   /* 3 x 2 world units in 16 frames */
                if (!t) { frame0[i] = malloc(W * H * 4); memcpy(frame0[i], cur, W * H * 4); }
                else for (int k = 0; k < W * H; k++)
                    for (int ch = 0; ch < 24; ch += 8) { double d = abs((int)(cur[k] >> ch & 255) - (int)(prev[k] >> ch & 255)); acc[k] += d / 3; tot += d / 3; }
                uint32_t *sw = prev; prev = cur; cur = sw;
            }
            flick[i] = malloc(W * H * 4);
            for (int k = 0; k < W * H; k++) { int g = (int)fmin(255, acc[k] / (F - 1) * 8); flick[i][k] = (uint32_t)(g << 16 | g << 8 | g); }
            mean[i] = tot / ((double)W * H * (F - 1));
            free(prev); free(cur); free(acc);
        }
        printf("%s tile at distance: mean frame-to-frame change per channel (of 255): now %.2f, terrainbox %.2f, both %.2f\n",
               pass ? "near (512)" : "far (DXT1 256)", mean[0], mean[1], mean[2]);
        sheet(pass ? "distance_near_frame.png" : "distance_far_frame.png", (panel[]){{frame0[0], W, H, 1}, {frame0[1], W, H, 1}, {frame0[2], W, H, 1}}, 3);
        sheet(pass ? "distance_near_flicker.png" : "distance_far_flicker.png", (panel[]){{flick[0], W, H, 1}, {flick[1], W, H, 1}, {flick[2], W, H, 1}}, 3);
    }
    return 0;
}
