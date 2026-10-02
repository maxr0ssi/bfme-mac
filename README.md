# Battle for Middle-earth II on a Mac

*The Battle for Middle-earth II* and *Rise of the Witch-king*, running properly on Apple Silicon.

![Loading a skirmish: 3 minutes before, 12 seconds now. Frames per second in your base: 10 before, 30 now.](https://github.com/maxr0ssi/bfme-mac/releases/download/media/speed.png)

## Play

You need your own copy of both games, from the original discs or the
[All-in-One BFME Launcher](https://www.bfmeladder.com/download). Then:

```sh
git clone https://github.com/maxr0ssi/bfme-mac.git && cd bfme-mac
scripts/install.sh --bfme2 <your BFME2 folder> --rotwk <your RotWK folder>
scripts/play-rotwk.sh
```

It copies your games, asks for your CD keys and adds them to Applications.
`scripts/install.sh --uninstall` removes everything.

I used to play this over LAN with my brothers. You still can, with friends on a Mac or a PC:
[MULTIPLAYER.md](MULTIPLAYER.md).

## New buildings

I've also redrawn the buildings of every faction: Dwarves, Elves, Men, Goblins, Isengard, Mordor
and Angmar, each with its own builder. They're optional in the installer: add `--buildings`.

![A Dwarven base in game](https://github.com/maxr0ssi/bfme-mac/releases/download/media/ingame-dwarves.jpg)

![An Elven base in game](https://github.com/maxr0ssi/bfme-mac/releases/download/media/ingame-elves.jpg)

Before and after:

![The Dwarven citadel, before and after](https://github.com/maxr0ssi/bfme-mac/releases/download/media/dwarves.jpg)

![The Men of the West citadel, before and after](https://github.com/maxr0ssi/bfme-mac/releases/download/media/men.jpg)

![The Elven citadel, before and after](https://github.com/maxr0ssi/bfme-mac/releases/download/media/elves.jpg)

## How

The games run through Wine. Most of the work was patching Wine and the game itself until they ran
at full speed. The game patch gives exactly the original results, so multiplayer stays in sync
with Windows players. Built with Claude Code.

[Performance](docs/PERFORMANCE.md) · [Loading](docs/LOAD-TIME.md) · [Buildings](docs/ART.md) ·
[Known issues](docs/PLAYING.md) · [Development](docs/DEVELOPMENT.md)

---

MIT ([LICENSE](LICENSE)), with the Wine patches under the LGPL ([NOTICE](NOTICE)). No game files included. Built on
[Wine](https://www.winehq.org/), the Mac Wine builds of Gcenx and
[Sikarugir](https://github.com/Sikarugir-App),
[DrewHoo's earlier work](https://github.com/DrewHoo/battle-for-middle-earth-apple-silicon) and the
[OpenSAGE](https://github.com/OpenSAGE) Blender add-on. Not affiliated with EA, Warner Bros. or
the Tolkien Estate.
