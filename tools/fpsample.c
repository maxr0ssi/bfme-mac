/* fpsample - frame-pointer stack sampler for one thread of a 32-bit process under Wine, for inclusive
 * profiles of the d3dx9 / d3d9 / wined3d path of a bench (Wine's PE DLLs are built with frame pointers,
 * so the EBP chain gives the real callers; eipsample.c's stack scan only keeps return sites into the exe).
 * Like eipsample it only suspends the thread for a moment; do not point it at a game you care about.
 *   i686-w64-mingw32-gcc -O2 -o build/fpsample.exe tools/fpsample.c -lwinmm
 *   wine build/fpsample.exe <exe name> <seconds> <interval ms> [main | thread id] > fp.txt
 * Output: the module table ("M name base size"), then one line per sample: "S eip ret1 ret2 ..."
 * (tools/fpsym.py turns it into a profile). */
#include <windows.h>
#include <tlhelp32.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv)
{
    const char *target = argc > 1 ? argv[1] : "d3dx9fxbench.exe";
    int secs = argc > 2 ? atoi(argv[2]) : 10, ms = argc > 3 ? atoi(argv[3]) : 1;
    DWORD pid = 0, tid = argc > 4 && strcmp(argv[4], "main") ? strtoul(argv[4], NULL, 0) : 0, t0;
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0), proc, th;
    PROCESSENTRY32 pe = {sizeof(pe)}; MODULEENTRY32 me = {sizeof(me)}; THREADENTRY32 te = {sizeof(te)};
    int n = 0;
    for (BOOL ok = Process32First(snap, &pe); ok; ok = Process32Next(snap, &pe))
        if (!_stricmp(pe.szExeFile, target)) { pid = pe.th32ProcessID; break; }
    CloseHandle(snap);
    if (!pid) { fprintf(stderr, "not running\n"); return 1; }
    proc = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, pid);
    snap = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid);
    for (BOOL ok = Module32First(snap, &me); ok; ok = Module32Next(snap, &me))
        printf("M %s %08lx %lx\n", me.szModule, (DWORD)(ULONG_PTR)me.modBaseAddr, me.modBaseSize);
    CloseHandle(snap);
    if (!tid)
    {
        snap = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
        for (BOOL ok = Thread32First(snap, &te); ok; ok = Thread32Next(snap, &te))
            if (te.th32OwnerProcessID == pid) { tid = te.th32ThreadID; break; }
        CloseHandle(snap);
    }
    th = OpenThread(THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT | THREAD_QUERY_INFORMATION, FALSE, tid);
    if (!th) { fprintf(stderr, "OpenThread failed\n"); return 1; }
    printf("T %lu\n", tid);
    timeBeginPeriod(1);
    t0 = GetTickCount();
    while (GetTickCount() - t0 < (DWORD)secs * 1000)
    {
        CONTEXT ctx = {0}; DWORD ret[48], fp, fr[2]; int d = 0; SIZE_T got;
        ctx.ContextFlags = CONTEXT_CONTROL | CONTEXT_INTEGER;
        if (SuspendThread(th) == (DWORD)-1) break;
        if (GetThreadContext(th, &ctx))
        {
            fp = ctx.Ebp;
            while (d < 48 && fp && !(fp & 3) && ReadProcessMemory(proc, (void *)(ULONG_PTR)fp, fr, 8, &got) && got == 8)
            {
                if (fr[0] <= fp) { ret[d++] = fr[1]; break; }
                ret[d++] = fr[1]; fp = fr[0];
            }
            ResumeThread(th);
            printf("S %08lx", ctx.Eip);
            for (int i = 0; i < d; i++) printf(" %lx", ret[i]);
            printf("\n"); n++;
        }
        else ResumeThread(th);
        Sleep(ms);
    }
    fprintf(stderr, "%d samples\n", n);
    return 0;
}
