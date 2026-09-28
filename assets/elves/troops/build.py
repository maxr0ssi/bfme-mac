"""Stage private Elven troop art for review; never install or launch the game."""
from pathlib import Path
from sagekit import paths
from assets.dwarves.troops import build as pipeline
from . import catalog, art

FOLDER=Path(paths.BUILD)/'elves/troops/redesign'
ARCHIVE='!!!!!!!!!!!!!sagekit-elf-troops.big'


def configure():
    pipeline.configure(FOLDER,ARCHIVE,'et',catalog,art,art,'assets.elves.troops.art')
    return pipeline


if __name__=='__main__':
    configure().main()
