/* laaprobe - does a LARGEADDRESSAWARE (4 GB) 32-bit program work under this Wine, and which part
 * breaks when its pointers are above 2 GB? Standalone; no game needed (docs/MEMORY-4GB.md).
 *
 *   laaprobe.exe [--fill-low] [--slack MB] [--mb N] [--hold S] test...
 *
 *   info     LAA flag of this exe, GetSystemInfo / GlobalMemoryStatusEx limits
 *   space    reserve 16 MB, then 64 KB blocks bottom-up until nothing is left; highest end, bytes
 *            above 2 GB, one committed page written and read back in every block
 *   topdown  MEM_TOP_DOWN reservation (lands just under 4 GB), a 64 MB heap block, msvcrt malloc
 *   thread   a thread whose stack is above 2 GB (after --fill-low): access violations caught by a
 *            vectored handler, by an fs:[0] SEH frame and by one that RtlUnwind()s (what the game's
 *            __except blocks do), 20000 window-message callbacks, file I/O into high buffers
 *   d3d9     window + HAL device; MANAGED / SYSTEMMEM / DYNAMIC textures and vertex buffers whose
 *            locks return pointers above 2 GB, drawn and read back pixel by pixel; --mb N of
 *            MANAGED 512x512 textures on top (the art mod's case: more texture memory)
 *   dlls     load the system DLLs the games load (d3dx9_27, dsound, dinput8, gdiplus, ...) and use
 *            d3dx9 and dsound with their buffers above 2 GB
 *   all      every test above, in that order
 *
 *   --fill-low  first reserve every free block below 0x80000000, so everything allocated
 *               afterwards (heaps, stacks, Wine's own and the driver's memory) must come from above
 *               2 GB: the state of a game that has used its first 2 GB
 *   --slack MB  leave that much of the low 2 GB free (default 0)
 *
 * Each check prints "ok <name>" or "FAIL <name>: ..."; the exit code is the failure count.
 * Build (the LAA flag is the point):  i686-w64-mingw32-gcc -O2 -Wl,--large-address-aware
 *     -o build/laaprobe.exe tools/laaprobe.c -ld3d9 -lgdi32
 * Run:   scripts/laa-probe.sh [args]   (throwaway prefix, never beside a running game)
 */
#define COBJMACROS
#include <windows.h>
#include <d3d9.h>
#include <mmsystem.h>
#include <dsound.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define HIGH(p) ((ULONG_PTR)(p) >= 0x80000000u)
static int failures;
static SIZE_T low_filled;

static void check(int ok, const char *name, const char *fmt, ...)
{
    va_list a;
    if (ok) { printf("ok   %s\n", name); fflush(stdout); return; }
    failures++;
    printf("FAIL %s: ", name);
    va_start(a, fmt); vprintf(fmt, a); va_end(a);
    printf("\n"); fflush(stdout);
}

/* ---- address space ---------------------------------------------------------------------------- */

/* The process heap keeps free space inside segments it reserved below 2 GB before fill_low ran
   (d3d9's and dsound's lock memory came from there). Use it up, largest blocks first, until each
   size comes back from above 2 GB; the blocks are kept, like the reservations. */
static void fill_heap(void)
{
    static const SIZE_T sizes[] = { 1 << 20, 64 << 10, 4 << 10, 256, 16 };
    HANDLE h = GetProcessHeap(); SIZE_T used = 0; int i, k;
    for (i = 0; i < (int)(sizeof(sizes) / sizeof(*sizes)); i++)
        for (k = 0; k < 200000; k++)
        {
            void *p = HeapAlloc(h, 0, sizes[i]);
            if (!p) break;
            if (HIGH(p)) { HeapFree(h, 0, p); break; }
            used += sizes[i];
        }
    printf("fill-low: used %lu KB of the process heap's low free space\n", (unsigned long)(used >> 10));
}

static void fill_low(SIZE_T slack)
{
    MEMORY_BASIC_INFORMATION mbi; char *p = (char *)0x10000; void *last[64]; int n = 0;
    while ((ULONG_PTR)p < 0x80000000u && VirtualQuery(p, &mbi, sizeof(mbi)))
    {
        char *next = (char *)mbi.BaseAddress + mbi.RegionSize;
        if (mbi.State == MEM_FREE)
        {
            ULONG_PTR b = ((ULONG_PTR)mbi.BaseAddress + 0xffff) & ~0xffffu;
            ULONG_PTR e = min((ULONG_PTR)next, 0x80000000u) & ~0xffffu;
            if (e > b && VirtualAlloc((void *)b, e - b, MEM_RESERVE, PAGE_NOACCESS))
            {
                low_filled += e - b;
                last[n++ % 64] = (void *)b;
            }
        }
        if (next <= p) break;
        p = next;
    }
    /* give back the most recent reservations until `slack` is free */
    while (slack && n > 0)
    {
        void *b = last[--n % 64];
        VirtualQuery(b, &mbi, sizeof(mbi));
        VirtualFree(b, 0, MEM_RELEASE);
        low_filled -= mbi.RegionSize;
        slack = mbi.RegionSize >= slack ? 0 : slack - mbi.RegionSize;
    }
    printf("fill-low: reserved %lu MB below 2 GB\n", (unsigned long)(low_filled >> 20));
    fill_heap();
}

