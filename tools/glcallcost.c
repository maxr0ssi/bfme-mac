/* glcallcost - what one OpenGL call costs a 32-bit program under WoW64 Wine (docs/PERFORMANCE.md).
 *
 * Every GL call wined3d makes from its render thread goes 32-bit opengl32.dll -> unix call ->
 * 64-bit opengl32.so -> the host driver. This times a few call shapes in a tight loop, so the
 * per-call transition cost can be separated from the driver's own work:
 *   glGetError        returns a value, no driver work to speak of
 *   glEnable/Disable  void, trivial state change
 *   glUniform4fv      void, pointer argument (the shape of most per-draw constant uploads)
 *   glBufferSubData   void, pointer + data copy (64 bytes)
 *
 *   i686-w64-mingw32-gcc -O2 -o build/glcallcost.exe tools/glcallcost.c -lopengl32 -lgdi32
 *   WINE_BUILD=w10 . ./env.sh && wine build/glcallcost.exe [iterations]
 * Opens a small window for a moment (a GL context needs one).
 */
#include <windows.h>
#include <GL/gl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef char GLchar;
typedef ptrdiff_t GLsizeiptr_, GLintptr_;
typedef void (APIENTRY *PGENBUFFERS)(GLsizei, GLuint *);
typedef void (APIENTRY *PBINDBUFFER)(GLenum, GLuint);
typedef void (APIENTRY *PBUFFERDATA)(GLenum, GLsizeiptr_, const void *, GLenum);
typedef void (APIENTRY *PBUFFERSUBDATA)(GLenum, GLintptr_, GLsizeiptr_, const void *);
typedef void (APIENTRY *PUNIFORM4FV)(GLint, GLsizei, const GLfloat *);

static double now_us(void)
{
    static LARGE_INTEGER f; LARGE_INTEGER c;
    if (!f.QuadPart) QueryPerformanceFrequency(&f);
    QueryPerformanceCounter(&c);
    return c.QuadPart * 1e6 / f.QuadPart;
}

