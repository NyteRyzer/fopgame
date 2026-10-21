"""Fairly OddParents asset pass: palette recolours of existing objects to match the design sheets."""
import recolor

PEACH = {'fff69c': 'ffd8b0', 'eecd73': 'e0a478'}

RECOLOURS = {
    # Vicky (BABYSITTER): red-orange hair, peach skin; pink top already matches
    8569: dict(PEACH, **{'bd7b41': 'f0601e', '6a4129': 'a8340c'}),
    # Jorgen Von Strangle (BODYBUILDER): tan skin
    8759: {'bd7b41': 'eab07c', '6a4129': 'b0703c'},
    # Mark Chang (ALIEN): teal-green
    7210: {'bdbdbd': '5ac8b4', '8b8b8b': '2e8a7a', '628300': '8b3cb4', 'ffffff': 'b4f0e6'},
    # Vicky's chainsaw: rusty orange body, rusty blade
    11281: {'b41800': 'c8621e', '7b1000': '7a3a10', 'bdbdbd': 'a89474', '8b8b8b': '6e5a44'},
    # Starite -> wish star: warmer gold
    8338: {'fff69c': 'ffe040', 'eecd73': 'e8a818'},
}


def apply(p):
    for i, mapping in RECOLOURS.items():
        p.set(i, recolor.remap_palette(p.get(i)[0], mapping))
    return len(RECOLOURS)