static void test_info(void)
{
    IMAGE_DOS_HEADER *dos = (IMAGE_DOS_HEADER *)GetModuleHandleA(NULL);
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)((char *)dos + dos->e_lfanew);
    SYSTEM_INFO si; MEMORYSTATUSEX ms = { sizeof(ms) };
    GetSystemInfo(&si); GlobalMemoryStatusEx(&ms);
    printf("exe LAA flag: %s\n", nt->FileHeader.Characteristics & IMAGE_FILE_LARGE_ADDRESS_AWARE ? "on" : "off");
    printf("MaximumApplicationAddress %p, TotalVirtual %llu MB, AvailVirtual %llu MB\n",
           si.lpMaximumApplicationAddress, ms.ullTotalVirtual >> 20, ms.ullAvailVirtual >> 20);
    check((ULONG_PTR)si.lpMaximumApplicationAddress > 0xf0000000u, "info-4gb-limit",
          "MaximumApplicationAddress %p (LAA not honoured)", si.lpMaximumApplicationAddress);
}

static void test_space(void)
{
    static void *blocks[70000]; int n = 0, bad = 0, i; ULONG_PTR top = 0; unsigned long long total = 0, high = 0;
    SIZE_T sizes[2] = { 16 << 20, 64 << 10 };
    for (i = 0; i < 2; i++)
        for (;;)
        {
            char *p = n < 70000 ? VirtualAlloc(NULL, sizes[i], MEM_RESERVE, PAGE_NOACCESS) : NULL;
            if (!p) break;
            blocks[n++] = p; total += sizes[i];
            if (HIGH(p)) high += sizes[i];
            if ((ULONG_PTR)p + sizes[i] > top) top = (ULONG_PTR)p + sizes[i];
            if (!VirtualAlloc(p, 4096, MEM_COMMIT, PAGE_READWRITE)) { bad++; continue; }
            *(volatile DWORD *)p = (DWORD)(ULONG_PTR)p;
            if (*(volatile DWORD *)p != (DWORD)(ULONG_PTR)p) bad++;
        }
    printf("space: reserved %llu MB in %d blocks, %llu MB above 2 GB, highest end %#lx\n",
           (total + low_filled) >> 20, n, high >> 20, (unsigned long)top);
    check(high > (1ull << 30), "space-above-2gb", "only %llu MB above 2 GB", high >> 20);
    check(!bad, "space-commit-rw", "%d blocks failed commit/write/read", bad);
    while (n) VirtualFree(blocks[--n], 0, MEM_RELEASE);
}

static void test_topdown(void)
{
    char *p = VirtualAlloc(NULL, 1 << 20, MEM_RESERVE | MEM_COMMIT | MEM_TOP_DOWN, PAGE_READWRITE);
    char *h, *m; HANDLE heap;
    printf("topdown: MEM_TOP_DOWN 1 MB at %p\n", p);
    check(p && HIGH(p), "topdown-high", "got %p", p);
    if (p) { memset(p, 0x5a, 1 << 20); check(p[(1 << 20) - 1] == 0x5a, "topdown-rw", "readback"); VirtualFree(p, 0, MEM_RELEASE); }
    heap = HeapCreate(0, 0, 0);
    h = HeapAlloc(heap, 0, 64 << 20);
    m = malloc(8 << 20);
    printf("topdown: 64 MB HeapAlloc %p, 8 MB malloc %p\n", h, m);
    check(h && m, "topdown-heap", "allocation failed");
    if (h && m) { memset(h, 1, 64 << 20); memcpy(m, h + (56 << 20), 8 << 20); check(m[(8 << 20) - 1] == 1, "topdown-memcpy", "readback"); }
    free(m); HeapDestroy(heap);
}

/* ---- exceptions, callbacks and syscalls on a stack above 2 GB ---------------------------------- */

static volatile LONG veh_hits, seh_hits, unwind_hits, veh_on;

/* `movl 0x10, %ecx` = 8b 0d 10 00 00 00: every fault below is that instruction. */
static LONG CALLBACK veh(EXCEPTION_POINTERS *ep)
{
    BYTE *ip = (BYTE *)ep->ContextRecord->Eip;
    if (ep->ExceptionRecord->ExceptionCode != EXCEPTION_ACCESS_VIOLATION || ip[0] != 0x8b || ip[1] != 0x0d
            || *(DWORD *)(ip + 2) != 0x10 || ep->ExceptionRecord->ExceptionInformation[1] != 0x10)
        return EXCEPTION_CONTINUE_SEARCH;
    if (!veh_on) return EXCEPTION_CONTINUE_SEARCH;   /* off while the fs:[0] frames are tested */
    ep->ContextRecord->Eip += 6; ep->ContextRecord->Ecx = 1;
    InterlockedIncrement(&veh_hits);
    return EXCEPTION_CONTINUE_EXECUTION;
}

