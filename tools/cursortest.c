/* cursortest - the game's cursors through Wine's Mac driver, without the game.
 *
 * RotWK loads its cursors from data/cursors with LoadCursorFromFileA (81 .ani/.cur files, 32x32) and
 * sets them the way EA's Win32Mouse does (game.dat 0x4019c2 and 0x4413e3): WM_SETCURSOR always calls
 * SetCursor(current) and returns TRUE, never DefWindowProc, and the window class has no cursor. Under
 * Wine each change reaches winemac's macdrv_SetCursor, which turns the cursor into NSCursor frames,
 * or shows the macOS arrow when that fails (dlls/winemac.drv/mouse.c:826).
 *
 * This loads every .ani/.cur in <dir>, puts a small window of its own under the pointer and sets each
 * cursor once. With WINEDEBUG=+cursor the driver traces what it made of each handle;
 * scripts/cursor-test.sh matches the two and fails on any cursor that became the arrow.
 * Prints "handle file steps rate color|mono WxH hotspot" per cursor.
 *
 * Build: i686-w64-mingw32-gcc -O2 -o build/cursortest.exe tools/cursortest.c -lgdi32
 * Run:   scripts/cursor-test.sh
 * It moves the pointer once (SetCursorPos into its window, top left of the screen) and puts it back.
 */
#include <windows.h>
#include <stdio.h>
#include <string.h>

typedef HCURSOR (WINAPI *GetCursorFrameInfo_t)(HCURSOR, DWORD, DWORD, DWORD *, DWORD *);

#define MAXCUR 256
static HCURSOR cursors[MAXCUR];
static char names[MAXCUR][MAX_PATH];
static int ncursors, current;

static LRESULT CALLBACK wndproc(HWND hwnd, UINT msg, WPARAM wp, LPARAM lp)
{
    if (msg == WM_SETCURSOR)       /* as game.dat 0x4019c2: always ours, always handled */
    {
        if (ncursors) SetCursor(cursors[current]);
        return TRUE;
    }
    return DefWindowProcA(hwnd, msg, wp, lp);
}

static void pump(DWORD ms)
{
    DWORD end = GetTickCount() + ms;
    MSG m;
    do {
        while (PeekMessageA(&m, 0, 0, 0, PM_REMOVE)) { TranslateMessage(&m); DispatchMessageA(&m); }
        Sleep(5);
    } while ((LONG)(end - GetTickCount()) > 0);
}

static int load_dir(const char *dir)
{
    const char *exts[] = { "*.ani", "*.cur" };
    for (int e = 0; e < 2; e++)
    {
        char pattern[2 * MAX_PATH], path[2 * MAX_PATH];
        WIN32_FIND_DATAA fd;
        HANDLE h;
        snprintf(pattern, sizeof(pattern), "%s\\%s", dir, exts[e]);
        if ((h = FindFirstFileA(pattern, &fd)) == INVALID_HANDLE_VALUE) continue;
        do {
            if (ncursors == MAXCUR) break;
            snprintf(path, sizeof(path), "%s\\%s", dir, fd.cFileName);
            if (!(cursors[ncursors] = LoadCursorFromFileA(path)))
            {
                printf("LOADFAIL %s error %lu\n", fd.cFileName, GetLastError());
                continue;
            }
            lstrcpynA(names[ncursors++], fd.cFileName, MAX_PATH);
        } while (FindNextFileA(h, &fd));
        FindClose(h);
    }
    return ncursors;
}

static void describe(int i)
{
    GetCursorFrameInfo_t frameinfo =
        (GetCursorFrameInfo_t)GetProcAddress(GetModuleHandleA("user32.dll"), "GetCursorFrameInfo");
    DWORD rate = 0, steps = 1;
    ICONINFO ii;
    BITMAP bm = {0};

    if (frameinfo) frameinfo(cursors[i], 0, 0, &rate, &steps);
    if (!GetIconInfo(cursors[i], &ii))
    {
        printf("%p %-22s GetIconInfo failed\n", (void *)cursors[i], names[i]);
        return;
    }
    GetObjectA(ii.hbmColor ? ii.hbmColor : ii.hbmMask, sizeof(bm), &bm);
    printf("%p %-22s steps %2lu rate %2lu %s %ldx%ld hotspot %lu,%lu\n", (void *)cursors[i], names[i],
           steps, rate, ii.hbmColor ? "color" : "mono ", bm.bmWidth, bm.bmHeight, ii.xHotspot, ii.yHotspot);
    if (ii.hbmColor) DeleteObject(ii.hbmColor);
    DeleteObject(ii.hbmMask);
}

int main(int argc, char **argv)
{
    const char *dir = argc > 1 ? argv[1] : "data\\cursors";
    WNDCLASSA wc = {0};
    POINT saved;
    HWND hwnd;

    if (!load_dir(dir)) { printf("no cursors in %s\n", dir); return 1; }
    wc.lpfnWndProc = wndproc;
    wc.hInstance = GetModuleHandleA(NULL);
    wc.lpszClassName = "cursortest";      /* hCursor NULL, as the game's class */
    RegisterClassA(&wc);
    hwnd = CreateWindowExA(WS_EX_TOPMOST, "cursortest", "cursortest", WS_POPUP | WS_VISIBLE,
                           0, 0, 256, 256, NULL, NULL, wc.hInstance, NULL);
    pump(300);
    GetCursorPos(&saved);
    SetCursorPos(128, 128);               /* makes our window the server's cursor window */
    pump(100);
    for (current = 0; current < ncursors; current++)
    {
        describe(current);
        fflush(stdout);
        SetCursor(cursors[current]);
        pump(40);
    }
    SetCursorPos(saved.x, saved.y);
    DestroyWindow(hwnd);
    pump(50);
    printf("done: %d cursors\n", ncursors);
    return 0;
}
