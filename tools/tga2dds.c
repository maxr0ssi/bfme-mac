/* tga2dds - convert a TGA texture to a DDS with a precomputed mipmap chain.
 *
 * Why: ~60% of the games' texture bytes ship as uncompressed TGA, which carries no
 * mipmaps, so the engine converts the pixels and builds every mip level on the CPU at
 * load time, single-threaded (docs/LOAD-TIME.md). Pre-baking the same pixels into DDS
 * moves that work offline. ".tga" and ".dds" are the same length, so references inside
 * W3D files can be patched in place without changing any offsets.
 *
 *   cc -O2 -o build/tga2dds tools/tga2dds.c
 *   tga2dds <in.tga> <out.dds> [--format dxt1|dxt5|raw|auto] [--no-mips]
 *
 * auto (default): DXT1 when the source is opaque, DXT5 when it has real alpha.
 * raw: A8R8G8B8, pixel-identical to the source, mips only. Bigger files, zero loss.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

typedef struct { int w, h; uint8_t *px; } Image; /* px = BGRA, top-left origin */

static int read_tga(const char *path, Image *out)
{
    FILE *f = fopen(path, "rb");
    if (!f) { fprintf(stderr, "tga2dds: cannot open %s\n", path); return 0; }
    uint8_t h[18];
    if (fread(h, 1, 18, f) != 18) { fclose(f); fprintf(stderr, "tga2dds: short header\n"); return 0; }
    int idlen = h[0], cmap = h[1], type = h[2];
    int w = h[12] | (h[13] << 8), ht = h[14] | (h[15] << 8);
    int bpp = h[16], desc = h[17];
    if (cmap) { fclose(f); fprintf(stderr, "tga2dds: colour-mapped TGA unsupported\n"); return 0; }
    if (type != 2 && type != 10) { fclose(f); fprintf(stderr, "tga2dds: TGA type %d unsupported\n", type); return 0; }
    if (bpp != 24 && bpp != 32) { fclose(f); fprintf(stderr, "tga2dds: %d bpp unsupported\n", bpp); return 0; }
    if (w <= 0 || ht <= 0) { fclose(f); fprintf(stderr, "tga2dds: bad dimensions\n"); return 0; }
    fseek(f, idlen, SEEK_CUR);

    int nch = bpp / 8;
    size_t npx = (size_t)w * ht;
    uint8_t *px = malloc(npx * 4);
    if (!px) { fclose(f); fprintf(stderr, "tga2dds: out of memory\n"); return 0; }

    if (type == 2) {
        uint8_t *row = malloc((size_t)w * nch);
        if (!row) { free(px); fclose(f); return 0; }
        for (int y = 0; y < ht; y++) {
            if (fread(row, nch, w, f) != (size_t)w) { free(row); free(px); fclose(f);
                fprintf(stderr, "tga2dds: truncated pixel data\n"); return 0; }
            uint8_t *dst = px + (size_t)y * w * 4;
            for (int x = 0; x < w; x++) {
                dst[x*4+0] = row[x*nch+0]; dst[x*4+1] = row[x*nch+1];
                dst[x*4+2] = row[x*nch+2]; dst[x*4+3] = (nch == 4) ? row[x*nch+3] : 255;
            }
        }
        free(row);
    } else { /* RLE */
        size_t got = 0;
        while (got < npx) {
            int c = fgetc(f);
            if (c < 0) { free(px); fclose(f); fprintf(stderr, "tga2dds: truncated RLE\n"); return 0; }
            int count = (c & 0x7f) + 1;
            if (got + count > npx) count = (int)(npx - got);
            if (c & 0x80) {
                uint8_t p[4] = {0,0,0,255};
                if (fread(p, 1, nch, f) != (size_t)nch) { free(px); fclose(f); return 0; }
                if (nch == 3) p[3] = 255;
                for (int i = 0; i < count; i++) memcpy(px + (got + i) * 4, p, 4);
            } else {
                for (int i = 0; i < count; i++) {
                    uint8_t p[4] = {0,0,0,255};
                    if (fread(p, 1, nch, f) != (size_t)nch) { free(px); fclose(f); return 0; }
                    if (nch == 3) p[3] = 255;
                    memcpy(px + (got + i) * 4, p, 4);
                }
            }
            got += count;
        }
    }
    fclose(f);

    /* TGA bit 5 of the descriptor set = rows already run top-to-bottom. */
    if (!(desc & 0x20)) {
        uint8_t *tmp = malloc((size_t)w * 4);
        if (tmp) {
            for (int y = 0; y < ht / 2; y++) {
                uint8_t *a = px + (size_t)y * w * 4, *b = px + (size_t)(ht - 1 - y) * w * 4;
                memcpy(tmp, a, (size_t)w * 4); memcpy(a, b, (size_t)w * 4); memcpy(b, tmp, (size_t)w * 4);
            }
            free(tmp);
        }
    }
    out->w = w; out->h = ht; out->px = px;
    return 1;
}

