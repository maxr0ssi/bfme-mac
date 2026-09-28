/* t_highmem: the highmem diagnostic in a large-address-aware stand-in for the game (no game code).
 * Loads the proxy with GAMEPATCH_HIGHMEM=1 and GAMEPATCH_HIGHMEM_SLACK=<slack>, then checks: the log
 * line; at most <slack> MB left free below 2 GB; once the slack is used (64 KB reservations), every
 * kind of new memory above 2 GB: VirtualAlloc, the process heap's small blocks (all but a few freed
 * since the fill) and large ones, a new heap, msvcrt malloc, a thread stack, DLLs loaded late, and d3d9
 * MANAGED / SYSTEMMEM / DYNAMIC texture and vertex-buffer locks (written and read back).
 * usage: t_highmem.exe <proxy dll path> <log path> [slack MB, default 32]
 * Build: -Wl,--large-address-aware -ld3d9 (gamepatch/Makefile). Run with dinput8=n,b. */
#define COBJMACROS
#include <windows.h>
#include <d3d9.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define HIGH(p) ((ULONG_PTR)(p) >= 0x80000000u)
static int fails;
static char logbuf[16384];

static void check(int ok, const char *what, const void *p)
{
    printf("%s %-34s %p\n", ok ? "ok  " : "FAIL", what, p);
    fails += !ok;
}

static ULONG_PTR largest_free_low(void)   /* in whole 64 KB units, as VirtualAlloc can use it */
{
    MEMORY_BASIC_INFORMATION m; ULONG_PTR p = 0x10000, big = 0;
    while (p < 0x80000000u && VirtualQuery((void *)p, &m, sizeof m)) {
        ULONG_PTR next = (ULONG_PTR)m.BaseAddress + m.RegionSize;
        ULONG_PTR b = ((ULONG_PTR)m.BaseAddress + 0xffff) & ~(ULONG_PTR)0xffff;
        ULONG_PTR e = (next < 0x80000000u ? next : 0x80000000u) & ~(ULONG_PTR)0xffff;
        if (m.State == MEM_FREE && e > b && e - b > big) big = e - b;
        if (next <= p) break;
        p = next;
    }
    return big;
}

static DWORD WINAPI stack_probe(void *out) { volatile int local = 1; *(ULONG_PTR *)out = (ULONG_PTR)&local; return local; }

static void d3d9_locks(void)
{
    WNDCLASSA wc = { 0 }; D3DPRESENT_PARAMETERS pp = { 0 }; IDirect3DDevice9 *dev = NULL;
    IDirect3DTexture9 *t; IDirect3DVertexBuffer9 *vb; D3DLOCKED_RECT lr; void *v;
    static const D3DPOOL pool[3] = { D3DPOOL_MANAGED, D3DPOOL_SYSTEMMEM, D3DPOOL_DEFAULT };
    static const char *name[3] = { "d3d9 MANAGED texture lock", "d3d9 SYSTEMMEM texture lock", "d3d9 DYNAMIC texture lock" };
    wc.lpfnWndProc = DefWindowProcA; wc.hInstance = GetModuleHandleA(NULL); wc.lpszClassName = "t_highmem";
    RegisterClassA(&wc);
    HWND hwnd = CreateWindowA("t_highmem", "t_highmem", WS_OVERLAPPEDWINDOW, 0, 0, 64, 64, NULL, NULL, wc.hInstance, NULL);
    IDirect3D9 *d3d = Direct3DCreate9(D3D_SDK_VERSION);
    pp.Windowed = TRUE; pp.SwapEffect = D3DSWAPEFFECT_DISCARD; pp.hDeviceWindow = hwnd;
    pp.BackBufferWidth = pp.BackBufferHeight = 64; pp.BackBufferFormat = D3DFMT_X8R8G8B8;
    HRESULT hr = d3d ? IDirect3D9_CreateDevice(d3d, 0, D3DDEVTYPE_HAL, hwnd, D3DCREATE_HARDWARE_VERTEXPROCESSING, &pp, &dev) : E_FAIL;
    check(SUCCEEDED(hr), "d3d9 device", dev);
    if (FAILED(hr)) return;
    for (int i = 0; i < 3; i++) {
        int ok = SUCCEEDED(IDirect3DDevice9_CreateTexture(dev, 256, 256, 1, i == 2 ? D3DUSAGE_DYNAMIC : 0,
                     D3DFMT_A8R8G8B8, pool[i], &t, NULL)) &&
                 SUCCEEDED(IDirect3DTexture9_LockRect(t, 0, &lr, NULL, i == 2 ? D3DLOCK_DISCARD : 0));
        if (ok) {
            memset(lr.pBits, 0x5a, 256 * lr.Pitch);
            ok = ((BYTE *)lr.pBits)[255 * lr.Pitch + 1023] == 0x5a;
            IDirect3DTexture9_UnlockRect(t, 0);
        }
        check(ok && HIGH(lr.pBits), name[i], ok ? lr.pBits : NULL);
        if (t) IDirect3DTexture9_Release(t);
    }
    int ok = SUCCEEDED(IDirect3DDevice9_CreateVertexBuffer(dev, 65536, D3DUSAGE_DYNAMIC | D3DUSAGE_WRITEONLY, 0,
                 D3DPOOL_DEFAULT, &vb, NULL)) && SUCCEEDED(IDirect3DVertexBuffer9_Lock(vb, 0, 0, &v, D3DLOCK_DISCARD));
    if (ok) { memset(v, 1, 65536); IDirect3DVertexBuffer9_Unlock(vb); }
    check(ok && HIGH(v), "d3d9 DYNAMIC vertex buffer lock", ok ? v : NULL);
    if (vb) IDirect3DVertexBuffer9_Release(vb);
    IDirect3DDevice9_Release(dev); IDirect3D9_Release(d3d); DestroyWindow(hwnd);
}

