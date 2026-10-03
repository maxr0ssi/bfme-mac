# Playing together (Mac ↔ Mac, Mac ↔ Windows)

EA's servers are gone. Play over a virtual LAN (ZeroTier, below). Everyone needs identical game
data: the same game version, the same group pack and the same art packs. A "mismatch" error when
joining means the game data differs.

## Same game version

- Everyone runs the same versions: BFME2 1.06, or RotWK 2.02 (the All-in-One BFME Launcher's
  `Vanilla (2.01)` + `Patch 2.02 (9.7.7)`). The RotWK 2.02 HD Edition is cosmetic and may differ.
- `scripts/install.sh` removes the `LODPreset` rows from `INI.big` / `__patch202.big` (RotWK) and
  `ini.big` (BFME2), which stops the crash before the menu under Rosetta; every Mac install makes
  the same edit. A player on Windows can make it too (`tools/neuter_gamelod.py <archive>`, Python)
  or use the Mac's edited archives (the originals are kept as `*.preLODfix.bak`). Whether the
  multiplayer check covers these rows is not verified; matching them removes the question.
- Keep `Maps.big` untouched on every machine.

## The group pack

The repo's INI changes live in one add-on archive, `!!!!!!!!!!group-pack.big`: particle limit
4000 and heat effects off at UltraHigh, camera max height 700 (the `EDITS` list in
`tools/make_group_pack.py`). Its name sorts before the game's own `.big` files, so it wins over
them. It changes `gamedata.ini`, which multiplayer checks, so every player needs the identical
file.

One player builds it (`scripts/install.sh … --group-pack`, or `tools/make_group_pack.py rotwk`)
and sends `build/group-pack/rotwk/install/!!!!!!!!!!group-pack.big` to the others. Mac players
install that file with `scripts/install-mod.sh rotwk <folder with the file>`; PC players drop it
into their RotWK folder. Send the file rather than rebuilding it on each machine, so every copy
is byte-identical.

## Art packs

The redesigned buildings ([docs/ART.md](docs/ART.md)) are optional in the installer:
`scripts/install.sh --buildings` adds them, `--no-buildings` takes them out. They go into the
RotWK folder as `!!!!!!!!!!!sagekit-<faction>.big` archives with edited faction INIs, and the game
compares INI data when you join. So everyone in a LAN game makes the same choice: the same
factions from the same release, or none.

The builders (`!!!!!!!!!!!!sagekit-<unit>-builder.big`) come with their faction's pack. Anything
built on your own machine with `python3 -m sagekit install` is not in the release. If you play with
that, one player copies every `*sagekit-*.big` file and `asset.dat` from their RotWK folder to the others (keep a
copy of your own `asset.dat` first), or everyone takes them out (`python3 -m sagekit revert
<faction>`, `python3 -m assets.<faction>.porter.install --revert`).

Setting up a friend's Mac by copying your installed games, so it matches yours: [docs/SECOND-MAC.md](docs/SECOND-MAC.md).

To check, compare on every machine:

```sh
cd "prefixes/w10/drive_c/Program Files (x86)/Electronic Arts/RotWK"
shasum *sagekit-*.big '!!!!!!!!!!group-pack.big'
```

The file names and hashes must be the same everywhere. A pack built on two machines from the same
recipes can still differ in bytes, so install the release's packs or copy the files instead of
building them twice.

## Virtual LAN over the internet (ZeroTier)

ZeroTier puts every player's computer on one virtual network, so the game's **Multiplayer → LAN**
works over the internet. Macs and PCs alike.

**Cost:** free for up to 10 devices on one network (ZeroTier's Personal plan; each player's
computer is one device). Beyond that it's $18/month; check zerotier.com/pricing.

**Setup (~10 minutes):**
1. Host, once: sign up at zerotier.com → *Create Network* → copy the 16-character network ID.
2. Everyone (Mac or PC): install the ZeroTier app → *Join Network* → paste the ID.
3. Host: in the ZeroTier web console, tick *Auth* next to each player's device.
4. In game: Multiplayer → LAN. One person hosts, the others see the game and join.

Tailscale won't do: the game discovers LAN games by UDP broadcast, which Tailscale doesn't forward.

**If a guest sees no games:** the game may be bound to Wi-Fi instead of the ZeroTier adapter.
Pick the ZeroTier address in the game's network/IP option (stored as `GameSpyIPAddress` in
Options.ini). Also check that everyone is on the network (`zerotier-cli listnetworks`) and that
the Windows firewall allows the game.

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
your machine as on a home network: keep System Settings → General → Sharing (File/Screen Sharing)
off unless wanted and the macOS firewall on. Only devices you approve can join.

## Mac ↔ PC sync

Mac ↔ Mac games run the same code and stay in sync. Mac ↔ PC is untested: Wine's builtin
`msvcr71` may round `sqrt` (and `sin`/`cos`) differently from Microsoft's, so results could differ
([PERFORMANCE.md](docs/PERFORMANCE.md) §10).