/* Box-filter downsample by 2 (dimensions clamp at 1, so non-square chains work). */
static Image halve(const Image *s)
{
    int w = s->w > 1 ? s->w / 2 : 1, h = s->h > 1 ? s->h / 2 : 1;
    Image d = { w, h, malloc((size_t)w * h * 4) };
    if (!d.px) return d;
    for (int y = 0; y < h; y++) {
        int y0 = (s->h > 1) ? y * 2 : 0, y1 = (s->h > 1) ? y0 + 1 : 0;
        for (int x = 0; x < w; x++) {
            int x0 = (s->w > 1) ? x * 2 : 0, x1 = (s->w > 1) ? x0 + 1 : 0;
            const uint8_t *a = s->px + ((size_t)y0 * s->w + x0) * 4;
            const uint8_t *b = s->px + ((size_t)y0 * s->w + x1) * 4;
            const uint8_t *c = s->px + ((size_t)y1 * s->w + x0) * 4;
            const uint8_t *e = s->px + ((size_t)y1 * s->w + x1) * 4;
            uint8_t *o = d.px + ((size_t)y * w + x) * 4;
            for (int k = 0; k < 4; k++) o[k] = (uint8_t)((a[k] + b[k] + c[k] + e[k] + 2) / 4);
        }
    }
    return d;
}

static void gather_block(const Image *im, int bx, int by, uint8_t blk[64])
{
    for (int y = 0; y < 4; y++) {
        int sy = by + y; if (sy >= im->h) sy = im->h - 1;
        for (int x = 0; x < 4; x++) {
            int sx = bx + x; if (sx >= im->w) sx = im->w - 1;
            memcpy(blk + (y * 4 + x) * 4, im->px + ((size_t)sy * im->w + sx) * 4, 4);
        }
    }
}

