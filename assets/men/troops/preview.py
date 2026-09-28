"""Paired Men of the West troop equipment and authored-animation previews, offline only."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from assets.dwarves.troops import preview as pipeline
from assets.men.troops import catalog
from sagekit import paths

FOLDER=Path(paths.BUILD)/'men/troops/redesign'
NOTES=('The staged art keeps original skeletons and authored animation clips. Missing or incompatible '
       'source references are recorded by the animation audit. Forged-blade glow can show speckling in both comparison columns; source effect materials are unchanged. These offline previews do not establish '
       'runtime appearance. Both primary and secondary skin transforms are evaluated. Particles, launched projectiles and player-colour blending are not simulated.')


if __name__=='__main__':
    pipeline.configure(FOLDER,catalog,Path(__file__).resolve(),'Men of the West troops',NOTES)
    pipeline.draw() if 'bpy' in sys.modules else pipeline.main()
