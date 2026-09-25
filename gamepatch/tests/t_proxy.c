/* t_proxy: the DLL as the game loads it. This exe imports DirectInput8Create from dinput8.dll like
 * lotrbfme2ep1.exe does; run from a folder holding gamepatch's dinput8.dll with
 * WINEDLLOVERRIDES=dinput8=n,b, it must get the proxy (which, seeing an exe that is not RotWK,
 * applies nothing and says so in its log) and a working IDirectInput8 from the system dinput8.dll.
 * usage: t_proxy.exe (from the folder with the proxy) */
#define DIRECTINPUT_VERSION 0x0800
#include <windows.h>
#include <dinput.h>
#include <psapi.h>
#include <stdio.h>

int main(void)
{
    IDirectInput8A *di = NULL;
    HRESULT hr = DirectInput8Create(GetModuleHandleA(NULL), DIRECTINPUT_VERSION, &IID_IDirectInput8A, (void **)&di, NULL);
    printf("DirectInput8Create: hr=%08lx object=%p\n", hr, (void *)di);
    int ok = SUCCEEDED(hr) && di;
    if (di) {
        IDirectInputDevice8A *kb = NULL;
        HRESULT h2 = IDirectInput8_CreateDevice(di, &GUID_SysKeyboard, &kb, NULL);
        printf("CreateDevice(keyboard): hr=%08lx\n", h2);
        ok &= SUCCEEDED(h2);
        if (kb) IDirectInputDevice8_Release(kb);
        IDirectInput8_Release(di);
    }
    HMODULE mods[256]; DWORD n = 0; int proxies = 0, systems = 0;
    EnumProcessModules(GetCurrentProcess(), mods, sizeof mods, &n);
    for (DWORD i = 0; i < n / sizeof mods[0]; i++) {
        char path[MAX_PATH]; GetModuleFileNameA(mods[i], path, sizeof path);
        const char *b = strrchr(path, '\\'); b = b ? b + 1 : path;
        if (_stricmp(b, "dinput8.dll")) continue;
        int proxy = GetProcAddress(mods[i], "DirectInput8Create") && strstr(path, "proxytest") != NULL;
        printf("loaded: %s (%s)\n", path, proxy ? "gamepatch proxy" : "system dinput8");
        proxies += proxy; systems += !proxy;
    }
    ok &= proxies == 1 && systems == 1;
    printf("%s\n", ok ? "PASS" : "FAIL");
    return !ok;
}
