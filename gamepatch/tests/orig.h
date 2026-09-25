/* Test support: read the game's original code from the exe on disk (never shipped or committed;
 * the path is given at run time) and run it in the test process. */
#ifndef ORIG_H
#define ORIG_H
#include <stdint.h>
#include <stddef.h>
int orig_load(const char *exe_path);                   /* 0 = ok; checks the PE timestamp */
const uint8_t *orig_bytes(uint32_t va, uint32_t len);   /* file bytes of image VA, or NULL */
void *orig_copy(uint32_t va, uint32_t len, uint32_t extra); /* RWX copy (+extra spare bytes) */
int orig_map_at(uint32_t va, uint32_t len, uint32_t off); /* commit RWX at va+off, copy va's bytes */
/* Wine maps NLS files over 0x400000 in a test process, so the game's code is run at va + offset
 * inside a private reservation of the image range; returns the offset (0 on failure) */
uint32_t orig_reserve_image(void);
void orig_fix_rel32(uint8_t *copy, uint32_t copy_va_base, uint32_t insn_va, const void *target);
const char *orig_default_path(void);
uint64_t now_us(void);
#endif
