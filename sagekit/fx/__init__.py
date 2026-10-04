"""Effects in each faction's colours: tinted copies of EA's particle systems, one shared archive.

    assets/<faction>/fx.py      the faction's recipe (plan.FactionFX): its ramps, the spell book
                                powers whose FX take them, the classes its building fire takes
    blocks      the INI grammar of particle systems, FX lists and object modules, by line
    tint        a system's Color keyframes moved onto a ramp, every other value EA's
    plan        a recipe resolved: which systems and FX lists get copies, which references move
    compose     the copies and the moved references written onto the game's INIs
    checks      what must hold: EA's file plus exactly our blocks, nothing but colours changed
    install     stage, install, revert, status; the guard sagekit/install.py calls
    preview     the review sheet: EA's effect beside ours (an approximation of the game's sprites)

    RotWK/!!!!!!!!!!!!sagekit-fx.big    (twelve '!': read before every faction pack, which has
                                         eleven, so its fxparticlesystem.ini is the one the game uses)

    python3 -m sagekit.fx --stage | --install | --revert | --status | --review
"""
ARCHIVE = "!!!!!!!!!!!!sagekit-fx.big"
