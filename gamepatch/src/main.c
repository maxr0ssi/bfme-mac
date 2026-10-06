/* gamepatch DLL: a proxy dinput8.dll. The game imports DirectInput8Create from dinput8.dll, so a
 * dinput8.dll in the game folder (with WINEDLLOVERRIDES=dinput8=n,b under Wine; first in the search
 * order on Windows) is loaded before the exe's entry point. DllMain checks that the exe is RotWK
 * 2.02 and applies the enabled patches; DirectInput8Create forwards to the system dinput8.dll,
 * loaded by its full path so this DLL never loads itself.
 *
 * Switches: GAMEPATCH=0 disables every patch; GAMEPATCH_<NAME>=0/1 one patch (NAME = DXLOCK,
 * INVSQRT, NORMTAIL, HITTEST, QUATMAT, SHUTDOWN, LIMITER, FLOOR, PERFMARKER, PASSTIMERS, ANIMDEDUP,
 * ANIMDECODE, PARTICLEVTX, EDGEMAP, SHADOWPAR, SHADOWSTATS, RENDERSTATS, PARTICLESTATS, MONITOR, STALLS, MAT2QUAT, DISTCALC, BSPHERE, WORLDCELL, FTOL2, CRTSQRT, OCTILE, SHROUDSPAN, SCANTREE, AURA3D,
 * PATHFIND, MOVEAWAYCAP, MOVEAWAYQUEUE, PATHSPLIT, FLATTENLIGHT, TERRAINBOX, TERRAIN32,
 * LOGICSTATS, HIGHMEM); otherwise [patches] <name>=0/1 in gamepatch.ini
 * next to the DLL; default on, except limiter, passtimers, shadowpar, logicstats, highmem, terrainbox and terrain32 (off). Log: GAMEPATCH_LOG=<path>, else gamepatch.log next
 * to the DLL. highmem (a diagnostic, not a patch) runs in any large-address-aware exe, before the RotWK check. */
#include "gp.h"
#include "gp_render.h"
#include "par_shadow.h"
#include "gp_logic.h"
#include "gp_scale.h"
#include "p_spell.h"
#include "p_spell2.h"
#include "p_aura.h"
#include "p_mipfilter.h"
#include "p_terrain.h"
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

static int setting(const char *name, int def)   /* a number: env GAMEPATCH_<NAME>, then [patches] */
{
    char var[64], val[16];
    snprintf(var, sizeof var, "GAMEPATCH_%s", name);
    for (char *p = var; *p; p++) if (*p >= 'a' && *p <= 'z') *p -= 32;
    if (GetEnvironmentVariableA(var, val, sizeof val)) return atoi(val);
    return GetPrivateProfileIntA("patches", name, def, ini_path);
}

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
    if (enabled_default("highmem", 0)) {   /* diagnostic, off unless asked for: see gamepatch.ini */
        int slack = setting("highmem_slack", 256);
        gp_highmem(slack > 0 ? (unsigned)slack : 0);
    } else gp_log("highmem: off");
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
    run("flattenlight", gp_patch_flattenlight, &ok, 1);
    run("mipfilter", gp_patch_mipfilter, &ok, 1);
    gp_tb_mode = setting("terrainbox", 0) == 2 ? 2 : 1;   /* 1 rounded average, 2 Wine 11 to the bit */
    run("terrainbox", gp_patch_terrainbox, &ok, 0);  /* picture change, off unless chosen: after mipfilter */
    gp_t32_level = setting("terrain32", 0) == 2 ? 2 : 1;   /* 1 near tiles, 2 also the far 16-bit ones */
    run("terrain32", gp_patch_terrain32, &ok, 0);   /* picture change, off unless chosen */
    run("edgemap", gp_patch_edgemap, &ok, 1);
    run("shadowpar", gp_patch_shadowpar, &ok, 0);    /* off until tested in game: see gamepatch.ini */
    run("shadowstats", gp_patch_shadowstats, &ok, 1); /* counters only */
    run("renderstats", gp_patch_renderstats, &ok, 1); /* counters only */
    run("particlestats", gp_patch_particlestats, &ok, 1); /* counters only */
    run("mat2quat", gp_patch_mat2quat, &ok, 1);
    run("distcalc", gp_patch_distcalc, &ok, 1);
    run("bsphere", gp_patch_bsphere, &ok, 1);
    run("worldcell", gp_patch_worldcell, &ok, 1);
    run("ftol2", gp_patch_ftol2, &ok, 1);
    run("crtsqrt", gp_patch_crtsqrt, &ok, 1);
    run("octile", gp_patch_octile, &ok, 1);
    run("shroudspan", gp_patch_shroudspan, &ok, 1);
    run("scantree", gp_patch_scantree, &ok, 1);
    run("aura3d", gp_patch_aura3d, &ok, 1);
    run("firecircle", gp_patch_firecircle, &ok, 1);
    run("fxparamused", gp_patch_fxparamused, &ok, 1);
    run("pathfind", gp_patch_pathfind, &ok, 1);
    run("moveawaycap", gp_patch_moveawaycap, &ok, 1);     /* changes behaviour: same on every LAN machine */
    run("moveawayqueue", gp_patch_moveawayqueue, &ok, 1); /* changes behaviour: same on every LAN machine */
    int ps_cells = setting("pathsplit_cells", 1000);
    gp_ps_budget = ps_cells < 100 ? 100 : (uint32_t)ps_cells;
    run("pathsplit", gp_patch_pathsplit, &ok, 1);         /* changes behaviour: same on every LAN machine */
    /* last, so its call-site writes never meet another patch's byte checks */
    run("monitor", gp_patch_monitor, &ok, 1);       /* counters only; needs GAMEPATCH_MONITOR */
    run("logicstats", gp_patch_logicstats, &ok, 0); /* diagnostic, off unless asked for */
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
        gp_pst_exit_log();
        gp_mon_exit();
        gp_logic_exit_log();
        gp_l2_exit_log();
        gp_shroud_exit_log();
        gp_scan_exit_log();
        gp_au_exit_log();
        gp_fc_exit_log();
        gp_fxu_exit_log();
        gp_pf_exit_log();
        gp_maq_exit_log();
        gp_ps_exit_log();
        gp_fl_exit_log();
        gp_mf_exit_log();
        gp_tb_exit_log();
        gp_t32_exit_log();
        gp_lst_exit_log();
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
