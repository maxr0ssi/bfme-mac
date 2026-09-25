#include "orig.h"
#include "gp.h"
#include <windows.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <stdlib.h>

static uint8_t *file; static size_t file_len;
static IMAGE_NT_HEADERS32 *nt; static IMAGE_SECTION_HEADER *sec;

/* the DLL's logging / config, test flavour */
void gp_log(const char *fmt, ...)
{
    va_list ap; va_start(ap, fmt);
    printf("  [gp] "); vprintf(fmt, ap); printf("\n");
    va_end(ap);
}
int gp_enabled(const char *name) { (void)name; return 1; }

const char *orig_default_path(void) { return "disk.exe"; }

uint64_t now_us(void)
{
    static LARGE_INTEGER f; LARGE_INTEGER t;
    if (!f.QuadPart) QueryPerformanceFrequency(&f);
    QueryPerformanceCounter(&t);
    return (uint64_t)(t.QuadPart * 1000000.0 / f.QuadPart);
}

int orig_load(const char *path)
{
    FILE *f = fopen(path, "rb");
    if (!f) { printf("cannot open %s\n", path); return 1; }
    fseek(f, 0, SEEK_END); file_len = ftell(f); fseek(f, 0, SEEK_SET);
    file = malloc(file_len);
    if (fread(file, 1, file_len, f) != file_len) { fclose(f); return 1; }
    fclose(f);
    nt = (IMAGE_NT_HEADERS32 *)(file + ((IMAGE_DOS_HEADER *)file)->e_lfanew);
    sec = IMAGE_FIRST_SECTION(nt);
    if (nt->FileHeader.TimeDateStamp != GP_EXE_TIMESTAMP || nt->OptionalHeader.ImageBase != GP_EXE_BASE) {
        printf("%s is not lotrbfme2ep1.exe 2.02 (timestamp %08lx)\n", path, nt->FileHeader.TimeDateStamp);
        return 1;
    }
    printf("original code from %s (timestamp %08lx)\n", path, nt->FileHeader.TimeDateStamp);
    return 0;
}

const uint8_t *orig_bytes(uint32_t va, uint32_t len)
{
    uint32_t rva = va - GP_EXE_BASE;
    for (int i = 0; i < nt->FileHeader.NumberOfSections; i++) {
        uint32_t a = sec[i].VirtualAddress, n = sec[i].SizeOfRawData;
        if (rva >= a && rva + len <= a + n) return file + sec[i].PointerToRawData + (rva - a);
    }
    return NULL;
}

void *orig_copy(uint32_t va, uint32_t len, uint32_t extra)
{
    const uint8_t *b = orig_bytes(va, len);
    if (!b) return NULL;
    uint8_t *p = VirtualAlloc(NULL, len + extra, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    memcpy(p, b, len);
    memset(p + len, 0xcc, extra);
    return p;
}

int orig_map_at(uint32_t va0, uint32_t len, uint32_t off)
{
    uint32_t va = va0 + off;
    uint32_t base = va & ~0xfffu, end = (va + len + 0xfff) & ~0xfffu;
    MEMORY_BASIC_INFORMATION m;
    for (uint32_t p = base; p < end; p += 0x1000) {
        VirtualQuery((void *)(uintptr_t)p, &m, sizeof m);
        if (m.State == MEM_FREE) {    /* reserve the whole 64 KB granule, then commit pages */
            if (!VirtualAlloc((void *)(uintptr_t)(p & ~0xffffu), 0x10000, MEM_RESERVE, PAGE_EXECUTE_READWRITE)) {
                printf("cannot reserve %08x (%lu)\n", p & ~0xffffu, GetLastError());
                return 1;
            }
            VirtualQuery((void *)(uintptr_t)p, &m, sizeof m);
        }
        if (m.State == MEM_RESERVE &&
            !VirtualAlloc((void *)(uintptr_t)p, 0x1000, MEM_COMMIT, PAGE_EXECUTE_READWRITE)) {
            printf("cannot commit %08x (%lu)\n", p, GetLastError());
            return 1;
        }
        if (m.State == MEM_COMMIT && m.Type != MEM_PRIVATE) {
            printf("cannot map %08x: in use (type %lx base %p)\n", p, m.Type, m.AllocationBase);
            return 1;
        }
    }
    const uint8_t *b = orig_bytes(va0, len);
    if (b) memcpy((void *)(uintptr_t)va, b, len);
    else memset((void *)(uintptr_t)va, 0, len);
    return 0;
}

uint32_t orig_reserve_image(void)
{
    uint32_t size = 0xe10000 - GP_EXE_BASE;
    void *p = VirtualAlloc(NULL, size, MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!p) { printf("cannot reserve %x bytes for the image\n", size); return 0; }
    return (uint32_t)(uintptr_t)p - GP_EXE_BASE;
}

void orig_fix_rel32(uint8_t *copy, uint32_t copy_va_base, uint32_t insn_va, const void *target)
{
    uint8_t *at = copy + (insn_va - copy_va_base);
    int32_t rel = (int32_t)((uint32_t)(uintptr_t)target - (uint32_t)(uintptr_t)(at + 5));
    memcpy(at + 1, &rel, 4);
}