int main(int argc, char **argv)
{
    int n = argc > 1 ? atoi(argv[1]) : 200000, i;
    WNDCLASSA wc = {0};
    wc.lpfnWndProc = DefWindowProcA; wc.hInstance = GetModuleHandleA(NULL); wc.lpszClassName = "glcallcost";
    RegisterClassA(&wc);
    HWND w = CreateWindowA("glcallcost", "glcallcost", WS_OVERLAPPEDWINDOW, 0, 0, 64, 64, 0, 0, wc.hInstance, 0);
    HDC dc = GetDC(w);
    PIXELFORMATDESCRIPTOR pfd = {sizeof pfd, 1, PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER, PFD_TYPE_RGBA, 32};
    SetPixelFormat(dc, ChoosePixelFormat(dc, &pfd), &pfd);
    HGLRC rc = wglCreateContext(dc);
    if (!rc || !wglMakeCurrent(dc, rc)) { fprintf(stderr, "no GL context\n"); return 1; }
    if (!getenv("GLCC_LEGACY")) {   /* wined3d runs on a 4.1 core context; so do we unless asked */
        typedef HGLRC (WINAPI *PCREATECTX)(HDC, HGLRC, const int *);
        PCREATECTX create = (PCREATECTX)wglGetProcAddress("wglCreateContextAttribsARB");
        static const int attribs[] = {0x2091, 4, 0x2092, 1, 0x9126, 1 /* core */, 0x2094, 2 /* forward compatible */, 0};
        HGLRC core = create ? create(dc, NULL, attribs) : NULL;
        if (core && wglMakeCurrent(dc, core)) { wglDeleteContext(rc); rc = core; }
        else fprintf(stderr, "no core context, staying on legacy\n");
    }
    printf("GL_RENDERER %s | GL_VERSION %s | %d iterations\n",
           glGetString(GL_RENDERER), glGetString(GL_VERSION), n);

    PGENBUFFERS genbuffers = (PGENBUFFERS)wglGetProcAddress("glGenBuffers");
    PBINDBUFFER bindbuffer = (PBINDBUFFER)wglGetProcAddress("glBindBuffer");
    PBUFFERDATA bufferdata = (PBUFFERDATA)wglGetProcAddress("glBufferData");
    PBUFFERSUBDATA buffersubdata = (PBUFFERSUBDATA)wglGetProcAddress("glBufferSubData");
    PUNIFORM4FV uniform4fv = (PUNIFORM4FV)wglGetProcAddress("glUniform4fv");
    static float data[64];
    GLuint bo = 0;
    double t;

    for (i = 0; i < 1000; i++) glGetError();   /* warm up translation */

    t = now_us();
    for (i = 0; i < n; i++) glGetError();
    printf("glGetError          %7.3f us/call\n", (now_us() - t) / n);

    t = now_us();
    for (i = 0; i < n; i++) { if (i & 1) glEnable(GL_BLEND); else glDisable(GL_BLEND); }
    printf("glEnable/glDisable  %7.3f us/call\n", (now_us() - t) / n);

    if (uniform4fv) {   /* no program bound: GL_INVAL_OPERATION, but the whole call path still runs */
        t = now_us();
        for (i = 0; i < n; i++) uniform4fv(0, 1, data);
        printf("glUniform4fv        %7.3f us/call\n", (now_us() - t) / n);
        glGetError();
    }
    if (genbuffers && bindbuffer && bufferdata && buffersubdata) {
        typedef void *(APIENTRY *PMAPRANGE)(GLenum, GLintptr_, GLsizeiptr_, GLbitfield);
        typedef GLboolean (APIENTRY *PUNMAP)(GLenum);
        PMAPRANGE maprange = (PMAPRANGE)wglGetProcAddress("glMapBufferRange");
        PUNMAP unmap = (PUNMAP)wglGetProcAddress("glUnmapBuffer");
        static char big[1 << 20];
        static const int sizes[] = {64, 4096, 65536};
        const int size = 1 << 20, m = n / 20;
        unsigned int k;
        genbuffers(1, &bo); bindbuffer(0x8892 /* GL_ARRAY_BUFFER */, bo);
        bufferdata(0x8892, size, NULL, 0x88E0 /* GL_STREAM_DRAW */);
        for (k = 0; k < 3; k++) {
            t = now_us();
            for (i = 0; i < m; i++) buffersubdata(0x8892, (i * sizes[k]) % (size - sizes[k]), sizes[k], big);
            glFinish();
            printf("glBufferSubData %6dB     %8.3f us/call\n", sizes[k], (now_us() - t) / m);
        }
        t = now_us();
        for (i = 0; i < m; i++) bufferdata(0x8892, size, NULL, 0x88E0);
        glFinish();
        printf("glBufferData(NULL) 1MB orphan %8.3f us/call\n", (now_us() - t) / m);
        t = now_us();
        for (i = 0; i < m; i++) { bufferdata(0x8892, size, NULL, 0x88E0); buffersubdata(0x8892, 0, 65536, big); }
        glFinish();
        printf("orphan + SubData 64KB         %8.3f us/pair\n", (now_us() - t) / m);
        if (maprange && unmap) {
            for (k = 0; k < 3; k++) {   /* 0x2|0x20: WRITE|UNSYNCHRONIZED, what wined3d uses for NOOVERWRITE */
                t = now_us();
                for (i = 0; i < m; i++) {
                    char *p = maprange(0x8892, (i * sizes[k]) % (size - sizes[k]), sizes[k], 0x2 | 0x20);
                    if (p) memcpy(p, big, sizes[k]);
                    unmap(0x8892);
                }
                glFinish();
                printf("MapRange+Unmap  %6dB unsync %8.3f us/pair\n", sizes[k], (now_us() - t) / m);
            }
            t = now_us();   /* the whole buffer, as wined3d 10.0 maps it on every lock */
            for (i = 0; i < m / 10; i++) { char *p = maprange(0x8892, 0, size, 0x2 | 0x20); if (p) p[0] = 1; unmap(0x8892); }
            glFinish();
            printf("MapRange+Unmap whole 1MB      %8.3f us/pair\n", (now_us() - t) / (m / 10));
        }
    }
    if (genbuffers && getenv("GLCC_DRAW") != (char *)1) {
        /* The WW3D pattern: append a range, draw from it, append the next, draw... DISCARD at wrap.
         * A draw between uploads leaves the buffer in flight on the GPU, which is what drivers sync on. */
        typedef GLuint (APIENTRY *PCREATESHADER)(GLenum);
        typedef void (APIENTRY *PSHADERSOURCE)(GLuint, GLsizei, const GLchar *const *, const GLint *);
        typedef void (APIENTRY *PUINT)(GLuint);
        typedef GLuint (APIENTRY *PCREATEPROGRAM)(void);
        typedef void (APIENTRY *PATTACH)(GLuint, GLuint);
        typedef void (APIENTRY *PGENVA)(GLsizei, GLuint *);
        typedef void (APIENTRY *PATTRIBPTR)(GLuint, GLint, GLenum, GLboolean, GLsizei, const void *);
        PCREATESHADER createshader = (PCREATESHADER)wglGetProcAddress("glCreateShader");
        PSHADERSOURCE shadersource = (PSHADERSOURCE)wglGetProcAddress("glShaderSource");
        PUINT compile = (PUINT)wglGetProcAddress("glCompileShader"), link = (PUINT)wglGetProcAddress("glLinkProgram");
        PUINT useprogram = (PUINT)wglGetProcAddress("glUseProgram"), bindva = (PUINT)wglGetProcAddress("glBindVertexArray");
        PUINT enableattrib = (PUINT)wglGetProcAddress("glEnableVertexAttribArray");
        PCREATEPROGRAM createprogram = (PCREATEPROGRAM)wglGetProcAddress("glCreateProgram");
        PATTACH attach = (PATTACH)wglGetProcAddress("glAttachShader");
        PGENVA genva = (PGENVA)wglGetProcAddress("glGenVertexArrays");
        PATTRIBPTR attribptr = (PATTRIBPTR)wglGetProcAddress("glVertexAttribPointer");
        typedef void *(APIENTRY *PMAPRANGE_)(GLenum, GLintptr_, GLsizeiptr_, GLbitfield);
        typedef GLboolean (APIENTRY *PUNMAP_)(GLenum);
        PMAPRANGE_ maprange_ = (PMAPRANGE_)wglGetProcAddress("glMapBufferRange");
        PUNMAP_ unmap_ = (PUNMAP_)wglGetProcAddress("glUnmapBuffer");
        static const GLchar *vs = "#version 150\nin vec4 p; void main() { gl_Position = p; gl_PointSize = 1.0; }";
        static const GLchar *fs = "#version 150\nout vec4 c; void main() { c = vec4(1.0); }";
        static char chunk[1 << 20];
        const int vbsize = 5000 * 32, draws = 2000;   /* WW3D: 5000-vertex dynamic VB */
        static const int sizes[] = {256, 2048, 16384};
        GLuint prog = createprogram(), sh, va, vb2;
        unsigned int k, mode;
        sh = createshader(0x8B31); shadersource(sh, 1, &vs, NULL); compile(sh); attach(prog, sh);
        sh = createshader(0x8B30); shadersource(sh, 1, &fs, NULL); compile(sh); attach(prog, sh);
        link(prog); useprogram(prog);
        genva(1, &va); bindva(va);
        genbuffers(1, &vb2); bindbuffer(0x8892, vb2);
        bufferdata(0x8892, vbsize, NULL, 0x88E0);
        enableattrib(0); attribptr(0, 4, GL_FLOAT, GL_FALSE, 32, 0);
        for (mode = 0; mode < 2; mode++) {   /* baselines: no upload at all; one upload per wrap cycle */
            int off = 0;
            t = now_us();
            for (i = 0; i < draws; i++) {
                if (off + 2048 > vbsize) { off = 0; if (mode) buffersubdata(0x8892, 0, vbsize, chunk); }
                glDrawArrays(GL_POINTS, off / 32, 2048 / 32);
                off += 2048;
            }
            glFinish();
            printf("draw only 2048B %s        %8.3f us/draw\n", mode ? "+1 upload/cycle" : "no uploads     ", (now_us() - t) / draws);
        }
        for (k = 0; k < 3; k++) {   /* orphan the whole VB before every upload: fresh storage each time */
            int off = 0;
            t = now_us();
            for (i = 0; i < draws; i++) {
                if (off + sizes[k] > vbsize) off = 0;
                bufferdata(0x8892, vbsize, NULL, 0x88E0);
                buffersubdata(0x8892, off, sizes[k], chunk);
                glDrawArrays(GL_POINTS, off / 32, sizes[k] / 32);
                off += sizes[k];
            }
            glFinish();
            printf("orphan+append+draw %5dB         %8.3f us/draw\n", sizes[k], (now_us() - t) / draws);
        }
        {   /* round robin over a pool of small buffers, each upload into one the GPU is not using */
            static GLuint pool[256];
            genbuffers(256, pool);
            for (i = 0; i < 256; i++) { bindbuffer(0x8892, pool[i]); bufferdata(0x8892, 16384, NULL, 0x88E0); }
            for (k = 0; k < 3; k++) {
                t = now_us();
                for (i = 0; i < draws; i++) {
                    bindbuffer(0x8892, pool[i & 255]);
                    buffersubdata(0x8892, 0, sizes[k], chunk);
                    attribptr(0, 4, GL_FLOAT, GL_FALSE, 32, 0);
                    glDrawArrays(GL_POINTS, 0, sizes[k] / 32);
                }
                glFinish();
                printf("pool of 256 bufs   %5dB         %8.3f us/draw\n", sizes[k], (now_us() - t) / draws);
            }
            bindbuffer(0x8892, vb2); attribptr(0, 4, GL_FLOAT, GL_FALSE, 32, 0);
        }
        if (maprange_ && unmap_ && getenv("GLCC_SPLIT")) {   /* where does a WoW64 map/unmap spend its time? */
            typedef void (APIENTRY *PGETBP)(GLenum, GLenum, GLint *);
            typedef void (APIENTRY *PGETBPTR)(GLenum, GLenum, void **);
            PGETBP getbp = (PGETBP)wglGetProcAddress("glGetBufferParameteriv");
            PGETBPTR getbptr = (PGETBPTR)wglGetProcAddress("glGetBufferPointerv");
            double tm = 0, tu = 0, tq = 0, tp = 0, a;
            GLint v; void *pp;
            for (i = 0; i < draws; i++) {
                char *p;
                int o = getenv("GLCC_ADV") ? (i * 256) % (vbsize - 256) : 0;
                a = now_us(); p = maprange_(0x8892, o, 256, 0x2 | 0x4 | 0x20); tm += now_us() - a;
                if (i < 3 || i == draws - 1) printf("  map off %6d -> %p\n", o, p);
                if (p) memcpy(p, chunk, 256);
                a = now_us(); getbp(0x8892, 0x9120 /* GL_BUFFER_MAP_LENGTH */, &v); tq += now_us() - a;
                a = now_us(); getbptr(0x8892, 0x88BD, &pp); tp += now_us() - a;
                a = now_us(); unmap_(0x8892); tu += now_us() - a;
                if (!getenv("GLCC_NODRAW")) glDrawArrays(GL_POINTS, 0, 8);
            }
            printf("split: map %.3f  getBufferParameteriv %.3f  getBufferPointerv %.3f  unmap %.3f us\n",
                   tm / draws, tq / draws, tp / draws, tu / draws);
        }
        if (maprange_ && unmap_ && sizeof(void *) == 8) {
            /* Replay, natively, what Wine's WoW64 opengl32 does around a map: after mapping it asks for
             * the map pointer, and before unmapping for the pointer, GL_BUFFER_MAP_LENGTH and
             * GL_BUFFER_ACCESS_FLAGS (dlls/opengl32/unix_wgl.c). GLCC_Q selects which queries run. */
            typedef void (APIENTRY *PGETBP)(GLenum, GLenum, GLint *);
            typedef void (APIENTRY *PGETBPTR)(GLenum, GLenum, void **);
            PGETBP getbp = (PGETBP)wglGetProcAddress("glGetBufferParameteriv");
            PGETBPTR getbptr = (PGETBPTR)wglGetProcAddress("glGetBufferPointerv");
            static const char *qs[] = {"none", "pointer", "map_length", "access_flags", "all"};
            unsigned int q;
            for (q = 0; q < 5; q++) {
                int off = 0; double tu = 0, a; GLint v; void *pp;
                t = now_us();
                for (i = 0; i < draws; i++) {
                    char *p;
                    if (off + 2048 > vbsize) off = 0;
                    p = maprange_(0x8892, off, 2048, 0x2 | 0x4 | 0x20);
                    if (p) memcpy(p, chunk, 2048);
                    a = now_us();
                    if (q == 1 || q == 4) getbptr(0x8892, 0x88BD, &pp);
                    if (q == 2 || q == 4) getbp(0x8892, 0x9120, &v);
                    if (q == 3 || q == 4) getbp(0x8892, 0x911F, &v);
                    unmap_(0x8892); tu += now_us() - a;
                    glDrawArrays(GL_POINTS, off / 32, 2048 / 32);
                    off += 2048;
                }
                glFinish();
                printf("native map+draw, queries %-12s %8.3f us/draw (queries+unmap %.2f)\n", qs[q],
                       (now_us() - t) / draws, tu / draws);
            }
        }
        if (maprange_ && unmap_) {   /* append through an unsynchronized range map, as NOOVERWRITE allows */
            for (k = 0; k < 3; k++) {
                int off = 0;
                double tm = 0, tu = 0, td = 0, a;
                t = now_us();
                for (i = 0; i < draws; i++) {
                    char *p;
                    if (off + sizes[k] > vbsize) off = 0;
                    a = now_us();
                    p = maprange_(0x8892, off, sizes[k], 0x2 | 0x4 | 0x20);   /* WRITE|INVALIDATE_RANGE|UNSYNC */
                    tm += now_us() - a;
                    if (p) memcpy(p, chunk, sizes[k]);
                    a = now_us(); unmap_(0x8892); tu += now_us() - a;
                    a = now_us(); glDrawArrays(GL_POINTS, off / 32, sizes[k] / 32); td += now_us() - a;
                    off += sizes[k];
                }
                glFinish();
                printf("unsync map+draw    %5dB         %8.3f us/draw (map %.2f unmap %.2f draw %.2f)\n", sizes[k],
                       (now_us() - t) / draws, tm / draws, tu / draws, td / draws);
            }
        }
        for (mode = 0; mode < 2; mode++)
            for (k = 0; k < 3; k++) {
                int off = 0;
                t = now_us();
                for (i = 0; i < draws; i++) {
                    if (off + sizes[k] > vbsize) {   /* wrap = DISCARD */
                        off = 0;
                        if (mode) bufferdata(0x8892, vbsize, NULL, 0x88E0);
                    }
                    buffersubdata(0x8892, off, sizes[k], chunk);
                    glDrawArrays(GL_POINTS, off / 32, sizes[k] / 32);
                    off += sizes[k];
                }
                glFinish();
                printf("append+draw %5dB %s %8.3f us/draw\n", sizes[k],
                       mode ? "orphan at wrap" : "no orphan     ", (now_us() - t) / draws);
            }
    }
    wglMakeCurrent(NULL, NULL); wglDeleteContext(rc); DestroyWindow(w);
    return 0;
}
