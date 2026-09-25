/* Site verification and writing. A patch is all-or-nothing: every site's current bytes must equal
 * the expected original bytes (or already equal the replacement, i.e. applied twice) before any
 * site is written. */
#include "gp.h"
#include <string.h>
#include <stdio.h>

/* The DLL patches the game at its own addresses. The tests copy the original code somewhere else
 * (Wine maps NLS files over the game's range in a test process) and set this offset. */
uint32_t gp_va_offset;

void gp_site_init(gp_site *s, uint32_t va, const uint8_t *orig, uint32_t len)
{
    s->va = va; s->len = len; s->orig = orig; s->hash = 0;
    s->wlen = len <= sizeof s->repl ? len : 0;
    memcpy(s->repl, orig, len <= sizeof s->repl ? len : sizeof s->repl);
}

void gp_site_hash(gp_site *s, uint32_t va, uint32_t len, uint64_t fnv)
{
    s->va = va; s->len = len; s->orig = NULL; s->hash = fnv; s->wlen = 0;
}

uint64_t gp_fnv1a(const void *p, uint32_t len)
{
    uint64_t h = 0xcbf29ce484222325ull;
    for (uint32_t i = 0; i < len; i++) { h ^= ((const uint8_t *)p)[i]; h *= 0x100000001b3ull; }
    return h;
}

void gp_rel32(gp_site *s, uint32_t off, uint8_t opcode, const void *target)
{
    uint32_t next = s->va + gp_va_offset + off + 5;
    int32_t rel = (int32_t)((uint32_t)(uintptr_t)target - next);
    s->repl[off] = opcode;
    memcpy(&s->repl[off + 1], &rel, 4);
}

static void hex(char *out, const uint8_t *b, uint32_t n)
{
    for (uint32_t i = 0; i < n && i < 40; i++) sprintf(out + 2 * i, "%02x", b[i]);
}

static int readable(uint32_t va, uint32_t len)
{
    MEMORY_BASIC_INFORMATION mbi;
    if (!VirtualQuery((void *)(uintptr_t)va, &mbi, sizeof mbi)) return 0;
    if (mbi.State != MEM_COMMIT || (mbi.Protect & (PAGE_NOACCESS | PAGE_GUARD))) return 0;
    return (uintptr_t)mbi.BaseAddress + mbi.RegionSize >= (uintptr_t)va + len;
}

int gp_check(const char *name, gp_site *s, int n)
{
    char a[96], b[96];
    for (int i = 0; i < n; i++) {
        const uint8_t *p = (const uint8_t *)(uintptr_t)(s[i].va + gp_va_offset);
        if (!readable(s[i].va + gp_va_offset, s[i].len)) {
            gp_log("%s: site %08x not mapped; patch skipped", name, s[i].va);
            return 0;
        }
        if (!s[i].orig) {
            uint64_t h = gp_fnv1a(p, s[i].len);
            if (h != s[i].hash) {
                gp_log("%s: code at %08x+%x differs (hash %016llx, expected %016llx); patch skipped",
                       name, s[i].va, s[i].len, (unsigned long long)h, (unsigned long long)s[i].hash);
                return 0;
            }
            continue;
        }
        if (memcmp(p, s[i].orig, s[i].len) != 0) {
            hex(a, s[i].orig, s[i].len); hex(b, p, s[i].len);
            gp_log("%s: bytes at %08x differ (expected %s, found %s); patch skipped", name, s[i].va, a, b);
            return 0;
        }
    }
    return 1;
}

int gp_apply(const char *name, gp_site *s, int n)
{
    char a[96], b[96];
    if (!gp_check(name, s, n)) return 0;
    for (int i = 0; i < n; i++) {
        void *p = (void *)(uintptr_t)(s[i].va + gp_va_offset);
        DWORD old;
        if (!s[i].wlen) continue;
        if (!VirtualProtect(p, s[i].wlen, PAGE_EXECUTE_READWRITE, &old)) {
            gp_log("%s: VirtualProtect(%08x) failed (%lu)%s", name, s[i].va, GetLastError(),
                   i ? "; EARLIER SITES OF THIS PATCH ARE ALREADY WRITTEN" : "; patch skipped");
            return 0;
        }
        memcpy(p, s[i].repl, s[i].wlen);
        VirtualProtect(p, s[i].wlen, old, &old);
        FlushInstructionCache(GetCurrentProcess(), p, s[i].wlen);
        hex(a, s[i].orig, s[i].wlen); hex(b, s[i].repl, s[i].wlen);
        gp_log("%s: %08x %s -> %s", name, s[i].va, a, b);
    }
    return 1;
}
