"""sagekit - build new art for BFME2 / RotWK (SAGE engine) from the player's own install.

Layers, bottom to top (each only imports the ones below it):

    formats/    W3D models, the asset cache (asset.dat), .big archives, textures, INI files
    game        the install: archives in load order, extracting what the game would load
    taxonomy    factions, lifecycle states, texture tiers and names, the memory budget
    atlas, style, building      the base classes a faction and its buildings subclass
    geometry, mapping           solids and atlas UVs for new geometry (Blender's mathutils)
    paint/                      the texture painter: G-buffers -> layers -> diffuse + normal map
    blender/                    everything that runs inside Blender (bpy)
    checks, pipeline, cli       verification, the build steps, `python3 -m sagekit`

Content lives in assets/<faction>/ (a Style subclass) and assets/<faction>/<building>/ (a
Building subclass). The repo holds only recipes; every build starts from the installed game.
"""
