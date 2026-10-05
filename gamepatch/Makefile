# gamepatch: proxy dinput8.dll with in-memory patches for RotWK 2.02, and its standalone tests.
# Output goes to build/gamepatch/ (ignored by git). `make` builds the DLL and the tests;
# scripts/game-patch.sh builds, tests and installs.
MINGW   ?= /opt/homebrew/bin/i686-w64-mingw32-gcc
CC      := $(MINGW)
OUT     := ../build/gamepatch
# dependency-only lines above `all:` would otherwise make the DLL the default goal
.DEFAULT_GOAL := all
CFLAGS  := -O2 -msse2 -mfpmath=sse -ffp-contract=off -fno-strict-aliasing -Wall -Wextra \
           -Wno-cast-function-type -fno-asynchronous-unwind-tables -Isrc
PATCHES := src/patch.c src/p_dxlock.c src/p_hittest.c src/p_quat.c src/p_misc.c \
           src/p_invsqrt.S src/p_hittest.S src/p_quat.S src/p_floor.S
DLL     := $(OUT)/dinput8.dll
TESTS   := $(OUT)/t_invsqrt.exe $(OUT)/t_hittest.exe $(OUT)/t_dxlock.exe $(OUT)/t_misc.exe \
           $(OUT)/t_quat.exe $(OUT)/t_regs.exe \
           $(OUT)/t_attach.exe $(OUT)/proxytest/t_proxy.exe
# render-side patches (p_perf, p_particle, p_anim; declarations in gp_render.h)
PATCHES += src/p_perf.c src/p_particle.c src/p_anim.c src/p_perf.S src/p_particle.S src/p_anim.S
# counters for the UltraHigh render model and the shadow-mode switch log (renderstats)
PATCHES += src/p_rstats.c src/p_rstats.S
TESTS   += $(OUT)/t_rstats.exe
# timers for the RenderParticles pass, main vs shadow-map pass (particlestats)
PATCHES += src/p_pstats.c src/p_pstats.S
TESTS   += $(OUT)/t_pstats.exe
# per-frame session data for scripts/monitor.sh (monitor)
PATCHES += src/p_monitor.c src/p_stall.c
TESTS   += $(OUT)/t_monitor.exe $(OUT)/t_stall.exe
TESTS   += $(OUT)/t_perf.exe $(OUT)/t_particle.exe $(OUT)/t_anim.exe $(OUT)/t_adecode.exe
# shadow volumes on the worker pool of parallel/pool (shadowpar), edge chaining (edgemap), counters
# (shadowstats)
CFLAGS  += -I../parallel/pool
PATCHES += src/par_shadow.c src/par_shjob.c src/p_edgemap.c src/p_shstats.c src/p_shadow.S ../parallel/pool/parallel.c
TESTS   += $(OUT)/t_shadow.exe
# game-logic x87 replacements: mat2quat, distcalc, bsphere, worldcell, ftol2 (declarations gp_logic.h)
PATCHES += src/p_logic.c src/p_logic.S src/p_ftol2.S
TESTS   += $(OUT)/t_logic.exe $(OUT)/t_ftol2.exe
# msvcr71 sqrt import -> SSE with Wine's exact result (crtsqrt) and the octile path cost (octile)
PATCHES += src/p_lmath2.c src/p_lmath2.S
TESTS   += $(OUT)/t_lmath2.exe
# highmem diagnostic: the low 2 GB reserved at start-up (t_highmem: a large-address-aware stand-in)
PATCHES += src/p_highmem.c
# logicstats diagnostic: GameLogic::update per phase, its subsystems and update modules
PATCHES += src/p_lstats.c src/p_lstats.S
TESTS   += $(OUT)/t_lstats.exe
TESTS   += $(OUT)/t_highmem.exe
# unit-count scaling: shroud span updaters (shroudspan) and the range-scan quadtree walk (scantree)
PATCHES += src/p_shroud.c src/p_scan.c
TESTS   += $(OUT)/t_shroud.exe $(OUT)/t_scan.exe
$(DLL) $(TESTS): src/gp_scale.h
# pathfinder: the search step's movement check and crowd cost memoised per search (pathfind), a cell
# cap on the move-away search (moveawaycap), move-away orders spread over queue runs (moveawayqueue),
# the queue's long searches parked and resumed over queue runs (pathsplit)
PATCHES += src/p_path.c src/p_path2.c src/p_path3.c
TESTS   += $(OUT)/t_path.exe

all: $(DLL) $(TESTS)
$(DLL) $(TESTS): src/gp_render.h src/gp_logic.h src/p_stall.h
$(OUT)/t_logic.exe $(OUT)/t_ftol2.exe: tests/lm_harness.h

$(OUT):
	mkdir -p $(OUT)

$(DLL): src/main.c $(PATCHES) src/gp.h src/isqrt_range.h dinput8.def | $(OUT)
	$(CC) $(CFLAGS) -shared -o $@ src/main.c $(PATCHES) dinput8.def \
	    -static-libgcc -lwinmm -Wl,--enable-stdcall-fixup -s

# The tests run the original game code copied out of the exe on disk (path given at run time),
# so they are linked away from the game's address range.
TFLAGS  := $(CFLAGS) -Wl,--image-base,0x10000000 -static-libgcc
$(OUT)/t_%.exe: tests/t_%.c tests/orig.c tests/orig.h $(PATCHES) src/gp.h src/isqrt_range.h | $(OUT)
	$(CC) $(TFLAGS) -o $@ tests/t_$*.c tests/orig.c $(PATCHES) -lwinmm

$(OUT)/t_attach.exe: tests/t_attach.c | $(OUT)
	$(CC) -O2 -Wall -o $@ $< -Wl,--image-base,0x400000

$(OUT)/t_highmem.exe: tests/t_highmem.c | $(OUT)
	$(CC) -O2 -Wall -o $@ $< -Wl,--large-address-aware -ld3d9

$(OUT)/proxytest/t_proxy.exe: tests/t_proxy.c $(DLL) gamepatch.ini | $(OUT)
	mkdir -p $(OUT)/proxytest
	$(CC) -O2 -Wall -o $@ $< -ldinput8 -ldxguid -lpsapi
	cp $(DLL) gamepatch.ini $(OUT)/proxytest/

$(DLL) $(TESTS): src/par_shadow.h ../parallel/pool/parallel.h
$(OUT)/t_shadow.exe: tests/t_shadow.c tests/t_shadow_world.c tests/t_shadow.h tests/orig.c $(PATCHES) | $(OUT)
	$(CC) $(TFLAGS) -o $@ tests/t_shadow.c tests/t_shadow_world.c tests/orig.c $(PATCHES) -lwinmm

$(OUT)/t_path.exe: tests/t_path.c tests/t_path_world.c tests/t_path_split.c tests/t_path.h tests/orig.c $(PATCHES) | $(OUT)
	$(CC) $(TFLAGS) -o $@ tests/t_path.c tests/t_path_world.c tests/t_path_split.c tests/orig.c $(PATCHES) -lwinmm

clean:
	rm -rf $(OUT)

.PHONY: all clean
