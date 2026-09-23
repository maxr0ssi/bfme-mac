# `Lock(offset, 0)` on d3d8/d3d9 buffers — source fix for upstream Wine

Patches against **wine-11.0** (`git tag wine-11.0`, commit `db11d0fe`), also checked against
`master` (github.com/wine-mirror/wine, `df15af36`, 2026-09).

```
0001-d3d9-Treat-a-zero-lock-size-as-the-rest-of-the-buffe.patch
0002-d3d8-Treat-a-zero-lock-size-as-the-rest-of-the-buffe.patch          (wine-11.0)
0002-d3d8-Treat-a-zero-lock-size-as-the-rest-of-the-buffe.master.patch   (master variant)
0003-d3d9-tests-Add-tests-for-zero-size-buffer-locks.patch
```

Built and run against wine-11.0 on this machine (`wine/build-11.0`, WoW64, host x86_64 under
Rosetta) — see "Build and test results" at the end.

## The bug

`IDirect3DVertexBuffer9::Lock()` / `IDirect3DIndexBuffer9::Lock()` (and the d3d8 equivalents)
take `OffsetToLock` and `SizeToLock`. Per MSDN, "to lock the entire vertex buffer, specify 0 for
both parameters, SizeToLock and OffsetToLock". BFME2 (SAGE engine, 2006) locks its dynamic vertex
and index buffers exactly that way.

`d3d9_vertexbuffer_Lock()` and `d3d9_indexbuffer_Lock()` in `dlls/d3d9/buffer.c` translate the
pair into a wined3d box with

```c
    wined3d_box_set(&wined3d_box, offset, 0, offset + size, 1, 0, 1);
```

so `size == 0` yields an empty box (`left == right`), which
`wined3d_resource_check_box_dimensions()` (`dlls/wined3d/resource.c:503`) rejects
(`box->left >= box->right`). That is the source of the log lines

```
warn:d3d:wined3d_resource_check_box_dimensions Box (0, 0, 0)-(0, 1, 1) is invalid.
warn:d3d:wined3d_device_context_map Map box is invalid.
```

## Root cause, and a correction to `patches/README.md`

`patches/README.md` (section 1) says the invalid box makes `Lock()` **fail**, so the game writes
through an uninitialised pointer. **That is not what happens in wine-11.0.** In
`wined3d_device_context_map()` (`dlls/wined3d/device.c:4632` in 11.0, `:4714` in master) an invalid
box is only fatal for resources that are neither buffers nor 2D textures:

```c
    else if (FAILED(wined3d_resource_check_box_dimensions(resource, sub_resource_idx, box)))
    {
        WARN("Map box is invalid.\n");

        if (resource->type != WINED3D_RTYPE_BUFFER && resource->type != WINED3D_RTYPE_TEXTURE_2D)
            return WINED3DERR_INVALIDCALL;
        ...
    }
```

Buffers fall through and the map proceeds. That exemption has been there since
`08c96a4888` ("wined3d: Move box validation to wined3d_device_context_map.", Elizabeth Figura,
2021-06-25). Wine's own test suite relies on it: `dlls/d3d9/tests/device.c` already locks with
`(0, 0)` in `test_vb_lock_flags()`, `test_vertex_buffer_alignment()`, `test_vertex_buffer_read_write()`
and `test_resource_access()` and requires `D3D_OK`.

So the real defects are smaller than advertised, but real:

1. **Wrong dirty range for `Lock(offset > 0, 0)`.** `buffer_resource_sub_resource_map()`
   (`dlls/wined3d/buffer.c:560`) derives `offset = box->left`, `size = box->right - box->left`.
   With `size == 0` and `offset != 0`, `buffer_invalidate_bo_range()` (`dlls/wined3d/buffer.c:57`)
   records a *zero-length* dirty range instead of "to the end of the buffer", so data the
   application writes after `offset` is never uploaded to the BO. Only `offset == 0` accidentally
   works, because `buffer_invalidate_bo_range()` special-cases `!offset && !size` as
   "invalidate everything".
