"""Constellation map top screen: replace the blueprint drawing of Maxwell with Timmy, Cosmo and Wanda.

Sub-screen 8bpp layer: tiles 27989 + map 27991 (32x24) + palette 27990 (only used by this screen).
"""
import struct
from collections import deque
from PIL import Image
import bg8
import img

TILES, PALETTE, MAP = 27989, 27990, 27991
PAPER = (0, 90, 131)
FIGURE = {(115, 164, 189), (172, 205, 213), (205, 222, 230), (255, 255, 255)}
BOX = (52, 4, 205, 188)            # Maxwell's drawing lives inside this box


def _blueprint(sprite):
    """Recolour a sprite in the blueprint style: white outline, pale blue fills."""
    out = Image.new('RGBA', sprite.size, (0, 0, 0, 0))
    src, dst = sprite.load(), out.load()
    for y in range(sprite.height):
        for x in range(sprite.width):
            r, g, b, a = src[x, y]
            if a < 128:
                continue
            lum = (r * 3 + g * 6 + b) // 10
            if lum < 40:
                c = (255, 255, 255)          # outlines
            elif lum < 75:
                c = (0, 32, 49)              # pupils and dark details
            elif lum > 200:
                c = (205, 222, 230)
            elif lum > 140:
                c = (172, 205, 213)
            else:
                c = (115, 164, 189)
            dst[x, y] = c + (255,)
    return out


def compose(original, cast):
    """original: RGBA render of the map layer. cast: [(RGBA sprite, scale, (x, y))]."""
    im = original.convert('RGBA')
    px = im.load()
    x0, y0, x1, y1 = BOX
    # flood the drawing from its centre through figure colours, then grow the mask 1px
    seen = set(); q = deque([((x0 + x1) // 2, (y0 + y1) // 2)])
    while q:
        x, y = q.popleft()
        if (x, y) in seen or not (x0 <= x < x1 and y0 <= y < y1):
            continue
        if px[x, y][:3] not in FIGURE:
            continue
        seen.add((x, y)); q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    grow = {(x + dx, y + dy) for x, y in seen for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    for x, y in grow:
        if x0 <= x < x1 and y0 <= y < y1 and px[x, y][:3] in FIGURE:
            px[x, y] = PAPER + (255,)
    # Maxwell's dark detail lines (eyes, mouth) sit inside the drawing: paint those too
    for x in range(x0, x1):
        for y in range(y0, y1):
            if px[x, y][:3] == (0, 32, 49):
                n = sum((x + dx, y + dy) in seen for dx in (-2, 0, 2) for dy in (-2, 0, 2))
                if n >= 5:
                    px[x, y] = PAPER + (255,)
    for spr, scale, (x, y) in cast:
        s = _blueprint(spr.resize((spr.width * scale, spr.height * scale), Image.NEAREST))
        im.paste(s, (x, y), s)
    return im


def encode(p, im):
    """Re-encode the layer with the existing palette (every colour used is already in it)."""
    pal = list(struct.unpack_from('<256H', p.get(PALETTE)[0], 0))
    lookup = {}
    for i, c in enumerate(pal):
        lookup.setdefault(img.rgb(c), i)
    tiles, index, mp = [bytes(64)], {bytes(64): 0}, bytearray()
    px = im.load()
    for ty in range(24):
        for tx in range(32):
            t = bytearray(64)
            for y in range(8):
                for x in range(8):
                    r, g, b, a = px[tx * 8 + x, ty * 8 + y]
                    if a >= 128:
                        t[y * 8 + x] = lookup[(r, g, b)]
            t = bytes(t)
            if t not in index:
                index[t] = len(tiles); tiles.append(t)
            mp += struct.pack('<H', index[t])
    original_tiles = len(p.get(TILES)[0]) // 64
    assert len(tiles) <= original_tiles, 'map art needs %d tiles (max %d)' % (len(tiles), original_tiles)
    p.set(TILES, b''.join(tiles)); p.set(MAP, bytes(mp))
    return len(tiles)


CAST = lambda t, c, w: [(c, 2, (24, 80)), (w, 2, (168, 88)), (t, 2, (96, 64))]  # fits the 499-tile budget


def build(p, timmy, cosmo, wanda):
    orig = bg8.render(p.get(TILES)[0], p.get(MAP)[0], p.get(PALETTE)[0])
    im = compose(orig, CAST(timmy, cosmo, wanda))
    return encode(p, im)
