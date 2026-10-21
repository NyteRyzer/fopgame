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
    'f8f068': 'ecd4fa', 'f8f8a8': 'f4e8fc', 'f0d040': 'c8a0e8',
    'd8f020': '80d850', 'a8d820': '58b838', 'd0f840': '90e060',    # lime accents
}.items()}

# 256-colour palettes of the menu / HUD backgrounds that use the UI colours
RAW_PALETTES = [745, 748, 749, 750, 751, 752, 753, 754, 755, 756, 757, 758, 759, 760, 761, 765, 766,
                767, 924, 931, 993, 26869, 30350, 31696, 31698, 31727, 31739, 31802, 31814, 31820]
NCLR = [743, 762, 763, 764, 923, 962, 964, 967, 968, 995, 996, 29061, 29967, 31817, 33322]


def _swap(colours):
    return [MAP.get(c & 0x7fff, c & 0x7fff) | (c & 0x8000) for c in colours]


def is_ui_image(i, w, h):
    return i < 1000 or i >= 28500 or w >= 96


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
        if new != cols:
            struct.pack_into('<%dH' % len(new), d, a, *new); p.set(i, bytes(d)); n += 1
    for i in RAW_PALETTES:
        d, _ = p.get(i)
        cols = list(struct.unpack_from('<256H', d, 0))
        new = _swap(cols)
        if new != cols:
            p.set(i, struct.pack('<256H', *new)); n += 1
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
