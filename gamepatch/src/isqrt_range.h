/* Inputs (float bit patterns) for which the SSE inverse square root runs; everything else runs the
 * original x87 code. Over all 2^32 inputs the unguarded SSE sequence differs from the game's x87
 * result only for negative inputs, NaNs and positive inputs >= 0x7e6ecbbc (~7.9e37, where y*y
 * becomes denormal); the range below keeps positive normal floats up to 2^124.
 * (gamepatch/tests/t_invsqrt.c, logs/gamepatch/t_invsqrt.txt) */
#define GP_ISQRT_LO 0x00800000
#define GP_ISQRT_HI 0x7dffffff