static EXCEPTION_DISPOSITION __cdecl seh_handler(EXCEPTION_RECORD *rec, void *frame, CONTEXT *ctx, void *disp)
{
    (void)disp;
    if (rec->ExceptionFlags & (EXCEPTION_UNWINDING | EXCEPTION_EXIT_UNWIND)) return ExceptionContinueSearch;
    if (rec->ExceptionCode != EXCEPTION_ACCESS_VIOLATION) return ExceptionContinueSearch;
    if (!HIGH(frame)) printf("  (seh frame %p is not above 2 GB)\n", frame);
    ctx->Eip += 6; ctx->Ecx = 1;
    InterlockedIncrement(&seh_hits);
    return ExceptionContinueExecution;
}

static EXCEPTION_DISPOSITION __cdecl unwind_handler(EXCEPTION_RECORD *rec, void *frame, CONTEXT *ctx, void *disp)
{
    (void)disp;
    if (rec->ExceptionFlags & (EXCEPTION_UNWINDING | EXCEPTION_EXIT_UNWIND)) return ExceptionContinueSearch;
    if (rec->ExceptionCode != EXCEPTION_ACCESS_VIOLATION) return ExceptionContinueSearch;
    RtlUnwind(frame, NULL, rec, NULL);   /* unwinds nothing above us, but walks the chain like _global_unwind2 */
    ctx->Eip += 6; ctx->Ecx = 1;
    InterlockedIncrement(&unwind_hits);
    return ExceptionContinueExecution;
}

/* Registers `handler` as an fs:[0] frame on the current stack, faults once, unregisters. */
static int seh_fault(void *handler)
{
    int r;
    __asm__ volatile(
        "pushl %1\n\t"
        "pushl %%fs:0\n\t"
        "movl %%esp, %%fs:0\n\t"
        "xorl %%ecx, %%ecx\n\t"
        ".byte 0x8b, 0x0d, 0x10, 0, 0, 0\n\t"   /* movl 0x10, %ecx */
        "movl %%ecx, %0\n\t"
        "movl (%%esp), %%edx\n\t"
        "movl %%edx, %%fs:0\n\t"
        "addl $8, %%esp\n\t"
        : "=r"(r) : "r"(handler) : "ecx", "edx", "memory");
    return r;
}

static int veh_fault(void)
{
    int r;
    __asm__ volatile("xorl %%ecx, %%ecx\n\t.byte 0x8b, 0x0d, 0x10, 0, 0, 0\n\tmovl %%ecx, %0" : "=r"(r) : : "ecx", "memory");
    return r;
}

static LRESULT CALLBACK probe_wndproc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp)
{
    if (msg == WM_USER) { volatile char buf[256]; buf[0] = (char)wp; return (LRESULT)(ULONG_PTR)buf + buf[0] * 0; }
    return DefWindowProcA(hwnd, msg, wp, lp);
}

