"""Super Scribblenauts sprite image: u8 ncolors, ncolors*u16 BGR555, u8 w, u8 h, pixels (4bpp if ncolors<=16 else 8bpp)."""
import struct
from PIL import Image


def parse(d):
    if len(d) < 8:
        return None
    n = d[0]
    if n < 2 or len(d) < 3 + 2 * n:
        return None
    pal = list(struct.unpack_from('<%dH' % n, d, 1))
    w, h, off = d[1 + 2 * n], d[2 + 2 * n], 3 + 2 * n
    if w == 0 and len(d) >= 6 + 2 * n:   # large image: 0, u16 width, u16 height
        w, h = struct.unpack_from('<HH', d, 2 + 2 * n)
        off = 6 + 2 * n
    bpp = 4 if n <= 16 else 8
    stride = (w * bpp + 7) // 8
    if w == 0 or h == 0 or off + stride * h != len(d):
        return None
    return pal, w, h, bpp, off


def rgb(c):
    return ((c & 31) * 255 // 31, (c >> 5 & 31) * 255 // 31, (c >> 10 & 31) * 255 // 31)


def bgr(r, g, b):
    return (r * 31 // 255) | (g * 31 // 255) << 5 | (b * 31 // 255) << 10


def to_image(d):
    pal, w, h, bpp, off = parse(d)
    stride = (w * bpp + 7) // 8
    im = Image.new('RGBA', (w, h))
    px = im.load()
    for y in range(h):
        row = d[off + y * stride: off + (y + 1) * stride]
        for x in range(w):
            i = (row[x // 2] >> (4 * (x & 1))) & 15 if bpp == 4 else row[x]
            px[x, y] = (0, 0, 0, 0) if i == 0 else rgb(pal[i]) + (255,)
    return im


def set_palette(d, pal):
    n = d[0]
    assert len(pal) == n
    return d[:1] + struct.pack('<%dH' % n, *pal) + d[1 + 2 * n:]
