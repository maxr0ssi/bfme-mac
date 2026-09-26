# Playing together (Mac ↔ Mac, Mac ↔ Windows)

EA's servers are gone; the two routes are a virtual LAN (simplest) or the community
online service. Both require *identical game data* on both machines.

## 1. Same game version on both sides

- Everyone runs the same versions: BFME2 1.06, or RotWK 2.02 (the All-in-One BFME Launcher's
  `Vanilla (2.01)` + `Patch 2.02 (9.7.7)`). The RotWK 2.02 HD Edition is cosmetic and may differ.
- `scripts/install.sh` removes the `LODPreset` rows from `INI.big` / `__patch202.big` (RotWK) and
  `ini.big` (BFME2), which stops the crash before the menu under Rosetta; every Mac install makes
  the same edit. A friend on Windows can make it too (`tools/neuter_gamelod.py <archive>`, Python)
  or use the Mac's edited archives (the originals are kept as `*.preLODfix.bak`). Whether the
  multiplayer check covers these rows is not yet verified; matching them removes the question.
- Keep `Maps.big` untouched on both sides (don't install `resfix-maps/` for online play).

## 1b. The group pack — everyone runs the same one

Our tweaks (and later any mods) live in one add-on archive, `!!!!!!!!!!group-pack.big`, built by
`tools/make_group_pack.py` and installed next to the game's own `.big` files; its name makes it
win over them. It changes `gamedata.ini`, which multiplayer checks, so **every player needs the
identical file**: Mac friends build or copy it and install with `scripts/install-mod.sh`; PC
friends drop the same `.big` into their RotWK folder. Send the file itself rather than rebuilding
it per machine, so everyone's copy is byte-identical.

## 2. Virtual LAN over the internet (ZeroTier) — the route to use

"LAN" in the game doesn't mean same house: ZeroTier makes everyone's machines look like one local
network wherever they are, and the game's **Multiplayer → LAN** works over the internet. Macs and
PCs alike, any version as long as everyone runs the same one (ours included).

**Cost:** free for up to 10 devices on one network (ZeroTier's Personal plan, as of Aug 2026; each
player's computer is one device). Beyond that it's $18/month.

**Setup (~10 minutes):**
1. Host, once: sign up at zerotier.com → *Create Network* → copy the 16-character network ID.
2. Everyone (Mac or PC): install the ZeroTier app → *Join Network* → paste the ID.
3. Host: in the ZeroTier web console, tick *Auth* next to each friend's device.
4. In game: Multiplayer → LAN. One person hosts, the others see the game and join.

Tailscale won't do: the game discovers LAN games by UDP broadcast, which Tailscale doesn't forward.

**If a guest sees no games:** the game may be bound to Wi-Fi instead of the ZeroTier adapter —
pick the ZeroTier address in the game's network/IP option (SAGE games have one; exact place in
BFME2 not yet confirmed). Also check both are on the network (`zerotier-cli listnetworks`), the
Windows firewall allows the game, and both versions match (a "mismatch" error is data, not network).

**Turning it off when you're not playing:**
- Between sessions: ZeroTier menu-bar icon → disconnect from (or leave) the network. You're off the
  virtual network and nobody in it can reach your machine. Rejoin with the same ID to play.
- Completely (the app keeps a small background service running otherwise):
  `sudo launchctl unload /Library/LaunchDaemons/com.zerotier.one.plist` to stop,
  `sudo launchctl load /Library/LaunchDaemons/com.zerotier.one.plist` to start again.
  Windows: Services → *ZeroTier One* → Stop.

**Privacy:** game traffic is end-to-end encrypted and usually goes directly between players.
ZeroTier (the company) sees metadata while the service runs (that a device is online, its public
IP), not content; with the service stopped, nothing. While connected, the other members can reach
your machine as on a home network — keep System Settings → General → Sharing (File/Screen Sharing)
off unless wanted and the macOS firewall on. Only devices you approve can join.

## 3. Community online service (later)

T3A:Online / Online Battle Arena provide lobbies and ladders; their client is Windows-only,
so on the Mac it's another program to run under Wine. Do the LAN route first.

## Cross-platform sync

The Mac runs the x86 game through Rosetta, which reproduces x86 floating point exactly, and
RTS lockstep relies on that. First real match will confirm; if it desyncs, the first suspects
are differing INIs, not the CPU.