static DWORD WINAPI high_thread(void *arg)
{
    int i, ok; char local; char *io; HWND hwnd; WNDCLASSA wc = { 0 }; char path[MAX_PATH]; HANDLE f; DWORD done;
    unsigned calls = 0, high_stacks = 0;
    (void)arg;
    printf("thread: stack at %p\n", &local);
    check(!low_filled || HIGH(&local), "thread-stack-high", "stack %p (fill-low did not push it up)", &local);

    veh_on = 1;
    for (i = 0, ok = 1; i < 2000; i++) ok &= veh_fault() == 1;
    check(ok && veh_hits == 2000, "thread-veh", "%ld of 2000 faults handled", veh_hits);
    veh_on = 0;
    for (i = 0, ok = 1; i < 2000; i++) ok &= seh_fault(seh_handler) == 1;
    check(ok && seh_hits == 2000, "thread-seh-frame", "%ld of 2000 faults handled", seh_hits);
    for (i = 0, ok = 1; i < 2000; i++) ok &= seh_fault(unwind_handler) == 1;
    check(ok && unwind_hits == 2000, "thread-seh-rtlunwind", "%ld of 2000 faults handled", unwind_hits);

    wc.lpfnWndProc = probe_wndproc; wc.hInstance = GetModuleHandleA(NULL); wc.lpszClassName = "laaprobe_msg";
    RegisterClassA(&wc);
    hwnd = CreateWindowA("laaprobe_msg", "laaprobe", WS_OVERLAPPEDWINDOW, 0, 0, 64, 64, NULL, NULL, wc.hInstance, NULL);
    for (i = 0; i < 20000 && hwnd; i++)
    {
        LRESULT r = SendMessageA(hwnd, WM_USER, 0, 0);
        calls++;
        if (HIGH(r)) high_stacks++;
    }
    check(hwnd && calls == 20000 && (!low_filled || high_stacks == calls), "thread-callbacks",
          "window %p, %u callbacks, %u with the callback stack above 2 GB", hwnd, calls, high_stacks);
    if (hwnd) DestroyWindow(hwnd);
    /* one more fault after the callbacks: the pattern of the Wine 11 WoW64 bug (patches/WINE-BUG-REPORT.md) */
    ok = seh_fault(unwind_handler) == 1;
    veh_on = 1; ok &= veh_fault() == 1; veh_on = 0;
    check(ok, "thread-fault-after-callbacks", "not handled");

    io = VirtualAlloc(NULL, 1 << 20, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    GetTempPathA(sizeof(path), path); strcat(path, "laaprobe.tmp");
    f = CreateFileA(path, GENERIC_READ | GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, FILE_FLAG_DELETE_ON_CLOSE, NULL);
    for (i = 0; io && i < (1 << 20); i++) io[i] = (char)(i * 7);
    ok = io && f != INVALID_HANDLE_VALUE && WriteFile(f, io, 1 << 20, &done, NULL) && done == 1 << 20;
    if (ok) { memset(io, 0, 1 << 20); SetFilePointer(f, 0, NULL, FILE_BEGIN); ok = ReadFile(f, io, 1 << 20, &done, NULL) && done == 1 << 20; }
    for (i = 0; ok && i < (1 << 20); i++) ok = io[i] == (char)(i * 7);
    check(ok, "thread-file-io", "1 MB write/read through buffer %p failed", io);
    CloseHandle(f);
    return 0;
}

static void test_thread(void)
{
    HANDLE t;
    void *v = AddVectoredExceptionHandler(1, veh);
    t = CreateThread(NULL, 1 << 20, high_thread, NULL, 0, NULL);
    check(t != NULL, "thread-create", "CreateThread failed (%lu)", GetLastError());
    if (t) { WaitForSingleObject(t, 120000); CloseHandle(t); }
    RemoveVectoredExceptionHandler(v);
}

/* ---- Direct3D 9 --------------------------------------------------------------------------------- */

#define W 256
#define H 256
typedef struct { float x, y, z, rhw; DWORD c; float u, v; } Vtx;
#define FVF (D3DFVF_XYZRHW | D3DFVF_DIFFUSE | D3DFVF_TEX1)
static IDirect3DDevice9 *dev;
static float uv_max = 1.0f;   /* 64 / texture size: draws the texture's top-left 64x64 texels 1:1 */

static DWORD pattern(int tex, int x, int y) { return 0xff000000u | ((tex * 37 + x * 5) & 0xff) << 16 | ((y * 3 + tex) & 0xff) << 8 | ((x ^ y) & 0xff); }

static int fill_texture(IDirect3DTexture9 *t, int id, int size, DWORD lock_flags, void **ptr)
{
    D3DLOCKED_RECT lr; int x, y;
    if (FAILED(IDirect3DTexture9_LockRect(t, 0, &lr, NULL, lock_flags))) return 0;
    *ptr = lr.pBits;
    for (y = 0; y < size; y++) for (x = 0; x < size; x++) ((DWORD *)((BYTE *)lr.pBits + y * lr.Pitch))[x] = pattern(id, x, y);
    IDirect3DTexture9_UnlockRect(t, 0);
    return 1;
}

/* Draws the texture (or untextured, coloured vertices from vb) 1:1 over the 64x64 top-left and
 * returns the number of wrong pixels. */
static int draw_and_compare(IDirect3DBaseTexture9 *tex, IDirect3DVertexBuffer9 *vb, int id, IDirect3DSurface9 *rb)
{
    IDirect3DSurface9 *bb; D3DLOCKED_RECT lr; int x, y, bad = 0;
    Vtx q[4] = { { -0.5f, -0.5f, 0, 1, 0, 0, 0 }, { 63.5f, -0.5f, 0, 1, 0, uv_max, 0 }, { -0.5f, 63.5f, 0, 1, 0, 0, uv_max }, { 63.5f, 63.5f, 0, 1, 0, uv_max, uv_max } };
    IDirect3DDevice9_Clear(dev, 0, NULL, D3DCLEAR_TARGET, 0xff000000, 1.0f, 0);
    IDirect3DDevice9_BeginScene(dev);
    IDirect3DDevice9_SetTexture(dev, 0, tex);
    IDirect3DDevice9_SetTextureStageState(dev, 0, D3DTSS_COLOROP, tex ? D3DTOP_SELECTARG1 : D3DTOP_SELECTARG2);
    if (vb) { IDirect3DDevice9_SetStreamSource(dev, 0, vb, 0, sizeof(Vtx)); IDirect3DDevice9_DrawPrimitive(dev, D3DPT_TRIANGLESTRIP, 0, 2); }
    else IDirect3DDevice9_DrawPrimitiveUP(dev, D3DPT_TRIANGLESTRIP, 2, q, sizeof(Vtx));
    IDirect3DDevice9_EndScene(dev);
    IDirect3DDevice9_GetBackBuffer(dev, 0, 0, D3DBACKBUFFER_TYPE_MONO, &bb);
    IDirect3DDevice9_GetRenderTargetData(dev, bb, rb);
    IDirect3DSurface9_Release(bb);
    if (FAILED(IDirect3DSurface9_LockRect(rb, &lr, NULL, D3DLOCK_READONLY))) return 64 * 64;
    for (y = 0; y < 64; y++)
        for (x = 0; x < 64; x++)
        {
            DWORD got = ((DWORD *)((BYTE *)lr.pBits + y * lr.Pitch))[x] & 0xffffff;
            DWORD want = (vb ? 0xff000000u | (id * 0x10101u) : pattern(id, x, y)) & 0xffffff;
            bad += got != want;
        }
    IDirect3DSurface9_UnlockRect(rb);
    IDirect3DDevice9_Present(dev, NULL, NULL, NULL, NULL);
    return bad;
}

static void test_d3d9(int extra_mb)
{
    IDirect3D9 *d3d; D3DPRESENT_PARAMETERS pp = { 0 }; HWND hwnd; WNDCLASSA wc = { 0 }; HRESULT hr;
    IDirect3DSurface9 *rb; IDirect3DTexture9 *t[3], *def, **big = NULL; IDirect3DVertexBuffer9 *vb[2];
    const char *pool_name[3] = { "d3d9-managed-texture", "d3d9-systemmem-texture", "d3d9-dynamic-texture" };
    void *ptr = NULL; int i, j, bad, nbig = 0, highbig = 0, badbig = 0;

    wc.lpfnWndProc = DefWindowProcA; wc.hInstance = GetModuleHandleA(NULL); wc.lpszClassName = "laaprobe_d3d";
    RegisterClassA(&wc);
    hwnd = CreateWindowA("laaprobe_d3d", "laaprobe", WS_OVERLAPPEDWINDOW | WS_VISIBLE, 40, 40, W, H, NULL, NULL, wc.hInstance, NULL);
    d3d = Direct3DCreate9(D3D_SDK_VERSION);
    pp.Windowed = TRUE; pp.SwapEffect = D3DSWAPEFFECT_DISCARD; pp.BackBufferWidth = W; pp.BackBufferHeight = H;
    pp.BackBufferFormat = D3DFMT_X8R8G8B8; pp.hDeviceWindow = hwnd;
    hr = d3d ? IDirect3D9_CreateDevice(d3d, D3DADAPTER_DEFAULT, D3DDEVTYPE_HAL, hwnd, D3DCREATE_HARDWARE_VERTEXPROCESSING, &pp, &dev) : E_FAIL;
    check(SUCCEEDED(hr), "d3d9-device", "CreateDevice hr=%#lx", (unsigned long)hr);
    if (FAILED(hr)) return;
    IDirect3DDevice9_CreateOffscreenPlainSurface(dev, W, H, D3DFMT_X8R8G8B8, D3DPOOL_SYSTEMMEM, &rb, NULL);
    IDirect3DDevice9_SetFVF(dev, FVF);
    IDirect3DDevice9_SetRenderState(dev, D3DRS_LIGHTING, FALSE);
    IDirect3DDevice9_SetTextureStageState(dev, 0, D3DTSS_COLORARG1, D3DTA_TEXTURE);
    IDirect3DDevice9_SetTextureStageState(dev, 0, D3DTSS_COLORARG2, D3DTA_DIFFUSE);
    IDirect3DDevice9_SetSamplerState(dev, 0, D3DSAMP_MINFILTER, D3DTEXF_POINT);
    IDirect3DDevice9_SetSamplerState(dev, 0, D3DSAMP_MAGFILTER, D3DTEXF_POINT);

    IDirect3DDevice9_CreateTexture(dev, 64, 64, 1, 0, D3DFMT_A8R8G8B8, D3DPOOL_MANAGED, &t[0], NULL);
    IDirect3DDevice9_CreateTexture(dev, 64, 64, 1, 0, D3DFMT_A8R8G8B8, D3DPOOL_SYSTEMMEM, &t[1], NULL);
    IDirect3DDevice9_CreateTexture(dev, 64, 64, 1, D3DUSAGE_DYNAMIC, D3DFMT_A8R8G8B8, D3DPOOL_DEFAULT, &t[2], NULL);
    IDirect3DDevice9_CreateTexture(dev, 64, 64, 1, 0, D3DFMT_A8R8G8B8, D3DPOOL_DEFAULT, &def, NULL);
    for (i = 0; i < 3; i++)
    {
        int ok = t[i] && fill_texture(t[i], i + 1, 64, i == 2 ? D3DLOCK_DISCARD : 0, &ptr);
        printf("%s: lock pointer %p\n", pool_name[i], ok ? ptr : NULL);
        if (ok && i == 1) IDirect3DDevice9_UpdateTexture(dev, (IDirect3DBaseTexture9 *)t[1], (IDirect3DBaseTexture9 *)def);
        bad = ok ? draw_and_compare((IDirect3DBaseTexture9 *)(i == 1 ? def : t[i]), NULL, i + 1, rb) : -1;
        check(bad == 0 && (!low_filled || HIGH(ptr)), pool_name[i], "%d wrong pixels, lock pointer %p", bad, ptr);
    }

    /* MANAGED and DYNAMIC (DISCARD, then NOOVERWRITE) vertex buffers */
    IDirect3DDevice9_CreateVertexBuffer(dev, 64 * sizeof(Vtx), D3DUSAGE_WRITEONLY, FVF, D3DPOOL_MANAGED, &vb[0], NULL);
    IDirect3DDevice9_CreateVertexBuffer(dev, 64 * sizeof(Vtx), D3DUSAGE_DYNAMIC | D3DUSAGE_WRITEONLY, FVF, D3DPOOL_DEFAULT, &vb[1], NULL);
    for (i = 0; i < 2; i++)
        for (j = 0; j < 8; j++)
        {
            Vtx *v; DWORD c = 0xff000000u | ((i * 8 + j + 1) * 0x10101u);
            UINT off = i ? j * 4 * sizeof(Vtx) : 0;
            char name[64];
            Vtx q[4] = { { -0.5f, -0.5f, 0, 1, c, 0, 0 }, { 63.5f, -0.5f, 0, 1, c, 0, 0 }, { -0.5f, 63.5f, 0, 1, c, 0, 0 }, { 63.5f, 63.5f, 0, 1, c, 0, 0 } };
            if (!vb[i] || FAILED(IDirect3DVertexBuffer9_Lock(vb[i], off, 4 * sizeof(Vtx), (void **)&v,
                    i ? (j ? D3DLOCK_NOOVERWRITE : D3DLOCK_DISCARD) : 0))) { check(0, "d3d9-vb-lock", "vb %d", i); break; }
            memcpy(v, q, sizeof(q));
            IDirect3DVertexBuffer9_Unlock(vb[i]);
            IDirect3DDevice9_Clear(dev, 0, NULL, D3DCLEAR_TARGET, 0xff000000, 1.0f, 0);
            IDirect3DDevice9_BeginScene(dev);
            IDirect3DDevice9_SetTexture(dev, 0, NULL);
            IDirect3DDevice9_SetTextureStageState(dev, 0, D3DTSS_COLOROP, D3DTOP_SELECTARG2);
            IDirect3DDevice9_SetStreamSource(dev, 0, vb[i], 0, sizeof(Vtx));
            IDirect3DDevice9_DrawPrimitive(dev, D3DPT_TRIANGLESTRIP, off / sizeof(Vtx), 2);
            IDirect3DDevice9_EndScene(dev);
            {
                IDirect3DSurface9 *bb; D3DLOCKED_RECT lr; int x, y;
                IDirect3DDevice9_GetBackBuffer(dev, 0, 0, D3DBACKBUFFER_TYPE_MONO, &bb);
                IDirect3DDevice9_GetRenderTargetData(dev, bb, rb);
                IDirect3DSurface9_Release(bb);
                IDirect3DSurface9_LockRect(rb, &lr, NULL, D3DLOCK_READONLY);
                for (bad = 0, y = 0; y < 64; y++) for (x = 0; x < 64; x++)
                    bad += (((DWORD *)((BYTE *)lr.pBits + y * lr.Pitch))[x] & 0xffffff) != (c & 0xffffff);
                IDirect3DSurface9_UnlockRect(rb);
                IDirect3DDevice9_Present(dev, NULL, NULL, NULL, NULL);
            }
            if (j == 0 || j == 7 || bad)
            {
                sprintf(name, "d3d9-%s-vb-%d", i ? "dynamic" : "managed", j);
                check(!bad && (!low_filled || HIGH(v)), name, "%d wrong pixels, lock pointer %p", bad, v);
            }
        }

    /* the art mod's case: a lot more MANAGED texture memory; every one locked, filled, 1 in 16 drawn */
    if (extra_mb)
    {
        int count = extra_mb, x, y;   /* 512x512x4 = 1 MB each */
        big = calloc(count, sizeof(*big));
        uv_max = 64.0f / 512;
        for (i = 0; i < count; i++)
        {
            D3DLOCKED_RECT lr;
            if (FAILED(IDirect3DDevice9_CreateTexture(dev, 512, 512, 1, 0, D3DFMT_A8R8G8B8, D3DPOOL_MANAGED, &big[i], NULL))) break;
            if (FAILED(IDirect3DTexture9_LockRect(big[i], 0, &lr, NULL, 0))) { IDirect3DTexture9_Release(big[i]); break; }
            highbig += HIGH(lr.pBits);
            for (y = 0; y < 512; y++) for (x = 0; x < 512; x++) ((DWORD *)((BYTE *)lr.pBits + y * lr.Pitch))[x] = pattern(i, x, y);
            IDirect3DTexture9_UnlockRect(big[i], 0);
            nbig++;
            if (!(i % 16) && draw_and_compare((IDirect3DBaseTexture9 *)big[i], NULL, i, rb)) badbig++;
        }
        for (i = 0; i < nbig; i += 7) if (draw_and_compare((IDirect3DBaseTexture9 *)big[i], NULL, i, rb)) badbig++;
        printf("d3d9-bulk: %d of %d MB of MANAGED textures created, %d locked above 2 GB\n", nbig, count, highbig);
        check(nbig == count && !badbig, "d3d9-bulk", "%d of %d created, %d draws wrong", nbig, count, badbig);
        for (i = 0; i < nbig; i++) IDirect3DTexture9_Release(big[i]);
        uv_max = 1.0f;
        free(big);
    }
    for (i = 0; i < 3; i++) if (t[i]) IDirect3DTexture9_Release(t[i]);
    for (i = 0; i < 2; i++) if (vb[i]) IDirect3DVertexBuffer9_Release(vb[i]);
    IDirect3DTexture9_Release(def); IDirect3DSurface9_Release(rb);
    IDirect3DDevice9_Release(dev); IDirect3D9_Release(d3d); dev = NULL;
    DestroyWindow(hwnd);
}

/* ---- the games' DLLs ---------------------------------------------------------------------------- */

typedef HRESULT (WINAPI *PD3DXCreateTextureFromFileInMemory)(IDirect3DDevice9 *, const void *, UINT, IDirect3DTexture9 **);
typedef HRESULT (WINAPI *PDirectSoundCreate8)(const GUID *, IDirectSound8 **, IUnknown *);

static void test_dlls(void)
{
    static const char *names[] = { "d3dx9_27.dll", "dsound.dll", "dinput8.dll", "gdiplus.dll", "wininet.dll", "dbghelp.dll",
                                   "windowscodecs.dll", "d3dxof.dll", "mlang.dll", "ws2_32.dll", "winmm.dll", "msacm32.dll", "avifil32.dll" };
    unsigned i; HMODULE m; int ok;
    for (i = 0; i < sizeof(names) / sizeof(*names); i++)
    {
        char n[64];
        m = LoadLibraryA(names[i]);
        sprintf(n, "dll-load-%s", names[i]);
        check(m != NULL, n, "LoadLibrary error %lu", GetLastError());
    }
    /* d3dx9: decode a BMP from a buffer above 2 GB into a MANAGED texture */
    {
        IDirect3D9 *d3d = Direct3DCreate9(D3D_SDK_VERSION); D3DPRESENT_PARAMETERS pp = { 0 }; IDirect3DTexture9 *t = NULL;
        HWND hwnd = CreateWindowA("static", "laaprobe", WS_OVERLAPPEDWINDOW, 0, 0, 64, 64, NULL, NULL, NULL, NULL);
        PD3DXCreateTextureFromFileInMemory p = (void *)GetProcAddress(GetModuleHandleA("d3dx9_27.dll"), "D3DXCreateTextureFromFileInMemory");
        BYTE *bmp = VirtualAlloc(NULL, 65536, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
        BITMAPFILEHEADER *fh = (void *)bmp; BITMAPINFOHEADER *ih = (void *)(fh + 1); DWORD *px = (void *)(ih + 1);
        D3DLOCKED_RECT lr; HRESULT hr = E_FAIL;
        fh->bfType = 0x4d42; fh->bfOffBits = sizeof(*fh) + sizeof(*ih); fh->bfSize = fh->bfOffBits + 64 * 64 * 4;
        ih->biSize = sizeof(*ih); ih->biWidth = 64; ih->biHeight = -64; ih->biPlanes = 1; ih->biBitCount = 32;
        for (i = 0; i < 64 * 64; i++) px[i] = pattern(9, i % 64, i / 64);
        pp.Windowed = TRUE; pp.SwapEffect = D3DSWAPEFFECT_DISCARD; pp.hDeviceWindow = hwnd; pp.BackBufferWidth = pp.BackBufferHeight = 64;
        if (d3d && p && SUCCEEDED(IDirect3D9_CreateDevice(d3d, 0, D3DDEVTYPE_HAL, hwnd, D3DCREATE_HARDWARE_VERTEXPROCESSING, &pp, &dev)))
            hr = p(dev, bmp, fh->bfSize, &t);
        ok = SUCCEEDED(hr) && SUCCEEDED(IDirect3DTexture9_LockRect(t, 0, &lr, NULL, D3DLOCK_READONLY));
        if (ok) { ok = (((DWORD *)((BYTE *)lr.pBits + 5 * lr.Pitch))[7] & 0xffffff) == (pattern(9, 7, 5) & 0xffffff); IDirect3DTexture9_UnlockRect(t, 0); }
        check(ok && (!low_filled || HIGH(bmp)), "dll-d3dx9-texture-from-memory", "hr=%#lx, source %p", (unsigned long)hr, bmp);
        if (t) IDirect3DTexture9_Release(t);
        if (dev) IDirect3DDevice9_Release(dev);
        if (d3d) IDirect3D9_Release(d3d);
        dev = NULL; DestroyWindow(hwnd);
    }
    /* dsound: a secondary buffer, locked, filled, played for a moment */
    {
        PDirectSoundCreate8 p = (void *)GetProcAddress(GetModuleHandleA("dsound.dll"), "DirectSoundCreate8");
        IDirectSound8 *ds = NULL; IDirectSoundBuffer *b = NULL; DSBUFFERDESC d = { sizeof(d) }; WAVEFORMATEX wf = { WAVE_FORMAT_PCM, 2, 22050, 88200, 4, 16, 0 };
        void *a1 = NULL, *a2; DWORD n1, n2; HRESULT hr = p ? p(NULL, &ds, NULL) : E_FAIL;
        HWND hwnd = GetDesktopWindow();
        if (SUCCEEDED(hr)) hr = IDirectSound8_SetCooperativeLevel(ds, hwnd, DSSCL_PRIORITY);
        d.dwFlags = DSBCAPS_GLOBALFOCUS | DSBCAPS_CTRLVOLUME; d.dwBufferBytes = 88200; d.lpwfxFormat = &wf;
        if (SUCCEEDED(hr)) hr = IDirectSound8_CreateSoundBuffer(ds, &d, &b, NULL);
        if (SUCCEEDED(hr)) hr = IDirectSoundBuffer_Lock(b, 0, 0, &a1, &n1, &a2, &n2, DSBLOCK_ENTIREBUFFER);
        if (SUCCEEDED(hr)) { memset(a1, 0, n1); IDirectSoundBuffer_Unlock(b, a1, n1, a2, n2); IDirectSoundBuffer_SetVolume(b, DSBVOLUME_MIN);
                             IDirectSoundBuffer_Play(b, 0, 0, 0); Sleep(200); IDirectSoundBuffer_Stop(b); }
        printf("dsound: buffer lock pointer %p\n", a1);
        check(SUCCEEDED(hr) && (!low_filled || HIGH(a1)), "dll-dsound-buffer", "hr=%#lx, lock %p", (unsigned long)hr, a1);
        if (b) IDirectSoundBuffer_Release(b);
        if (ds) IDirectSound8_Release(ds);
    }
}

int main(int argc, char **argv)
{
    int i, fill = 0, slack = 0, mb = 0, hold = 0, any = 0;
    setvbuf(stdout, NULL, _IONBF, 0);
    for (i = 1; i < argc; i++)
    {
        if (!strcmp(argv[i], "--fill-low")) fill = 1;
        else if (!strcmp(argv[i], "--slack") && i + 1 < argc) slack = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--mb") && i + 1 < argc) mb = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--hold") && i + 1 < argc) hold = atoi(argv[++i]);
    }
    test_info();
    if (fill) fill_low((SIZE_T)slack << 20);
    for (i = 1; i < argc; i++)
    {
        const char *t = argv[i]; int all = !strcmp(t, "all");
        if (!strcmp(t, "--slack") || !strcmp(t, "--mb") || !strcmp(t, "--hold")) { i++; continue; }
        if (all || !strcmp(t, "space")) { test_space(); any = 1; }
        if (all || !strcmp(t, "topdown")) { test_topdown(); any = 1; }
        if (all || !strcmp(t, "thread")) { test_thread(); any = 1; }
        if (all || !strcmp(t, "d3d9")) { test_d3d9(mb); any = 1; }
        if (all || !strcmp(t, "dlls")) { test_dlls(); any = 1; }
    }
    if (!any) printf("usage: laaprobe.exe [--fill-low] [--slack MB] [--mb N] info|space|topdown|thread|d3d9|dlls|all\n");
    printf("%d failure(s)\n", failures);
    if (hold) Sleep(hold * 1000);   /* stay up (memory still held) for tools/memwatch.c to read */
    return failures;
}
