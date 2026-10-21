"""Cosmo (redrawn over the Fairy Godmother sheet 8614) and Wanda (recoloured fairy sheet 7178)."""
import struct
import img
import recolor
import timmy_art
from recolor import HEX

COSMO_SHEET = 8614   # FAIRY GODMOTHER: hooded head, two arms, robe body (32 x 64)
WANDA_SHEET = 7178   # FAIRY: pigtailed head, wings, dress, limbs

# Index 3/4 are the arm colours in 8614, so the arms become white sleeves for free;
# 6/7 stay the skin tones of the hands.
COSMO_PALETTE = ['ff00ff', '000000', 'ffffff', 'f4f4f4', 'b8b8c8', '62cd41', 'e0a478', 'ffd8b0',
                 '2e9431', '1a5a1a', '31b44a', 'ffd84a', 'c08a18', 'c8e6f0', '8bb4c8', '262626']
# Timmy head palette char -> Cosmo palette char
HEAD_MAP = {'3': '8', '4': '9', 'a': '5', '8': '8', '9': '9', 'f': '5', 'd': 'a'}


COSMO_HEAD = [   # 28 x 27, drawn from the reference sheet: crown floats left, swoosh rises right
    "..1b1b1.....................",
    "..1bbb1..................11.",
    "..1ccc1................11551",
    "...111...............1155581",
    "...........11111111115588891",
    ".........1155558888888888891",
    "........15588888888888888891",
    ".......158888888888888888891",
    "......1588888888888888888891",
    ".....15888888888888888888991",
    ".....18888888888888888889911",
    "....1888889999999999988881..",
    "....18889177777777777198891.",
    "....1889177777777777777191..",
    "...11891777777777777777711..",
    "...1761772222277722222771...",
    "..17617222222272222222271...",
    "..1761722aa222722aa222271...",
    "..1761722a1222722a1222271...",
    "...1117222222272222222271...",
    ".....1772222277722222771....",
    ".....1677777771777777761....",
    ".....16777777771777777761...",
    "......167711111111117761....",
    "......16771222222222761.....",
    ".......116771111117761......",
    ".........11111111111........",
]


def cosmo_head():
    return COSMO_HEAD


def cosmo_body(w=24, h=22):
    """White shirt + black tie, belt, black trousers splitting into legs; wings at the shoulders."""
    g = [['.'] * w for _ in range(h)]
    for y in range(h):
        half = 5 + (6 * y) // (h - 1)          # widen like the robe silhouette
        x0, x1 = 12 - half, 11 + half
        for x in range(x0, x1 + 1):
            if x in (x0, x1) or y == h - 1 or (y == 0):
                c = '1'
            elif y < 10:
                c = '4' if x >= x1 - 2 else '2'
                if x in (11, 12) and 1 <= y <= 8:
                    c = '1' if y < 3 or y == 8 else 'f'   # knot, tie, tip
            elif y == 10:
                c = '1'                                  # belt
            else:
                c = 'f'
                if y >= 15 and x in (11, 12):
                    c = '1' if y == 15 else '.'          # gap between the legs
            g[y][x] = c
    # wings: small ovals outside the shoulders
    for (cx, cy) in ((2, 4), (21, 4)):
        for y in range(cy - 3, cy + 4):
            for x in range(cx - 2, cx + 3):
                if 0 <= x < w and 0 <= y < h and g[y][x] == '.':
                    dx, dy = (x - cx) / 2.6, (y - cy) / 3.6
                    d = dx * dx + dy * dy
                    if d <= 1:
                        g[y][x] = '1' if d > 0.55 else ('d' if y < cy else 'e')
    return [''.join(r) for r in g]


def cosmo(d):
    pal, w, h, off, stride, px = recolor._pixels(d)
    for y in range(0, 27):          # clear the hooded head
        for x in range(w):
            px[y][x] = 0
    for y in range(42, 64):         # clear the robe
        for x in range(w):
            px[y][x] = 0
    for r, line in enumerate(cosmo_head()):
        for c, ch in enumerate(line[:w]):
            if ch != '.':
                px[r][c] = int(ch, 16)
    for r, line in enumerate(cosmo_body()):
        for c, ch in enumerate(line[:w]):
            if ch != '.':
                px[42 + r][c] = int(ch, 16)
    pal = [img.bgr(*HEX(c)) for c in COSMO_PALETTE]
    out = bytes([16]) + struct.pack('<16H', *pal) + bytes([w, h])
    return out + recolor._pack(b'\0' * (stride * h), 0, stride, px)


# Wanda: the FAIRY sheet keeps its wings, arms and dress layout; the head is redrawn with her
# pink swirl and crown, the dress becomes a yellow top and the legs black trousers.
WANDA_PALETTE = ['ff00ff', '000000', 'c8e6f0', 'ffffff', '8bb4c8', 'f0509c', 'b02873', 'd0a010',
                 'ffdc3a', 'e0a478', 'ffd8b0', '262626', 'ffd84a', 'd0408c', 'c08a18', 'ff9ccd']
WANDA_HEAD = [   # 23 x517 at (37, 8)
    "..........11111........",
    "........1155555511.....",
    ".1c1c1.155666666551....",
    ".1ccc115561111116651...",
    ".1eee11561555555161....",
    "..111.1561566651651....",
    ".....11561511116551....",
    "....155566111166551....",
    "...1555556666665551....",
    "..1555555555555555551..",
    "..155aaaaaaaaaaaaa551..",
    "..15a333aaaaa333aaa51..",
    "...1a3d1aaaaa3d1aaa1...",
    "...1aa33aaaaaa33aa91...",
    "....19aaaa111aaaa91....",
    ".....119aaaaaaa911.....",
    ".......111111111.......",
]
WANDA_LEGS = ((9, 48, 6, 7), (21, 48, 6, 7))


def wanda(d):
    pal, w, h, off, stride, px = recolor._pixels(d)
    for y in range(8, 25):
        for x in range(37, 60):
            px[y][x] = 0
    for r, line in enumerate(WANDA_HEAD):
        for c, ch in enumerate(line[:23]):
            if ch != '.':
                px[8 + r][37 + c] = int(ch, 16)
    for (x0, y0, lw, lh) in WANDA_LEGS:          # skin legs -> black trousers
        for y in range(y0, y0 + lh):
            for x in range(x0, x0 + lw):
                if px[y][x] in (9, 10):
                    px[y][x] = 11
    pal = [img.bgr(*HEX(c)) for c in WANDA_PALETTE]
    out = bytes([16]) + struct.pack('<16H', *pal) + bytes([w, h])
    return out + recolor._pack(b'\0' * (stride * h), 0, stride, px)