int main(int argc, char **argv)
{
    if (argc < 3) return 2;
    int slack = argc > 3 ? atoi(argv[3]) : 32;
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)((char *)GetModuleHandleA(NULL) + ((IMAGE_DOS_HEADER *)GetModuleHandleA(NULL))->e_lfanew);
    printf("exe LAA flag %s, largest free block below 2 GB before: %lu MB\n",
           nt->FileHeader.Characteristics & IMAGE_FILE_LARGE_ADDRESS_AWARE ? "on" : "off",
           (unsigned long)(largest_free_low() >> 20));
    DeleteFileA(argv[2]);
    SetEnvironmentVariableA("GAMEPATCH_LOG", argv[2]);
    SetEnvironmentVariableA("GAMEPATCH_HIGHMEM", "1");
    SetEnvironmentVariableA("GAMEPATCH_HIGHMEM_SLACK", argc > 3 ? argv[3] : "32");
    HMODULE d = LoadLibraryA(argv[1]);
    FILE *f = fopen(argv[2], "rb");
    if (f) { logbuf[fread(logbuf, 1, sizeof logbuf - 1, f)] = 0; fclose(f); }
    printf("---- log ----\n%s-------------\n", logbuf);
    check(d && strstr(logbuf, "] highmem: reserved "), "proxy loaded, highmem log line", d);
    ULONG_PTR big = largest_free_low();
    printf("largest free block below 2 GB after: %lu KB\n", (unsigned long)(big >> 10));
    check(big <= ((ULONG_PTR)slack << 20), "at most the slack left free", (void *)big);

    /* use up the slack first (64 KB reservations, down to its last piece), as the game's first
       minutes would: then every new allocation must come from above 2 GB */
    int low_64k = 0; void *p;
    while ((p = VirtualAlloc(NULL, 1 << 16, MEM_RESERVE, PAGE_NOACCESS)) && !HIGH(p)) low_64k++;
    printf("the slack took %d x 64 KB below 2 GB, then %p\n", low_64k, p);
    check(p && HIGH(p) && low_64k <= slack * 16, "VirtualAlloc 64 KB after the slack", p);
    p = VirtualAlloc(NULL, 1 << 20, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE);
    check(p && HIGH(p), "VirtualAlloc 1 MB", p);
    if (p) { memset(p, 0x77, 1 << 20); check(((BYTE *)p)[(1 << 20) - 1] == 0x77, "  written and read back", p); }
    HANDLE ph = GetProcessHeap();
    /* the heap's low free space is used up; only blocks freed since (the loader, the log's file
       I/O) can still come back low */
    SIZE_T small[] = { 16, 256, 4096, 65536 };
    for (int i = 0; i < 4; i++) {
        char what[64]; int low = 0;
        for (int k = 0; k < 200; k++) if ((p = HeapAlloc(ph, 0, small[i])) && !HIGH(p)) low++;
        snprintf(what, sizeof what, "process heap 200 x %lu B, %d low", (unsigned long)small[i], low);
        check(p && HIGH(p) && low <= 20, what, p);
    }
    p = HeapAlloc(ph, 0, 4 << 20);
    check(p && HIGH(p), "process heap 4 MB block", p);
    HANDLE nh = HeapCreate(0, 0, 0);
    p = nh ? HeapAlloc(nh, 0, 100) : NULL;
    check(p && HIGH(p), "new heap, 100 bytes", p);
    p = malloc(100);
    printf("info msvcrt malloc 100 bytes %p (a heap created before the proxy loaded)\n", p);
    p = malloc(8 << 20);
    check(p && HIGH(p), "msvcrt malloc 8 MB", p);
    ULONG_PTR sp = 0;
    HANDLE th = CreateThread(NULL, 0, stack_probe, &sp, 0, NULL);
    WaitForSingleObject(th, 5000);
    check(sp && HIGH(sp), "new thread's stack", (void *)sp);
    HMODULE m1 = LoadLibraryA("d3dx9_27.dll"), m2 = LoadLibraryA("dsound.dll");
    check(m1 != NULL, "late LoadLibrary d3dx9_27.dll", m1);
    check(m2 != NULL, "late LoadLibrary dsound.dll", m2);
    d3d9_locks();
    printf("%d failure(s)\n%s\n", fails, fails ? "FAIL" : "PASS");
    return fails;
}
