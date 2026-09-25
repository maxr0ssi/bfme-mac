/* gamepatch DLL: a proxy dinput8.dll. The game imports DirectInput8Create from dinput8.dll, so a
 * dinput8.dll in the game folder (with WINEDLLOVERRIDES=dinput8=n,b under Wine; first in the search
 * order on Windows) is loaded before the exe's entry point. DllMain checks that the exe is RotWK
 * 2.02 and applies the enabled patches; DirectInput8Create forwards to the system dinput8.dll,
 * loaded by its full path so this DLL never loads itself.
 *
 * Switches: GAMEPATCH=0 disables every patch; GAMEPATCH_<NAME>=0/1 one patch (NAME = DXLOCK,
 * INVSQRT, NORMTAIL, HITTEST, QUATMAT, SHUTDOWN, LIMITER, FLOOR, PERFMARKER, PASSTIMERS, ANIMDEDUP,
 * ANIMDECODE, PARTICLEVTX, EDGEMAP, SHADOWPAR, SHADOWSTATS, RENDERSTATS); otherwise [patches] <name>=0/1 in gamepatch.ini
 * next to the DLL; default on, except limiter, passtimers and shadowpar (off). Log: GAMEPATCH_LOG=<path>, else gamepatch.log next
 * to the DLL. */
#include "gp.h"
#include "gp_render.h"
#include "par_shadow.h"
#include <stdio.h>
#include <stdarg.h>
#include <string.h>

int gp_patch_normtail(void);
extern DWORD gp_limiter_margin;

/* scripts/game-patch.sh recognises its own DLL by this string */
__attribute__((used)) static const char marker[] = "gamepatch proxy dinput8.dll for RotWK 2.02";

static char dll_dir[MAX_PATH], ini_path[MAX_PATH + 32], log_path[MAX_PATH + 32];
static HMODULE real_dinput8;
static int is_rotwk;

void gp_log(const char *fmt, ...)
{
    char line[512];
    SYSTEMTIME t;
    GetLocalTime(&t);
    int n = snprintf(line, sizeof line, "%04d-%02d-%02d %02d:%02d:%02d.%03d [%lu] ", t.wYear, t.wMonth,
                     t.wDay, t.wHour, t.wMinute, t.wSecond, t.wMilliseconds, GetCurrentProcessId());
    va_list ap;
    va_start(ap, fmt);
    n += vsnprintf(line + n, sizeof line - n - 2, fmt, ap);
    va_end(ap);
    if (n > (int)sizeof line - 3) n = sizeof line - 3;
    line[n++] = '\r'; line[n++] = '\n'; line[n] = 0;
    OutputDebugStringA(line);
    HANDLE f = CreateFileA(log_path, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL,
                           OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (f != INVALID_HANDLE_VALUE) {
        DWORD w;
        WriteFile(f, line, n, &w, NULL);
        CloseHandle(f);
    }
}

static int enabled_default(const char *name, int def)
{
    char var[64], val[16];
    if (GetEnvironmentVariableA("GAMEPATCH", val, sizeof val) && val[0] == '0') return 0;
    snprintf(var, sizeof var, "GAMEPATCH_%s", name);
    for (char *p = var; *p; p++) if (*p >= 'a' && *p <= 'z') *p -= 32;
    if (GetEnvironmentVariableA(var, val, sizeof val)) return val[0] != '0';
    return GetPrivateProfileIntA("patches", name, def, ini_path) != 0;
}

int gp_enabled(const char *name) { return enabled_default(name, 1); }

static void run(const char *name, int (*fn)(void), int *n_ok, int def)
{
    if (!enabled_default(name, def)) { gp_log("%s: off", name); return; }
    if (fn()) (*n_ok)++;
}

static void attach(HMODULE self)
{
    char val[MAX_PATH];
    GetModuleFileNameA(self, dll_dir, sizeof dll_dir);
    char *slash = strrchr(dll_dir, '\\');
    if (slash) *slash = 0;
    snprintf(ini_path, sizeof ini_path, "%s\\gamepatch.ini", dll_dir);
    if (!GetEnvironmentVariableA("GAMEPATCH_LOG", log_path, sizeof log_path))
        snprintf(log_path, sizeof log_path, "%s\\gamepatch.log", dll_dir);

    HMODULE exe = GetModuleHandleA(NULL);
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)((char *)exe + ((IMAGE_DOS_HEADER *)exe)->e_lfanew);
    GetModuleFileNameA(exe, val, sizeof val);
    gp_log("gamepatch " __DATE__ " loaded in %s (base %p, timestamp %08lx)", val, exe,
           nt->FileHeader.TimeDateStamp);
    if ((uintptr_t)exe != GP_EXE_BASE || nt->FileHeader.TimeDateStamp != GP_EXE_TIMESTAMP) {
        gp_log("not RotWK 2.02 (lotrbfme2ep1.exe 0x460da09e); no patches, dinput8 proxy only");
        return;
    }
    is_rotwk = 1;
    if (GetEnvironmentVariableA("GAMEPATCH_LIMITER_MARGIN", val, sizeof val))
        gp_limiter_margin = (DWORD)atoi(val);
    else
        gp_limiter_margin = GetPrivateProfileIntA("limiter", "margin_ms", 2, ini_path);
    int ok = 0;
    run("dxlock", gp_patch_dxlock, &ok, 1);
    run("invsqrt", gp_patch_invsqrt, &ok, 1);
    run("normtail", gp_patch_normtail, &ok, 1);
    run("hittest", gp_patch_hittest, &ok, 1);
    run("quatmat", gp_patch_quatmat, &ok, 1);
    run("shutdown", gp_patch_shutdown, &ok, 1);
    run("limiter", gp_patch_limiter, &ok, 0);   /* off unless asked for: see gamepatch.ini */
    run("floor", gp_patch_floor, &ok, 1);
    run("perfmarker", gp_patch_perfmarker, &ok, 1);
    run("passtimers", gp_patch_passtimers, &ok, 0);   /* diagnostic, off unless asked for */
    run("animdedup", gp_patch_animdedup, &ok, 1);
    run("animdecode", gp_patch_animdecode, &ok, 1);
    run("particlevtx", gp_patch_particlevtx, &ok, 1);
    run("edgemap", gp_patch_edgemap, &ok, 1);
    run("shadowpar", gp_patch_shadowpar, &ok, 0);    /* off until tested in game: see gamepatch.ini */
    run("shadowstats", gp_patch_shadowstats, &ok, 1); /* counters only */
    run("renderstats", gp_patch_renderstats, &ok, 1); /* counters only */
    gp_log("%d patches applied", ok);
}

