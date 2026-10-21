"""Render a raw DS text background: 4bpp tiles + 32x24 u16 map + 16-colour palettes."""
import struct
from PIL import Image
import img


def render(tiles, mp, pal):
    """pal: list of 256 BGR555 colours (16 palettes x 16)."""
    im = Image.new('RGBA', (256, 192))
    px = im.load()
    for ty in range(24):
        for tx in range(32):
            e = struct.unpack_from('<H', mp, (ty * 32 + tx) * 2)[0]
            t, hf, vf, pn = e & 0x3ff, e >> 10 & 1, e >> 11 & 1, e >> 12
            for y in range(8):
                for x in range(8):
                    o = t * 32 + y * 4 + x // 2
                    if o >= len(tiles):
                        continue
                    c = (tiles[o] >> (4 * (x & 1))) & 15
                    if c:
                        X = tx * 8 + (7 - x if hf else x); Y = ty * 8 + (7 - y if vf else y)
                        px[X, Y] = img.rgb(pal[pn * 16 + c]) + (255,)
    return im
