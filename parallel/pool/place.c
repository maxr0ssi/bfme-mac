/* Core-placement probe: do Wine thread priorities steer macOS P-core vs E-core placement?
 * place.exe <nthreads> <priority> : each thread runs a fixed scalar kernel for ~2 s and reports
 * its rate; an E-core runs this ~2x slower than a P-core on an M3 Max. Priority is a Win32
 * THREAD_PRIORITY_* value (-2 LOWEST, 0 NORMAL, 1 ABOVE_NORMAL, 2 HIGHEST, 15 TIME_CRITICAL).
 * Wine's server maps priority to Mach QoS tiers (wine/src/server/thread.c apply_thread_priority). */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

static volatile LONG go, stop;
static double rate[64];

static DWORD WINAPI spin(LPVOID pv)
{
    int id = (int)(INT_PTR)pv;
    while (!go) YieldProcessor();
    LARGE_INTEGER f, a, b; QueryPerformanceFrequency(&f); QueryPerformanceCounter(&a);
    unsigned x = 12345 + id; uint64_t it = 0;
    while (!stop) {
        for (int k = 0; k < 4096; k++) x = x * 1103515245u + 12345u ^ (x >> 7);
        it++;
    }
    QueryPerformanceCounter(&b);
    rate[id] = it * 4096.0 / ((b.QuadPart - a.QuadPart) * 1e6 / f.QuadPart) + (x & 0) ;
    return 0;
}

static int cmpd(const void *a, const void *b)
{ double x = *(const double *)a, y = *(const double *)b; return x < y ? -1 : x > y; }

int main(int argc, char **argv)
{
    int n = argc > 1 ? atoi(argv[1]) : 7, pr = argc > 2 ? atoi(argv[2]) : 0;
    HANDLE th[64];
    for (int i = 0; i < n; i++) {
        th[i] = CreateThread(NULL, 0, spin, (LPVOID)(INT_PTR)i, 0, NULL);
        if (!SetThreadPriority(th[i], pr)) printf("SetThreadPriority(%d) failed %lu\n", pr, GetLastError());
    }
    Sleep(300);
    go = 1;
    Sleep(2500);
    stop = 1;
    WaitForMultipleObjects(n, th, TRUE, 5000);
    double r[64]; for (int i = 0; i < n; i++) r[i] = rate[i];
    qsort(r, n, sizeof r[0], cmpd);
    printf("place n=%2d prio=%3d  rate Mops/s: min %.0f  median %.0f  max %.0f  (min/max %.2f)\n",
           n, pr, r[0], r[n / 2], r[n - 1], r[0] / r[n - 1]);
    fflush(stdout);
    return 0;
}