BOOL WINAPI DllMain(HINSTANCE inst, DWORD reason, LPVOID reserved)
{
    if (reason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(inst);
        attach(inst);
    } else if (reason == DLL_PROCESS_DETACH && is_rotwk) {
        gp_log("exit: hittest calls %ld, bbox rejects %ld, scans %ld, x87 fallbacks %ld; quatmat x87 "
               "fallbacks %ld; shutdown Releases skipped %ld", gp_hittest_stats[0], gp_hittest_stats[1],
               gp_hittest_stats[2], gp_hittest_stats[3], gp_quat2mat_fallbacks, gp_safe_release_skipped);
        gp_render_exit_log();
        gp_shadow_exit_log();
        gp_rst_exit_log();
    }
    (void)reserved;
    return TRUE;
}

/* ---- the proxy ---------------------------------------------------------------------------- */
static FARPROC real(const char *name)
{
    if (!real_dinput8) {
        WCHAR path[MAX_PATH];
        UINT n = GetSystemDirectoryW(path, MAX_PATH - 16);
        wcscpy(path + n, L"\\dinput8.dll");
        real_dinput8 = LoadLibraryW(path);
        if (!real_dinput8) { gp_log("cannot load the system dinput8.dll (%lu)", GetLastError()); return NULL; }
    }
    return GetProcAddress(real_dinput8, name);
}

HRESULT WINAPI proxy_DirectInput8Create(HINSTANCE h, DWORD v, REFIID r, LPVOID *o, LPUNKNOWN u)
{
    typedef HRESULT (WINAPI *fn_t)(HINSTANCE, DWORD, REFIID, LPVOID *, LPUNKNOWN);
    fn_t f = (fn_t)real("DirectInput8Create");
    return f ? f(h, v, r, o, u) : E_FAIL;
}
HRESULT WINAPI proxy_DllCanUnloadNow(void)
{
    typedef HRESULT (WINAPI *fn_t)(void);
    fn_t f = (fn_t)real("DllCanUnloadNow");
    return f ? f() : S_FALSE;
}
HRESULT WINAPI proxy_DllGetClassObject(REFCLSID c, REFIID r, LPVOID *o)
{
    typedef HRESULT (WINAPI *fn_t)(REFCLSID, REFIID, LPVOID *);
    fn_t f = (fn_t)real("DllGetClassObject");
    return f ? f(c, r, o) : CLASS_E_CLASSNOTAVAILABLE;
}
HRESULT WINAPI proxy_DllRegisterServer(void)
{
    typedef HRESULT (WINAPI *fn_t)(void);
    fn_t f = (fn_t)real("DllRegisterServer");
    return f ? f() : E_FAIL;
}
HRESULT WINAPI proxy_DllUnregisterServer(void)
{
    typedef HRESULT (WINAPI *fn_t)(void);
    fn_t f = (fn_t)real("DllUnregisterServer");
    return f ? f() : E_FAIL;
}
