# Setting up a second Mac from yours

This is how I set up my brother's Mac so we can play LAN together. You both need to own the games.
They're Windows games, but this repo runs them on a Mac, so neither of you needs a PC.

The easiest way is to copy your installed games to the other Mac. Then it has exactly what you
have: the same game version, the new buildings, icons and Create-a-Hero parts. LAN games need
that.

## On your Mac

1. Play a skirmish first, so you know it all works.
2. Copy these two folders to a USB drive, or AirDrop them (about 15 GB):

   ```
   prefixes/w10/drive_c/Program Files (x86)/Electronic Arts/BFME2
   prefixes/w10/drive_c/Program Files (x86)/Electronic Arts/RotWK
   ```

## On the second Mac

1. Install Rosetta and the command line tools (for git):

   ```sh
   softwareupdate --install-rosetta --agree-to-license
   xcode-select --install
   ```

2. Put the two folders somewhere, e.g. `~/Games/BFME2` and `~/Games/RotWK`.
3. Install:

   ```sh
   git clone https://github.com/maxr0ssi/bfme-mac.git && cd bfme-mac
   scripts/install.sh --bfme2 ~/Games/BFME2 --rotwk ~/Games/RotWK
   ```

   When it asks for CD keys, press Enter and it makes one. Each Mac needs its own key. When it asks
   about new buildings, say no. They're already in the folders you copied, and the download is an
   older set that wouldn't match yours.

4. Play: `scripts/play-rotwk.sh`, or the app in Applications.

To play over the internet, set up ZeroTier as in [MULTIPLAYER.md](../MULTIPLAYER.md#virtual-lan-over-the-internet-zerotier),
then go to Multiplayer → LAN in game.

## After you change anything

Whenever you install new art on your Mac, the other Mac needs the same files again. Otherwise
joining gives a "mismatch" error. Copy every file with `sagekit` in its name, plus `asset.dat`,
from your RotWK folder to the same folder on theirs:
`prefixes/w10/drive_c/Program Files (x86)/Electronic Arts/RotWK` in their `bfme-mac` folder.

Then run this on both Macs. The lists must be the same:

```sh
cd "prefixes/w10/drive_c/Program Files (x86)/Electronic Arts/RotWK"
shasum *sagekit-*.big asset.dat '!!!!!!!!!!group-pack.big'
```

## On a smaller Mac

A 13" M1 MacBook runs it fine. To keep it smooth:

- Leave Retina off. The installer does this by default.
- Plug it in and turn Low Power Mode off.
- With 8 GB of memory, close the browser before playing.
- If big battles stutter, lower Detail in the game's Options. It only changes your own screen, so
  the other player can stay on UltraHigh.
