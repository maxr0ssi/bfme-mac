"""sagekit - build new art for BFME2 / RotWK (SAGE engine) from the player's own install.

Host modules sit at the top level. Where Blender does the work, a host module has a partner of
the same name in blender/ (alpha, clear, house, lifecycle, measure, nightlights, preview).

    formats/        W3D models, the asset cache (asset.dat), .big archives, textures, INI files
    game            the install: archives in load order, extracting what the game would load
    taxonomy        factions, lifecycle states, texture tiers and names, the memory budget
    paths, workspace, registry    where things are, one build's layout, loading assets/ recipes
    atlas, style, building        the base classes a faction and its buildings subclass
    pipeline        the build steps (host side); __main__ is the `python3 -m sagekit` CLI
    paint/          the texture painter: G-buffers -> layers -> diffuse + normal map
    blender/        everything that runs inside Blender (bpy): geometry, mapping, bake, checks
    house, housemesh, nightlights, lifecycle, alpha, clear    faction standards applied per build
    ownership, owncopy, sharedsheets, names    who draws what; own copies and free names
    install, offload, snapshot    shipping a faction; builds on another machine
    scaffold, scaffold_write, measure, preview    `sagekit new`, `measure` and `preview`

Content lives in assets/<faction>/ (a Style subclass) and assets/<faction>/<building>/ (a
Building subclass). The repo holds only recipes; every build starts from the installed game.
"""