static uint16_t pack565(int r, int g, int b)
{ return (uint16_t)(((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)); }

static void unpack565(uint16_t c, int *r, int *g, int *b)
{
    int r5 = (c >> 11) & 31, g6 = (c >> 5) & 63, b5 = c & 31;
    *r = (r5 << 3) | (r5 >> 2); *g = (g6 << 2) | (g6 >> 4); *b = (b5 << 3) | (b5 >> 2);
}

/* Bounding-box colour selection: fast, and good enough for texture art. */
static void encode_colour(const uint8_t blk[64], uint8_t out[8], int allow_alpha_split)
{
    int lo[3] = {255,255,255}, hi[3] = {0,0,0}, transparent = 0;
    for (int i = 0; i < 16; i++) {
        if (allow_alpha_split && blk[i*4+3] < 128) { transparent = 1; continue; }
        for (int k = 0; k < 3; k++) {
            int v = blk[i*4 + (2 - k)]; /* BGRA -> RGB */
            if (v < lo[k]) lo[k] = v;
            if (v > hi[k]) hi[k] = v;
        }
    }
    if (lo[0] > hi[0]) { lo[0]=lo[1]=lo[2]=0; hi[0]=hi[1]=hi[2]=0; }
    uint16_t c0 = pack565(hi[0], hi[1], hi[2]), c1 = pack565(lo[0], lo[1], lo[2]);
    int four = 1;
    if (transparent) { four = 0; if (c0 > c1) { uint16_t t = c0; c0 = c1; c1 = t; } }
    else if (c0 < c1) { uint16_t t = c0; c0 = c1; c1 = t; }
    else if (c0 == c1) four = 0;

    int p[4][3];
    unpack565(c0, &p[0][0], &p[0][1], &p[0][2]);
    unpack565(c1, &p[1][0], &p[1][1], &p[1][2]);
    for (int k = 0; k < 3; k++) {
        if (four) { p[2][k] = (2*p[0][k] + p[1][k]) / 3; p[3][k] = (p[0][k] + 2*p[1][k]) / 3; }
        else      { p[2][k] = (p[0][k] + p[1][k]) / 2;   p[3][k] = 0; }
    }
    uint32_t idx = 0;
    for (int i = 0; i < 16; i++) {
        int best = 0;
        if (allow_alpha_split && blk[i*4+3] < 128 && !four) best = 3;
        else {
            long bd = -1;
            int n = four ? 4 : 3;
            for (int j = 0; j < n; j++) {
                long d = 0;
                for (int k = 0; k < 3; k++) { long e = blk[i*4 + (2 - k)] - p[j][k]; d += e * e; }
                if (bd < 0 || d < bd) { bd = d; best = j; }
            }
        }
        idx |= (uint32_t)best << (i * 2);
    }
    out[0] = c0 & 0xff; out[1] = c0 >> 8; out[2] = c1 & 0xff; out[3] = c1 >> 8;
    for (int i = 0; i < 4; i++) out[4 + i] = (idx >> (i * 8)) & 0xff;
}

static void encode_alpha(const uint8_t blk[64], uint8_t out[8])
{
    int amin = 255, amax = 0;
    for (int i = 0; i < 16; i++) { int a = blk[i*4+3]; if (a < amin) amin = a; if (a > amax) amax = a; }
    out[0] = (uint8_t)amax; out[1] = (uint8_t)amin;
    uint64_t bits = 0;
    for (int i = 0; i < 16; i++) {
        int a = blk[i*4+3], best = 0;
        if (amax == amin) best = 0;
        else {
            long bd = -1;
            for (int j = 0; j < 8; j++) {
                int v = (j == 0) ? amax : (j == 1) ? amin : (amax * (8 - j) + amin * (j - 1)) / 7;
                long d = (long)(a - v) * (a - v);
                if (bd < 0 || d < bd) { bd = d; best = j; }
            }
        }
        bits |= (uint64_t)best << (i * 3);
    }
    for (int i = 0; i < 6; i++) out[2 + i] = (bits >> (i * 8)) & 0xff;
}

static void put32(FILE *f, uint32_t v)
{ uint8_t b[4] = { v & 0xff, (v >> 8) & 0xff, (v >> 16) & 0xff, (v >> 24) & 0xff }; fwrite(b, 1, 4, f); }

enum { FMT_DXT1, FMT_DXT5, FMT_RAW };

int main(int argc, char **argv)
{
    const char *in = NULL, *out = NULL, *fmt = "auto";
    int mips = 1;
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--format") && i + 1 < argc) fmt = argv[++i];
        else if (!strcmp(argv[i], "--no-mips")) mips = 0;
        else if (!in) in = argv[i];
        else if (!out) out = argv[i];
    }
    if (!in || !out) {
        fprintf(stderr, "usage: tga2dds <in.tga> <out.dds> [--format dxt1|dxt5|raw|auto] [--no-mips]\n");
        return 2;
    }
    Image im;
    if (!read_tga(in, &im)) return 1;

    int f;
    if (!strcmp(fmt, "dxt1")) f = FMT_DXT1;
    else if (!strcmp(fmt, "dxt5")) f = FMT_DXT5;
    else if (!strcmp(fmt, "raw")) f = FMT_RAW;
    else {
        int has_alpha = 0;
        for (size_t i = 0; i < (size_t)im.w * im.h; i++) if (im.px[i*4+3] != 255) { has_alpha = 1; break; }
        f = has_alpha ? FMT_DXT5 : FMT_DXT1;
    }
    /* Block formats need multiples of 4; fall back rather than silently distorting. */
    if (f != FMT_RAW && ((im.w % 4) || (im.h % 4))) f = FMT_RAW;

    int levels = 1;
    if (mips) { int w = im.w, h = im.h; while (w > 1 || h > 1) { w = w > 1 ? w/2 : 1; h = h > 1 ? h/2 : 1; levels++; } }

    FILE *o = fopen(out, "wb");
    if (!o) { fprintf(stderr, "tga2dds: cannot write %s\n", out); free(im.px); return 1; }
    int blocksz = (f == FMT_DXT1) ? 8 : 16;
    uint32_t pitch = (f == FMT_RAW) ? (uint32_t)im.w * 4
                   : (uint32_t)((im.w + 3) / 4) * ((im.h + 3) / 4) * blocksz;

    fwrite("DDS ", 1, 4, o);
    put32(o, 124);
    put32(o, 0x1 | 0x2 | 0x4 | 0x1000 | (f == FMT_RAW ? 0x8 : 0x80000) | (levels > 1 ? 0x20000 : 0));
    put32(o, (uint32_t)im.h); put32(o, (uint32_t)im.w);
    put32(o, pitch); put32(o, 0); put32(o, (uint32_t)levels);
    for (int i = 0; i < 11; i++) put32(o, 0);
    put32(o, 32);
    if (f == FMT_RAW) {
        put32(o, 0x41); put32(o, 0); put32(o, 32);
        put32(o, 0x00ff0000); put32(o, 0x0000ff00); put32(o, 0x000000ff); put32(o, 0xff000000);
    } else {
        put32(o, 0x4);
        fwrite(f == FMT_DXT1 ? "DXT1" : "DXT5", 1, 4, o);
        for (int i = 0; i < 5; i++) put32(o, 0);
    }
    put32(o, 0x1000 | (levels > 1 ? (0x8 | 0x400000) : 0));
    put32(o, 0); put32(o, 0); put32(o, 0); put32(o, 0);

    Image cur = im;
    for (int lvl = 0; lvl < levels; lvl++) {
        if (f == FMT_RAW) {
            fwrite(cur.px, 4, (size_t)cur.w * cur.h, o);
        } else {
            uint8_t blk[64], enc[16];
            for (int by = 0; by < cur.h; by += 4)
                for (int bx = 0; bx < cur.w; bx += 4) {
                    gather_block(&cur, bx, by, blk);
                    if (f == FMT_DXT5) { encode_alpha(blk, enc); encode_colour(blk, enc + 8, 0); fwrite(enc, 1, 16, o); }
                    else { encode_colour(blk, enc, 1); fwrite(enc, 1, 8, o); }
                }
        }
        if (lvl + 1 < levels) {
            Image nxt = halve(&cur);
            if (!nxt.px) { fprintf(stderr, "tga2dds: out of memory at level %d\n", lvl); break; }
            if (cur.px != im.px) free(cur.px);
            cur = nxt;
        }
    }
    if (cur.px != im.px) free(cur.px);
    free(im.px);
    fclose(o);
    return 0;
}