2. **wined3d is fed an invalid box** on a path that only survives because of the
   buffer/2D-texture escape hatch, and every such lock logs two warnings (a few thousand per
   second in BFME2's menu with `WINEDEBUG=warn+d3d`).

Consequence for this repo: the binary `jae`→`ja` patch in
`patches/wined3d/wined3d.dll.emptyrect-patched` removes the warning spam but almost certainly did
**not** fix a crash — `Lock(0, 0)` already returned `D3D_OK` with a valid pointer. The BFME2 /
RotWK access violations are the WoW64 issue in section 2 of `patches/README.md`. The source fix
here is still worth upstreaming, and it makes the binary patch unnecessary for this path.

Textures/surfaces are unaffected: `d3d9_surface_LockRect()` (`dlls/d3d9/surface.c:249`) passes
`NULL` for a `NULL` rect, and `wined3d_device_context_map()` then builds a full-subresource box
itself. `ddraw`'s `d3d_vertex_buffer7_Lock()` has no offset/size parameters and maps the whole
buffer, so ddraw needs no change.

## The fix

In each of the four `Lock()` implementations (`dlls/d3d9/buffer.c`: `d3d9_vertexbuffer_Lock`,
`d3d9_indexbuffer_Lock`; `dlls/d3d8/buffer.c`: `d3d8_vertexbuffer_Lock`, `d3d8_indexbuffer_Lock`):

```c
    wined3d_resource = wined3d_buffer_get_resource(buffer->wined3d_buffer);

    /* A size of zero locks the buffer from "offset" to its end; in particular,
     * an offset and a size of zero lock the entire buffer. */
    if (!size)
    {
        wined3d_resource_get_desc(wined3d_resource, &resource_desc);
        if (offset < resource_desc.size)
            size = resource_desc.size - offset;
    }

    wined3d_box_set(&wined3d_box, offset, 0, offset + size, 1, 0, 1);
```

Notes on the choices:

- The returned pointer must stay at `base + offset` (wined3d derives it from `box->left`), so
  "size 0" is implemented as *offset → end of buffer*, not "whole buffer from 0". DXVK does the
  same for the pointer (`D3D9DeviceEx::LockBuffer()`: `data += OffsetToLock`) and treats
  `SizeToLock == 0` as covering the buffer for dirty-range purposes; for `offset == 0` the two are
  identical, and for `offset > 0` ours is a subset that still covers everything the application can
  legally write through that pointer.
- `offset >= resource_desc.size` (an out-of-range lock) is deliberately left alone rather than
  turned into a new `D3DERR_INVALIDCALL`: MSDN does not document it, we have no Windows box to
  test it on, and the unsigned subtraction would otherwise wrap. Behaviour for that case is
  exactly what it is today (invalid box, warning, map at `base + offset`).
- The d3d8 11.0 patch additionally replaces `struct wined3d_box wined3d_box = {0};` plus manual
  `left`/`right` assignment with `wined3d_box_set()`, so the box also has `bottom = 1` / `back = 1`
  and passes validation. Master already did that part (see below).
- Not changed, but worth knowing: all four `Lock()` implementations do
  `*data = wined3d_map_desc.data;` unconditionally, with `wined3d_map_desc` an uninitialised
  local. If `wined3d_resource_map()` fails early (e.g. `E_INVALIDARG` for a missing access flag)
  the application gets a stack-garbage pointer. Initialising the struct would be a separate,
  independently arguable patch; it is not part of this series.

## What the test does

`test_buffer_zero_lock_size()` in `dlls/d3d9/tests/device.c` (registered in `START_TEST` right
after `test_vertex_buffer_alignment()`), for a 1024-byte `D3DPOOL_MANAGED` vertex buffer and a
1024-byte `D3DFMT_INDEX16` index buffer:

1. `Lock(0, 0, &data, 0)` — expects `D3D_OK` and a non-NULL pointer, writes a 1024-byte pattern
   over the full size, unlocks.
2. `Lock(0, 0, &data, D3DLOCK_READONLY)` — the whole pattern must read back.
3. `Lock(256, 0, &data, 0)` — expects `D3D_OK`, a non-NULL pointer, and that the first
   `1024 - 256` bytes at that pointer equal `pattern + 256` (the pattern is `i + (i >> 8) + 1`, which is
   not periodic in 256, so a pointer at `base` instead of `base + 256` fails it). This assertion pins down
   both halves of the semantics: the pointer is at `offset`, and the mapping extends to the end of
   the buffer. It then overwrites those bytes.
4. A final full read-only lock checks that bytes `[0, 256)` are untouched and `[256, 1024)` hold
   the new value.
5. Finally the BFME2 shape: a `D3DUSAGE_DYNAMIC | D3DUSAGE_WRITEONLY`, `D3DPOOL_DEFAULT` vertex
   buffer locked with `(0, 0, …, D3DLOCK_DISCARD)` and `(256, 0, …, D3DLOCK_NOOVERWRITE)`, both
   expected to succeed with a non-NULL pointer (no read-back, the buffer is write-only).

No `todo_wine`: every assertion is documented or driver-confirmed Windows behaviour, and all of it
passes with the patched d3d9. Managed-pool buffers are used for the read-back steps so that reading
through the lock is legal on Windows.

**That test does not detect the bug** — measured, not guessed (see below). All of its read-backs go
through `Lock()`, which for a managed buffer reads the system-memory copy, and that copy is always
written whatever dirty range wined3d recorded. The defect is that the *GPU* copy is stale, and only
a draw can see it. So the series also adds a second test.

`test_zero_size_buffer_lock()` in `dlls/d3d9/tests/visual.c` (registered in `START_TEST` right after
`test_dynamic_map_synchronization()`) draws through the lock. For a vertex buffer holding two
full-viewport quads:

1. Lock the whole buffer with an explicit size, write a **red** quad into both halves, unlock.
2. Draw the *second* quad (`DrawPrimitive(D3DPT_TRIANGLESTRIP, 4, 2)`) and read the centre pixel
   with `getPixelColor()`. This both asserts red and forces the buffer to be uploaded to the GPU,
   so that the next step has something stale to be caught out by.
3. `Lock(4 * sizeof(*quads), 0, …)` — the zero-size lock under test — write a **green** quad,
   unlock.
4. Draw the second quad again. The pixel must now be green.

Step 4 is the assertion that fails without patch 1: `buffer_invalidate_bo_range()` records a
zero-length dirty range, `wined3d_buffer_load_location(WINED3D_LOCATION_BUFFER)` copies exactly
those ranges out of system memory, so nothing is copied and the draw renders the stale red quad.

The same four steps are then repeated on a `D3DUSAGE_DYNAMIC | D3DUSAGE_WRITEONLY`,
`D3DPOOL_DEFAULT` buffer with `D3DLOCK_DISCARD` / `D3DLOCK_NOOVERWRITE`, which is the exact shape
BFME2 uses. On this machine that variant **passes even unpatched**: a dynamic default-pool map
returns a pointer directly into the mapped GL buffer object, and the only thing the dirty range
drives is `glFlushMappedBufferRange()`, which Apple's GL evidently does not need in order to see
the write. It is kept because it is the case the game actually hits and it would catch the same bug
on a driver that honours `GL_MAP_FLUSH_EXPLICIT_BIT` (and under the Vulkan backend); just do not
expect it to be the assertion that goes red.

## Applying

On wine-11.0:

```sh
git clone --depth 1 --branch wine-11.0 https://gitlab.winehq.org/wine/wine.git wine
cd wine
git am /path/to/patches/lock-whole-buffer/0001-*.patch \
       /path/to/patches/lock-whole-buffer/0002-d3d8-*-buffe.patch \
       /path/to/patches/lock-whole-buffer/0003-*.patch
```

On current master, use the `.master` variant of patch 2:

```sh
git am 0001-*.patch 0002-*.master.patch 0003-*.patch
```

Expected conflicts on master (verified with `git apply --check` against
`wine-mirror/wine@df15af36`):

- `0001` (d3d9) applies cleanly; `dlls/d3d9/buffer.c` is unchanged between 11.0 and master.
- `0002` (d3d8, 11.0 version) **does not apply**: master already converted
  `dlls/d3d8/buffer.c` to `wined3d_box_set()`, so the `wined3d_box = {0}` / `left`/`right` hunks are
  gone. Use `0002-…-master.patch`, which only adds the zero-size handling.
- `0003` (tests) applies with line offsets (−4/+71 in `device.c`, +48/+231 in `visual.c`); both
  files have grown but none of the touched context changed. Re-checked with `git apply --check`
  after the visual test was added.

## Build and test results

Compiled and run on 2026-09-22 against `wine/build-11.0` (wine-11.0, WoW64, host x86_64 under
Rosetta, `--enable-archs=i386,x86_64`), 32-bit test executable
`wine/build-11.0/dlls/d3d9/tests/i386-windows/d3d9_test.exe` in the throwaway prefix
`build/prefix-smoke`. `git am` of all three patches onto `wine-11.0` applied without a conflict,
and `dlls/d3d8`, `dlls/d3d9` and their tests compile with no new warnings.

| run | `d3d9:device` | `d3d9:visual` |
|---|---|---|
| wine-11.0, no patches | 160710 tests, 20 failures | 211196 tests, 46 failures |
| test patch only (no fix) | 160743 tests, 19 failures | 211245 tests, **47** failures |
| all three patches | 160743 tests, 19 failures | 211245 tests, 46 failures |

The one extra failure without the fix is the new visual test, and it is the expected one:

```
visual.c:27016: Test failed: Got unexpected color 0x00ff0000.
```

i.e. the stale red quad, exactly as described above. Re-running the *same* test binary against the
patched and the unpatched `d3d9.dll` (nothing else changed) gives 47 vs 46 failures, so the test
tracks the fix and not the build. None of the `device.c` assertions in `test_buffer_zero_lock_size()`
ever fails, with or without the fix.

The ~20 `d3d9:device` and 46 `d3d9:visual` failures are pre-existing on this macOS/`winemac.drv`
build and unchanged by the series; the `device` count moves between 19 and 20 from run to run
because of a flaky window-message/`IsIconic` block around `device.c:4248-4432`.

`d3d8:device` was run too, for patch 2: 57432 tests, 16 failures, **identical failure sets** with
the patched and the unpatched `d3d8.dll`. There is no d3d8 regression test for the zero-size lock —
the d3d8 change is the same edit as the d3d9 one and is covered by review plus this no-regression
run.

To test a rebuilt `d3d9.dll` without `make install`-ing over an engine, copy the install tree and
drop the fresh DLLs in:

```sh
cp -a engines/src-11.0 build/engine-patched
cp wine/build-11.0/dlls/d3d9/i386-windows/d3d9.dll build/engine-patched/lib/wine/i386-windows/
cp wine/build-11.0/dlls/d3d8/i386-windows/d3d8.dll build/engine-patched/lib/wine/i386-windows/
WINEDEBUG=-all WINEDLLOVERRIDES="mscoree,mshtml=" WINEPREFIX=$BFME_ROOT/build/prefix-smoke \
  build/engine-patched/bin/wine wine/build-11.0/dlls/d3d9/tests/i386-windows/d3d9_test.exe visual
```

(`wine/build-11.0/loader/wine` looks like it should serve the same purpose, but it hangs on this
machine instead of running anything.)

**Unrelated, but worth knowing before anyone else runs these:** `d3d9:visual` aborts about two
seconds in, with no test output at all and
`err:seh:NtRaiseException Exception frame is not in stack limits => unable to dispatch exception`,
in roughly one run in three. Re-running gets a complete run; the failure list is identical either
way. That is a 2-second, no-game reproducer of what looks like the WoW64 exception-dispatch problem
in `patches/WINE-BUG-REPORT.md`, and it may be a much cheaper `git bisect run` predicate than
starting BFME2.

## Upstream submission

Upstream is GitLab merge requests, not the old mailing list.

1. Account on https://gitlab.winehq.org, fork `wine/wine`.
2. `git checkout -b d3d9-zero-lock-size origin/master`, `git am` the three master-compatible
   patches, set `git config user.name` / `user.email` to your real name and address (Wine requires
   a real name; no `Signed-off-by` is needed any more).
3. Build and run the affected tests (`d3d8:device`, `d3d9:device`, `d3d9:visual`) before pushing.
   `d3d9:visual` is the one that matters: it is where the regression test lives.
4. Push the branch to your fork and open an MR against `wine/wine` `master`, one MR for the whole
   series. Wine's CI (`winetest`) runs the d3d9 tests on Windows; if the `Lock(offset, 0)`
   assertions fail there, the semantics need to be relaxed to "whole buffer" rather than
   "offset → end", and the test updated accordingly.
5. Expect review from Elizabeth Figura / Henri Verbeet. Two things they will likely ask about:
   calling `wined3d_resource_get_desc()` without taking `wined3d_mutex_lock()` (the resource size
   is immutable, so this should be fine, and the lock path deliberately avoids the mutex), and
   whether the out-of-range `offset` case should return `D3DERR_INVALIDCALL` (needs a Windows test
   first).

No Wine Bugzilla entry was found for this (searches for "SizeToLock 0" / "lock entire buffer" /
`check_box_dimensions` turned up nothing), so the commits carry no `Wine-Bug:` line. If a bug is
filed later, add `Wine-Bug: https://bugs.winehq.org/show_bug.cgi?id=NNNNN` to the commit bodies.
