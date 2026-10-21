"""8bpp tiled background (DS text BG, 256 colours): tiles + u16 map + 256-colour palette."""
import struct
from PIL import Image
import img


def render(T, M, P, tw=32):
    pal = [img.rgb(c) for c in struct.unpack_from('<256H', P, 0)]
    th = len(M) // 2 // tw
    im = Image.new('RGBA', (tw * 8, th * 8))
    px = im.load()
    for ty in range(th):
        for tx in range(tw):
            e = struct.unpack_from('<H', M, (ty * tw + tx) * 2)[0]
            t, hf, vf = e & 0x3ff, e >> 10 & 1, e >> 11 & 1
            for y in range(8):
                for x in range(8):
                    o = t * 64 + y * 8 + x
                    if o < len(T) and T[o]:
                        px[tx * 8 + (7 - x if hf else x), ty * 8 + (7 - y if vf else y)] = pal[T[o]] + (255,)
    return im
