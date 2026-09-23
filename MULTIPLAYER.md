# Playing with a friend (Mac ↔ Windows)

EA's servers are gone; the two routes are a virtual LAN (simplest) or the community
online service. Both require *identical game data* on both machines.

## 1. Same game version on both sides

- Friend on Windows: install with the **All-in-One BFME Launcher** (bfmeladder.com), pick the
  same title and patch. Our files come from the same workshop packages:
  - BFME2: `Vanilla (1.06)` base (workshop `original-BFME2`), no patch.
  - RotWK: `Vanilla (2.01)` base + `Patch 2.02 (9.7.7)` (`official-2`) + `RotWK 2.02 HD Edition`.
- Because our `ini.big` (BFME2) / `__patch202.big` (RotWK) carry local edits (LOD-preset table
  removed, camera limits), the friend must either use the same edited archive or we must play
  with pristine files. Simplest: send him our edited `.big` (backups of the originals are next to
  them: `*.preLODfix.bak`, `*.preCameraFix.bak`). HD Edition is cosmetic and safe to differ.
- Keep `Maps.big` untouched on both sides (don't install `resfix-maps/` for online play).

## 2. Virtual LAN

- Both install **ZeroTier** (free) and join the same network, or Hamachi. Tailscale won't do:
  the game discovers LAN games by UDP broadcast, which Tailscale doesn't forward.
- In game: Multiplayer → LAN. The host creates the game; the guest should see it in the list.
- If the guest sees nothing: check both are on the ZeroTier network (`zerotier-cli listnetworks`),
  Windows firewall allows the game, and both game versions match (a "mismatch" error is
  data, not network).

## 3. Community online service (later)

T3A:Online / Online Battle Arena provide lobbies and ladders; their client is Windows-only,
so on the Mac it's another program to run under Wine. Do the LAN route first.

## Cross-platform sync

The Mac runs the x86 game through Rosetta, which reproduces x86 floating point exactly, and
RTS lockstep relies on that. First real match will confirm; if it desyncs, the first suspects
are differing INIs, not the CPU.
