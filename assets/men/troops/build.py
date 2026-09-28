"""Stage private Men of the West troop art for review; never install or launch the game."""
from pathlib import Path
from sagekit import paths
from assets.dwarves.troops import build as pipeline
from . import catalog, art

FOLDER=Path(paths.BUILD)/'men/troops/redesign'
ARCHIVE='!!!!!!!!!!!!!sagekit-men-troops.big'


def configure():
    pipeline.configure(FOLDER,ARCHIVE,'mt',catalog,art,art,'assets.men.troops.art')
    return pipeline


if __name__=='__main__':
    configure().main()
