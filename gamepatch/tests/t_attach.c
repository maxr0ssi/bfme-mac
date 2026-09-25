/* t_attach: the DLL's start-up path in a process that passes its RotWK check. This exe is linked
 * at 0x400000 and writes RotWK 2.02's PE timestamp into its own header before loading the proxy,
 * so DllMain reads the config, applies switches and tries every patch; none of the game's code is
 * here (whatever happens to be mapped at those addresses), so every patch must refuse without
 * writing anything.
 * Checks the log for that, for GAMEPATCH_QUATMAT=0 -> "quatmat: off", and for the limiter being
 * off by default. usage: t_attach.exe <proxy dll path> <log path> */
#include <windows.h>
#include <stdio.h>
#include <string.h>

static char logbuf[16384];
static int has(const char *s) { return strstr(logbuf, s) != NULL; }
static int skipped(const char *name)   /* the patch's log line ends in "patch skipped" */
{
    const char *p = strstr(logbuf, name), *e = p ? strstr(p, "\n") : NULL;
    const char *k = p ? strstr(p, "patch skipped") : NULL;
    return p && k && (!e || k < e);
}

int main(int argc, char **argv)
{
    if (argc < 3) return 2;
    HMODULE me = GetModuleHandleA(NULL);
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)((char *)me + ((IMAGE_DOS_HEADER *)me)->e_lfanew);
    DWORD old;
    VirtualProtect(&nt->FileHeader.TimeDateStamp, 4, PAGE_READWRITE, &old);
    nt->FileHeader.TimeDateStamp = 0x460da09e;
    printf("exe base %p, timestamp now %08lx\n", (void *)me, nt->FileHeader.TimeDateStamp);
    DeleteFileA(argv[2]);
    SetEnvironmentVariableA("GAMEPATCH_LOG", argv[2]);
    SetEnvironmentVariableA("GAMEPATCH_QUATMAT", "0");
    HMODULE d = LoadLibraryA(argv[1]);
    printf("LoadLibrary(%s) = %p\n", argv[1], (void *)d);
    FILE *f = fopen(argv[2], "rb");
    if (f) { logbuf[fread(logbuf, 1, sizeof logbuf - 1, f)] = 0; fclose(f); }
    printf("---- log ----\n%s-------------\n", logbuf);
    int ok = d && (uintptr_t)me == 0x400000 && has("timestamp 460da09e") && !has("not RotWK") &&
             has("quatmat: off") && has("limiter: off") && has("0 patches applied") &&
             skipped("] dxlock: ") && skipped("] invsqrt: ") && skipped("] normtail: ") &&
             skipped("] hittest: ") && skipped("] shutdown: ") && skipped("] floor: ");
    printf("%s\n", ok ? "PASS" : "FAIL");
    return !ok;
}
