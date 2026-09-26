"""The cloth mesh of a house-colour model: the part the game tints in the player's colour.

EA names most of them HC_BANNER / HC_BANNER01, but not all: EBHCFortress, NBHCElvnBarx and
EBHCMalTree hang their flag on CYLINDER01, MBHCLumberMill on HC, MBHCSltrHs on 'I HC_BANNER',
GBHCFarm on GBHCFARM. What they share is the texture: every faction's house flag is painted from
a house-colour sheet (Evil_House_Color_Flag.tga for the Elves and the evil factions,
Dwarven_House_Color_Banner.tga, the Men's GU_Banr_house.tga). An HC_ mesh still wins when there is
one, so the Dwarven models resolve as before.
"""
import re

HOUSE_TEXTURE = re.compile(r"house_?colou?r|_house\.(tga|dds)$", re.I)


def house_meshes(w3d):
    """Names of the meshes of W3DFile `w3d` that carry the house colour: its HC_ meshes, else the
    ones painted from a house-colour texture; [] when it has neither."""
    hc = [n for n in w3d.meshes if n.upper().startswith("HC_")]
    return hc or [n for n, m in w3d.meshes.items() if any(HOUSE_TEXTURE.search(t) for t in m.textures)]
