"""FOP UI reskin: orange buttons -> pink, yellow panels -> lavender, lime accents -> FOP green.

Colours are matched in the DS's 5-bit space. Only UI material is touched: NCLR palettes of the
2D sprite containers, the 256-colour menu/background palettes, and the UI sprite images.
"""
import os
import struct
import img
import ncer
import titlegen


def bgr5(h):
    return (int(h[:2], 16) >> 3) | (int(h[2:4], 16) >> 3) << 5 | (int(h[4:], 16) >> 3) << 10


MAP = {bgr5(a): bgr5(b) for a, b in {
    'f8a820': 'e8489c', 'e09018': 'c03080', 'f8c040': 'f070b8',    # orange buttons / frames
    'f8f860': 'e8d0f8', 'f8e848': 'd8b8f0', 'f0f058': 'e0c4f4',    # yellow panels
    'f8f068': 'ecd4fa', 'f8f8a8': 'f4e8fc', 'f0d040': 'c8a0e8', 'f8f850': 'e8d0f8',
    'd8f020': '80d850', 'a8d820': '58b838', 'd0f840': '90e060',    # lime accents
    'f8f858': 'e8d0f8', 'e8d848': 'd8b8f0', 'f8e898': 'f0dcfa',    # notepad / pause panels
    '888828': '7850a0', 'f0a820': 'e8489c', 'b8e028': '80d850',
}.items()}

# 256-colour palettes of the menu / HUD backgrounds that use the UI colours
RAW_PALETTES = [745, 748, 749, 750, 751, 752, 753, 754, 755, 756, 757, 758, 759, 760, 761, 765, 766,
                767, 924, 931, 993, 26869, 30350, 31696, 31698, 31727, 31739, 31802, 31814, 31820]
# short raw palettes of HUD / banner sprites (LEVEL START OK button, Wish counter)
SHORT_PALETTES = [929, 960, 963, 966]
# HUD player-head icon (8bpp, rows 3 and 13 of the HUD NCLRs): Maxwell's red hat -> Timmy's pink cap
HUD_HEAD_NCLR, HUD_HEAD_ROWS = (763, 964, 967), (3, 13)
HUD_HEAD_MAP = {bgr5(a): bgr5(b) for a, b in {
    'b01800': 'e8489c', '781000': 'a02870'}.items()}
NCLR = [743, 762, 763, 764, 923, 962, 964, 967, 968, 995, 996, 29061, 29967, 31817, 33322]


def _swap(colours):
    return [MAP.get(c & 0x7fff, c & 0x7fff) | (c & 0x8000) for c in colours]


MENU_BUTTONS = range(5636, 5670)        # back arrow, toolbar buttons
# notepad keys, toolbar and HUD buttons found while playing (8885 is an in-world object)
EXTRA_UI = {5502, 5504, 5510, 5521, 5525, 5526, 5528, 11914, 12543, 12544, 12549, 12551, 12553,
            12555, 12557, 12559, 12861, 12899, 12912, 12913, 12937, 12939, 12941, 12942, 12960,
            12962, 17306, 18218, 18221, 18223, 18224, 18236, 18237, 18241, 18245, 18250, 19459,
            24290, 24430,
            # LEVEL START / results buttons and toolbar tabs (drawn as 3D textures)
            12900, 12916, 12918, 12920, 12922, 12925, 12929, 12933, 12935, 12950, 12952, 12954,
            12957, 12963, 18235, 18243, 18248, 18249, 18251, 18252, 24120, 26648, 26650}
LEVEL_BACKGROUNDS = range(8340, 8369)   # scenery: deserts, walls... keep their colours


def is_ui_image(i, w, h):
    if i in LEVEL_BACKGROUNDS:
        return False
    return i < 1000 or i >= 28500 or w >= 96 or i in MENU_BUTTONS or i in EXTRA_UI


UI_IMAGES = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'ui_images.txt')


def apply(p):
    n = 0
    for i in NCLR:
        d = bytearray(p.get(i)[0])
        k = d.find(b'TTLP')
        _, _, size, off = struct.unpack_from('<IIII', d, k + 8)
        a = k + 8 + off
        cols = list(struct.unpack_from('<%dH' % (size // 2), d, a))
        new = _swap(cols)
        if i in HUD_HEAD_NCLR:
            for r in HUD_HEAD_ROWS:
                new[r * 16:r * 16 + 16] = [HUD_HEAD_MAP.get(c, c) for c in new[r * 16:r * 16 + 16]]
        if new != cols:
            struct.pack_into('<%dH' % len(new), d, a, *new); p.set(i, bytes(d)); n += 1
    for i in RAW_PALETTES:
        d, _ = p.get(i)
        cols = list(struct.unpack_from('<256H', d, 0))
        new = _swap(cols)
        if new != cols:
            p.set(i, struct.pack('<256H', *new)); n += 1
    for i in SHORT_PALETTES:
        d, _ = p.get(i)
        cols = list(struct.unpack_from('<%dH' % (len(d) // 2), d, 0))
        new = _swap(cols)
        if new != cols:
            p.set(i, struct.pack('<%dH' % len(new), *new)); n += 1
    # the shared title/top-screen palette: reskin its original UI slots
    d = p.get(titlegen.PALETTE)[0]
    cols = list(struct.unpack_from('<256H', d, 0))
    new = _swap(cols[:titlegen.FIRST_FREE_SLOT]) + cols[titlegen.FIRST_FREE_SLOT:]
    if new != cols:
        p.set(titlegen.PALETTE, struct.pack('<256H', *new)); n += 1
    ids = [int(x) for x in open(UI_IMAGES).read().split()]
    for i in ids:
        d, _ = p.get(i)
        pr = img.parse(d)
        if not pr or not is_ui_image(i, pr[1], pr[2]):
            continue
        new = _swap(pr[0])
        if new != pr[0]:
            p.set(i, img.set_palette(d, new)); n += 1
    return n
