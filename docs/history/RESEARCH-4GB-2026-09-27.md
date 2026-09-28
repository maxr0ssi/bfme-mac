> **Research snapshot (2026-09-27).** This is web and source research only. No game was run for it.
> The w10 LAA investigation (crash history and the `laaprobe` run) is in
> [MEMORY-4GB.md](../MEMORY-4GB.md). This file collects outside evidence and gives a source for every claim.
> Confidence: **H** = read in source or a primary document, **M** = several secondary sources agree,
> **L** = one forum post or a search snippet (the page itself was blocked).

# 4 GB / LAA for BFME2 and RotWK under macOS Wine: research

## The findings that matter most

1. **Under new WoW64 on macOS, the game does not share its low 4 GB with host libraries (H).**
   The Wine loader on 64-bit macOS reserves `0x1000–0x200000000` (the low 8 GB) with a zerofill
   segment, so the Apple GL driver, CoreAudio, dyld and Rosetta's own allocations all land above
   it. The commit message says that "Rosetta allocates memory starting at 0x100000000" and that libSystem
   "fragments the <4GB address space which is needed for Wow64"
   ([cfa0dd9](https://gitlab.winehq.org/wine/wine/-/commit/cfa0dd9dd91eea0e401347ba41141b9c0c23131d),
   Wine 8.13; [7b82f50](https://gitlab.winehq.org/wine/wine/-/commit/7b82f507bda6b94f6876256c278d3b3637e95b8c)).
   Local check: `otool -l engines/w10/wswine.bundle/bin/wine` shows `WINE_RESERVE` at vmaddr
   `0x1000`, size `0x1fffff000`. GL textures and buffers therefore live outside the 32-bit space.
   The only host memory inside it is memory the unix side deliberately allocates below 4 GB so
   that 32-bit code can reach it (`zero_bits` allocations: DIBs, audio buffers, GL map copy
   buffers). Proton describes the same effect: after the switch to new WoW64 "the low 4 GB stops being shared"
   ([IchaLaunch PR #273](https://github.com/brutaliccus/IchaLaunch/pull/273), M).
2. **wined3d frees the system-memory copy of a `D3DPOOL_MANAGED` texture once it has been uploaded (H).**
   `wined3d_texture_evict_sysmem()` runs when every sub-resource has a location other than
   SYSMEM ([texture.c L651/L692 @ wine-10.0](https://gitlab.winehq.org/wine/wine/-/blob/wine-10.0/dlls/wined3d/texture.c#L651),
   in Wine since 2016, [e6780a5](https://gitlab.winehq.org/wine/wine/-/commit/e6780a5e0518fcf02a1b25e20dd2ea4df110a130)).
   It does not free the copy when:
   - the format needs CPU conversion (`WINED3D_TEXTURE_CONVERTED`);
   - the texture has been read back more than 50 times (`WINED3D_TEXTURE_DYNAMIC_MAP_THRESHOLD`);
   - it is uploaded while it is mapped (the "pinning sysmem" warning).

   Managed **buffers** always keep their sysmem copy ([buffer.c L987](https://gitlab.winehq.org/wine/wine/-/blob/wine-10.0/dlls/wined3d/buffer.c#L987)).
   wined3d is a 32-bit PE DLL under WoW64, so every sysmem copy it does keep is in the game's 2 GB.
   On native Windows, "Managed resources are backed by system memory"
   ([D3DPOOL docs](https://learn.microsoft.com/en-us/windows/win32/direct3d9/d3dpool), H), and the runtime
   keeps that copy in the process.
   **Implication (M, inference):** a managed DXT texture in steady state costs *less* 32-bit
   space under our wined3d than on Windows. The cost that remains is the transient load peak (the
   `.big` read buffer, the D3DX decode and the sysmem copy before upload) plus anything the game
   keeps itself. The SAGE lineage creates textures in `D3DPOOL_MANAGED` by default. Evidence:
   Generals' `DX8Wrapper::_Create_DX8_Texture(..., D3DPOOL pool=D3DPOOL_MANAGED)`
   ([dx8wrapper.h](https://github.com/electronicarts/CnC_Generals_Zero_Hour/blob/main/GeneralsMD/Code/Libraries/Source/WWVegas/WW3D2/dx8wrapper.h)).
   BFME2 is its D3D9 descendant and has not been checked. Formats with CPU conversion (24-bit
   R8G8B8, P8, some bump formats) keep their sysmem copy, so ship new art as DXT1/DXT5 with mips.
3. **Upstream Wine has supported LAA in new WoW64 since 8.10–8.14 (H).** The fixes:
   - [a3de8d1](https://gitlab.winehq.org/wine/wine/-/commit/a3de8d191b7034ec47e3ed27f91fc7b1eb61d069) "wow64: Respect the large address aware flag" (7.14);
   - [bf1606c](https://gitlab.winehq.org/wine/wine/-/commit/bf1606cf350b5b631c063344a249ec7e0e8b1e6c) "Use the full 4Gb for LAA applications on Wow64" (8.10);
   - [3ac808e](https://gitlab.winehq.org/wine/wine/-/commit/3ac808e46e4795e14c5b999aa39fd9cd15f95279) "Set Wow64 user space limit based on LARGE_ADDRESS_AWARE" (8.14);
   - CodeWeavers' macOS developers made `zero_bits` LAA-correct in winevulkan, win32u, winecoreaudio and others ([0d21363](https://gitlab.winehq.org/wine/wine/-/commit/0d21363903a0df6e6966eb6d9024ec66ace4d407), [726472f](https://gitlab.winehq.org/wine/wine/-/commit/726472fef69341ff20bea068b80da84c3a689bab), [73fc9e7](https://gitlab.winehq.org/wine/wine/-/commit/73fc9e749372c06cff4e744e92a9de6ee60cc405), 8.12–8.13);
   - [7107a9b](https://gitlab.winehq.org/wine/wine/-/commit/7107a9b1027693ba90fb8dfd11f5c51fba7e13c7) (8.13) fixed a real LAA-only bug: HMODULEs above `0x7fffffff` were "incorrectly extended to 0xffffffffxxxxxxxx".

   **Sign extension in a thunk** is the bug class to suspect if LAA crashes on w10. Wine 10.0
   applies the limit at [virtual.c L4513](https://gitlab.winehq.org/wine/wine/-/blob/wine-10.0/dlls/ntdll/unix/virtual.c#L4513).
   Relocated 32-bit DLLs still go to `0x60000000–0x7c000000`, below 2 GB
   ([server/mapping.c L263](https://gitlab.winehq.org/wine/wine/-/blob/wine-10.0/server/mapping.c#L263)).
   A pointer above 2 GB therefore only appears once the heap grows or something asks for `MEM_TOP_DOWN`.
4. **`WINE_LARGE_ADDRESS_AWARE` is not an upstream Wine variable (H).** It came from Proton
   (`PROTON_FORCE_LARGE_ADDRESS_AWARE`, [Proton 1fb4db2](https://github.com/ValveSoftware/Proton/commit/1fb4db2331490aa0075b40bfcb29365ab5c635e1);
   Proton-Wine [9de03fa](https://github.com/ValveSoftware/wine/commit/9de03fa9a529298d698b4be4c380739c68958d00),
   cited in [Wine bug 47883](https://bugs.winehq.org/show_bug.cgi?id=47883)). CrossOver also has it.
   The upstream request, bug 47883, is still UNCONFIRMED. Wine developers call forcing LAA "a
   generic workaround for a generic problem" ([bug 33858 c17](https://bugs.winehq.org/show_bug.cgi?id=33858)).
   Local `strings` check of `x86_64-unix/ntdll.so`: the variable is present in `engines/cx`
   (Wine 9.0, SikarugirCX 24.0.7) and absent in `w10` (Sikarugir Wine 10.0), `stable` (11.0) and
   `staging` (11.17). **On w10 the PE flag is the only switch**, and `tools/pe_laa.py` can set it
   again. Gcenx keeps an old "always LAA" patch as a
   [gist](https://gist.github.com/Gcenx/e1a36e56b3a2c8efe0382163e301f643) (2018, pre-WoW64 code
   paths, not directly applicable).
5. **RotWK on Windows routinely runs with LAA on, so the SAGE engine tolerates pointers above 2 GB
   in practice (M).** RotWK 2.02 ships `lotrbfme2ep1.exe` and `game.dat` with the flag set. Local
   check: `pe_laa.py` on `prefixes/stable/.../RotWK/*.preLAAoff.bak` reports "LAA on" for both,
   while retail BFME2 `game.dat` is off. The flag is also widely applied by hand (see §1). No
   public report blames an above-2 GB pointer bug in `game.dat`. The only warning found is for
   WorldBuilder: "LAA may cause terrain texture issues on your map"
   ([AotR World Builder post, T3A staff, 2019](https://forums.revora.net/topic/113459-age-of-the-ring-40-world-builder/), M).
   That is a hint that some SAGE code is not fully LAA-clean.

## 1. The BFME/RotWK community

- **Where the flag is set.**
  - RotWK 2.02 ships with it on (local check above; the 2.02 changelog pages on GameReplays
    are balance notes and do not mention it; [changelog TOC](https://www.gamereplays.org/riseofthewitchking/portals.php?show=index&name=rise-of-the-witch-king-unofficial-patch-202-changelog-toc)).
  - The Edain launcher added an "experimental 4GB patch" in 1.2.0.7 and, in 1.2.0.9, a warning that
    it "makes multiplayer unplayable" ([Edain launcher on ModDB](https://www.moddb.com/mods/edain-mod/downloads/edain-mod-launcher-1200-edain-demo-required),
    [Edain wiki](https://edain.fandom.com/wiki/Launcher); both pages were blocked, so this is from search snippets, L).
    The likely cause is a game.dat checksum or version mismatch with unpatched peers (inference).
    That does not matter on a LAN where every player uses the same patched files.
  - According to its FAQ, the AotR standalone ships "an increased memory patch and optional DXVK"
    ([AotR FAQ](https://aotr.fandom.com/wiki/Frequently_Asked_Questions), L).
  - A ModDB pack offers LAA-patched exes for all three games, which it says speed up loading and help with "black,
    untextured" objects ([ModDB](https://www.moddb.com/downloads/large-address-aware-patched-exes), L).
  - For the BFME All-in-One launcher and the HD Edition installer, no documentation of LAA
    handling was found. The ModDB pages were blocked and the
    [HD Edition release note](https://www.gamereplays.org/riseofthewitchking/portals.php?show=page&name=release_952) (2025-05-17)
    says nothing about memory. The fact that 2.02 ships with LAA on suggests the launcher's 2.02 install carries it.
- **Out-of-memory crashes and "Serious Error" reports.**
  - AotR's division lead: "The limit is hard-coded at 2gb" and long skirmishes crash at that limit
    ([Revora 115403](https://forums.revora.net/topic/115403-long-skirmish-games-eventually-crash/), M).
  - A T3A admin in 2021: "due to a memory leak … BFME2 is known to crash during longer, bigger games";
    lower shadows and settings ([Revora 116111](https://forums.revora.net/topic/116111-rotwk-direct3d-error-crash/), M).
  - In the same thread (2025), `IdealStaticGameLOD = VeryLow` fixed Direct3D `E_OUTOFMEMORY` crashes;
    the "4GB patch (in .exe and in game.dat): seemed to help, but still crashed" (L).
  - Direct3D `0x8007000e` crashes with BFME2 1.09 stopped when the poster stopped using the HD
    version ([Revora 112802](https://forums.revora.net/topic/112802-bfme2-game-error-direct3d-0x0x8007000e/), L).
- **Memory figures (weak).** One OUT_OF_MEMORY report (BFME2/RotWK 2.01 + Edain 4.4.1) saw the crash
  at about **1262 MB** in use ([GameReplays 1001631](https://www.gamereplays.org/community/index.php?showtopic=1001631), L).
  That is well under 2 GB, which fits address-space fragmentation or D3D/driver mappings rather than raw
  heap size. A RotWK 2.02 OOM 15–20 min into skirmish persisted with LAA on
  ([GameReplays 976706](https://www.gamereplays.org/community/index.php?showtopic=976706), L).
  No published measurements of vanilla or HD Edition memory use were found; our own probe is the way to get them.
- **SAGE and pointers above 2 GB.** There is no documented `game.dat` failure. There is the
  WorldBuilder terrain caveat above. The Generals source has an OOM fallback: on
  `D3DERR_OUTOFVIDEOMEMORY` it frees textures unused for 5 s and retries
  ([dx8wrapper.cpp](https://github.com/electronicarts/CnC_Generals_Zero_Hour/blob/main/GeneralsMD/Code/Libraries/Source/WWVegas/WW3D2/dx8wrapper.cpp)).
  The byte-exact source recreation Open-BFME-2 lists "Memory fix (LAA/allocator)" as an open
  roadmap item ([PLAN.md](https://github.com/Open-BFME/Open-BFME-2)).

## 2. Wine and LAA

- **Mechanism (H).** In new WoW64, `virtual_set_large_address_space()` sets
  `user_space_wow_limit` to 4 GB − 1 when the flag is present and 2 GB − 1 otherwise (item 3). There is
  no runtime override upstream (item 4). `GlobalMemoryStatus` clamps to 2 GB for non-LAA apps
  (`dlls/kernel32/heap.c`).
- **Wine bugs.**
  - The generic address-space-exhaustion bugs [44375](https://bugs.winehq.org/show_bug.cgi?id=44375)
    (NEEDINFO) and [33858](https://bugs.winehq.org/show_bug.cgi?id=33858) (Far Cry 3; the 4GB patch fixes it).
  - [34658](https://bugs.winehq.org/show_bug.cgi?id=34658): Bioshock 2 hits
    "err:d3d:resource_init Failed to allocate system memory", which is wined3d sysmem exhaustion.
  - [44743](https://bugs.winehq.org/show_bug.cgi?id=44743): Anno 1404 with LAA segfaults in
    wined3d after 60–70 min (2018, pre-WoW64, UNCONFIRMED).
  - None is specific to new WoW64 or Rosetta. The one macOS WoW64 reservation regression found,
    [55674](https://bugs.winehq.org/show_bug.cgi?id=55674), was fixed in 8.18.
- **Old versus new WoW64 on the Mac (H/M).** Old 32-bit Wine, and CrossOver's wine32on64, loaded host
  libraries into the same 4 GB. New WoW64 keeps them above 8 GB (item 1). The Wine 11
  `syscall_32to64` crash is a separate WoW64 regression, not an LAA fault; see MEMORY-4GB.md §1.
- **Rosetta (L).** Rosetta 2 executes 32-bit code segments for Wine
  ([neugierig.org](https://neugierig.org/software/blog/2023/08/x86-x64-aarch64.html)). No public report
  of LAA-specific failures under Rosetta was found. The Sikarugir issue on new-WoW64 plus Rosetta
  (c000001d when creating the desktop window) has been deleted
  ([#239](https://github.com/Sikarugir-App/Sikarugir/issues/239)).
- **CrossOver, Whisky and Gcenx (L).** None documents per-game LAA advice for macOS. CrossOver 27
  (June 2026) removed 32-bit bottles, so 32-bit games run only in 64-bit (WoW64) bottles
  ([Gigazine](https://gigazine.net/gsc_news/en/20260612-crossover-27-removes-legacy-support-mac-intel/)).

## 3. wined3d memory behaviour

- **Managed textures** keep sysmem only until upload, with the exceptions in item 2. Managed or SWVP
  **buffers** pin sysmem permanently. Dynamic buffers can pin sysmem as a "doublebuffered" fallback
  (`buffer.c`).
- **`VideoMemorySize`** (the installer sets 4096) only changes wined3d's VRAM accounting. It feeds
  `GetAvailableTextureMem` and returns `D3DERR_OUTOFVIDEOMEMORY` for GPU-only resources past the
  budget ([resource.c L202](https://gitlab.winehq.org/wine/wine/-/blob/wine-10.0/dlls/wined3d/resource.c#L202)).
  It does **not** reserve or reduce address space. The SAGE lineage queries it through
  `DX8Wrapper::Get_Free_Texture_RAM()` (Generals source).
- **CSMT.** The command-stream queue is 4 MB per queue on 32-bit builds
  (`WINED3D_CS_QUEUE_SIZE`, `wined3d_private.h`), which is negligible. The registry key is `csmt`.
- **GL buffer maps under WoW64 (Wine 10.0).** When the host pointer is above 4 GB, `opengl32` copies
  into an `_aligned_malloc` buffer in the 32-bit space for the duration of the map
  ([wgl.c L1694](https://gitlab.winehq.org/wine/wine/-/blob/wine-10.0/dlls/opengl32/wgl.c#L1694)).
  That cost is transient but proportional to the mapped size. `GL_MAP_PERSISTENT_BIT` is unsupported in
  10.0; Wine 10.18+ emulates it through Vulkan
  ([a290684](https://gitlab.winehq.org/wine/wine/-/commit/a2906847c0c94c119b74c94f0fc606ca9e9f140d)).
- **wined3d has no "keep less sysmem" registry option.** The levers are formats (no converted
  formats), not locking managed textures after load, and the game's own texture-reduction settings.

## 4. How other projects relieve 32-bit address-space pressure

- **DXVK:**
  - [PR #2663](https://github.com/doitsujin/dxvk/pull/2663) (merged 2022-07-29, 32-bit only) keeps
    D3D9 texture shadow copies in 64 MB memory-mapped files and unmaps them LRU-first when they go
    over `d3d9.textureMemory` (default 100 MB, trimmed to 3/4). This saves "up to several hundred MB"
    ([dxvk.conf](https://github.com/doitsujin/dxvk/blob/master/dxvk.conf)).
  - [v2.5](https://github.com/doitsujin/dxvk/releases/tag/v2.5) throttles staging allocations in 32-bit games.
  - Pipeline-library lifetime tracking is on by default for 32-bit apps "to save memory and address space".
  - This is the model to copy if we ever keep sysmem copies ourselves. DXVK itself is not a drop-in
    on macOS 32-bit (MoltenVK and WoW64 Vulkan mapping; not evaluated here).
- **Gallium Nine:** MR "nine: Reduce virtual memory usage of textures"
  ([mesa !9377](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/9377); title only, page blocked, L).
- **Windows history:** [KB940105](https://www.betaarchive.com/wiki/index.php/Microsoft_KB_Archive/940105)
  stopped Vista's WDDM from mapping all of VRAM into 32-bit D3D9 processes (M). That is one reason
  old D3D9 games ran out of address space on Windows well below 2 GB of heap.
- **D3D9On12:** no 32-bit address-space mitigation was found documented. It is Windows-only in any case.
- **Testing LAA safety:** Microsoft recommends
  `HKLM\...\Memory Management\AllocationPreference = 0x100000` (top-down allocations) to expose
  high-bit pointer bugs quickly ([4-GB tuning doc](https://learn.microsoft.com/en-us/windows/win32/memory/4-gigabyte-tuning);
  [KB2555189](https://support.microsoft.com/en-us/help/2555189) warns that apps may crash with it).
  A Wine equivalent would be a debug patch that ORs in `MEM_TOP_DOWN`, which would make `game.dat`'s
  LAA safety testable in one run instead of after 2 GB of play.
- **Microsoft's LAA guidance:** 32-bit LAA apps on 64-bit Windows get 4 GB, "however, developers must
  be careful that pointer assumptions are not made, such as assuming that the high-bit is never set"
  ([64-bit programming for game developers](https://learn.microsoft.com/en-us/windows/win32/dxtecharts/sixty-four-bit-programming-for-game-developers), H).

## What this suggests for the art work (inference)

1. Re-enable LAA on w10 as a test build (`pe_laa.py` can set it). The web gives no reason to expect
   an LAA-specific failure in Wine 10.0's WoW64, and RotWK 2.02 runs with it on Windows.
2. Independent of LAA, ship new textures as DXT1/DXT5 with full mips and avoid 24-bit or converted
   formats. Under wined3d a managed DXT texture's steady-state 32-bit cost is close to zero; the peak is at load.
3. Measure the process with macOS `vmmap <wine-pid>` and count the regions below `0x100000000`.
   Forum figures for RotWK memory are too thin to budget from.
