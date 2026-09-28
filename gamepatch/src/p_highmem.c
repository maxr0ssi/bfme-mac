/* highmem: a diagnostic, OFF by default (highmem=1 in gamepatch.ini or GAMEPATCH_HIGHMEM=1). Windows
 * and Wine hand out low addresses first, so a large-address-aware game only gets pointers above
 * 0x80000000 late in a long match. At start-up (before the exe's own CRT and heaps exist) this
 * reserves every free block below 2 GB except highmem_slack MB (MEM_RESERVE, PAGE_NOACCESS, never
 * committed, kept for the process lifetime) and uses up the process heap's low free space, so the
 * game's memory comes from above 2 GB within minutes of starting (docs/MEMORY-4GB.md). The slack
 * stays one contiguous block, for DLLs loaded later and small allocations. Changes no game code;
 * does nothing unless the exe carries the LARGEADDRESSAWARE flag. */
#include "gp.h"

#define LOW_END 0x80000000u
#define GRAN    0x10000u                     /* allocation granularity */
#define HIGH(p) ((ULONG_PTR)(p) >= LOW_END)

/* the free blocks below 2 GB, in whole 64 KB units: reserve each (reserve = 1) or only measure;
   returns the bytes, with the count, the largest block and where it starts */
static ULONG_PTR walk_low(int reserve, int *count, ULONG_PTR *largest, ULONG_PTR *largest_at)
{
    MEMORY_BASIC_INFORMATION m;
    ULONG_PTR p = GRAN, total = 0;
    *count = 0; *largest = 0; *largest_at = 0;
    while (p < LOW_END && VirtualQuery((void *)p, &m, sizeof m)) {
        ULONG_PTR next = (ULONG_PTR)m.BaseAddress + m.RegionSize;
        if (m.State == MEM_FREE) {
            ULONG_PTR b = ((ULONG_PTR)m.BaseAddress + GRAN - 1) & ~(ULONG_PTR)(GRAN - 1);
            ULONG_PTR e = (next < LOW_END ? next : LOW_END) & ~(ULONG_PTR)(GRAN - 1);
            if (e > b && (!reserve || VirtualAlloc((void *)b, e - b, MEM_RESERVE, PAGE_NOACCESS))) {
                total += e - b;
                (*count)++;
                if (e - b > *largest) { *largest = e - b; *largest_at = b; }
            }
        }
        if (next <= p) break;
        p = next;
    }
    return total;
}

/* The process heap keeps free space inside segments it reserved below 2 GB earlier; use it up,
   largest pieces first, until each size comes back from above 2 GB (tools/laaprobe.c fill_heap).
   The blocks are kept, like the reservations. Returns the bytes taken; *first_high = where the heap
   now allocates. */
static SIZE_T fill_heap(void **first_high)
{
    static const SIZE_T sizes[] = { 1 << 20, 64 << 10, 4 << 10, 256, 16 };
    HANDLE h = GetProcessHeap();
    SIZE_T used = 0;
    *first_high = NULL;
    for (int i = 0; i < (int)(sizeof sizes / sizeof *sizes); i++)
        for (int k = 0; k < 200000; k++) {
            void *p = HeapAlloc(h, 0, sizes[i]);
            if (!p) break;
            if (HIGH(p)) { if (!*first_high) *first_high = p; HeapFree(h, 0, p); break; }
            used += sizes[i];
        }
    return used;
}

int gp_highmem(unsigned slack_mb)
{
    HMODULE exe = GetModuleHandleA(NULL);
    IMAGE_NT_HEADERS *nt = (IMAGE_NT_HEADERS *)((char *)exe + ((IMAGE_DOS_HEADER *)exe)->e_lfanew);
    SYSTEM_INFO si;
    if (!(nt->FileHeader.Characteristics & IMAGE_FILE_LARGE_ADDRESS_AWARE)) {
        gp_log("highmem: the exe is not large-address aware (no memory above 2 GB); nothing reserved");
        return 0;
    }
    GetSystemInfo(&si);
    if ((ULONG_PTR)si.lpMaximumApplicationAddress < LOW_END) {
        gp_log("highmem: no address space above 2 GB (highest %p); nothing reserved",
               si.lpMaximumApplicationAddress);
        return 0;
    }
    int n_before, n, n_after;
    ULONG_PTR big, big_at, big_after, at_after;
    ULONG_PTR before = walk_low(0, &n_before, &big, &big_at);

    /* the slack: the start of the largest free block, held by a placeholder while the heap is
       filled (or the heap would grow into it), then released */
    ULONG_PTR slack = (ULONG_PTR)slack_mb << 20;
    if (slack > big) slack = big;
    void *hold = slack ? VirtualAlloc((void *)big_at, slack, MEM_RESERVE, PAGE_NOACCESS) : NULL;
    if (slack && !hold) slack = 0;

    ULONG_PTR reserved = walk_low(1, &n, &big_after, &at_after);
    void *heap_high;
    SIZE_T heap_used = fill_heap(&heap_high);
    if (hold) VirtualFree(hold, 0, MEM_RELEASE);

    ULONG_PTR left = walk_low(0, &n_after, &big_after, &at_after);
    gp_log("highmem: reserved %lu MB below 2 GB in %d blocks (of %lu MB free in %d; never committed, "
           "kept until exit); used %lu KB of the process heap's low free space, which now allocates at "
           "%p; left free below 2 GB: %lu MB in %d blocks, largest %lu MB at %p (highmem_slack %u MB)",
           (unsigned long)(reserved >> 20), n, (unsigned long)(before >> 20), n_before,
           (unsigned long)(heap_used >> 10), heap_high, (unsigned long)(left >> 20), n_after,
           (unsigned long)(big_after >> 20), (void *)at_after, slack_mb);
    return reserved != 0;
}
