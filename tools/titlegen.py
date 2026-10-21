"""New Fairly OddParents title screen (top screen BG layers).

Sub-engine BG0..BG2, 8bpp, one shared tile block (entry 24342) and palette (entry 24344):
  BG0 gingham  map 24339 (32x32)
  BG1 logo     map 24343 (32x24)
  BG2 pegasus  map 27467 (32x32), absolute tile numbers (the pegasus tiles follow the logo's)
"""
import struct
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import img

TILES_A, MAP_GINGHAM, MAP_LOGO = 24342, 24339, 24343
MAP_CHARS = 27467
PALETTE = 24344

FONT = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
INK = (40, 20, 40)

# gingham recolour to the mockup's cream / soft green
GINGHAM = {(192, 232, 192): (238, 240, 200), (144, 200, 192): (200, 226, 160)}


def _text(draw_on, xy, s, size, fill, outline=INK, width=3, shadow=True):
    f = ImageFont.truetype(FONT, size)
    layer = Image.new('L', draw_on.size, 0)
    ImageDraw.Draw(layer).text(xy, s, font=f, fill=255)
    layer = layer.point(lambda v: 255 if v > 110 else 0)
    ring = layer.filter(ImageFilter.MaxFilter(2 * width + 1))
    if shadow:
        sh = ring.transform(ring.size, Image.AFFINE, (1, 0, -2, 0, 1, -3))
        draw_on.paste(INK, (0, 0), sh)
    draw_on.paste(outline, (0, 0), ring)
    draw_on.paste(fill, (0, 0), layer)
    # top highlight band for a glossy look
    hi = layer.transform(layer.size, Image.AFFINE, (1, 0, 0, 0, 1, 2))
    band = Image.new('L', layer.size, 0)
    top = min(y for y in range(layer.size[1]) if any(layer.getpixel((x, y)) for x in range(0, layer.size[0], 2))) if layer.getbbox() else 0
    ImageDraw.Draw(band).rectangle((0, top, layer.size[0], top + size // 5), fill=255)
    gl = Image.composite(layer, Image.new('L', layer.size, 0), band)
    lighter = tuple(min(255, c + 60) for c in fill)
    draw_on.paste(lighter, (0, 0), Image.composite(gl, Image.new('L', layer.size, 0), hi))


def _star(d, cx, cy, r, fill):
    import math
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill, outline=INK)


def logo_image():
    im = Image.new('RGBA', (256, 192), (0, 0, 0, 0))
    _text(im, (12, 6), 'The', 14, (250, 210, 60), width=2)
    _text(im, (42, 0), 'FAIRLY', 28, (236, 90, 170), width=2)
    _text(im, (10, 28), 'ODDPARENTS', 26, (120, 200, 70), width=2)
    _text(im, (26, 60), 'MAGIC', 18, (236, 110, 190), width=2)
    _text(im, (96, 60), 'WORDS!', 18, (90, 170, 240), width=2)
    d = ImageDraw.Draw(im)
    _star(d, 16, 70, 5, (250, 210, 60))
    _star(d, 178, 70, 5, (250, 210, 60))
    _star(d, 230, 24, 9, (250, 210, 60))
    _star(d, 84, 112, 5, (250, 210, 60))
    _star(d, 176, 104, 5, (250, 210, 60))
    return im


def chars_image(timmy_png, cosmo_png, wanda_png):
    """Compose the three characters (already assembled full-body images) at 2x on the right."""
    im = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    for path, (x, y) in ((cosmo_png, (14, 84)), (wanda_png, (182, 88)), (timmy_png, (98, 80))):
        s = Image.open(path).convert('RGBA')
        s = s.resize((s.width * 2, s.height * 2), Image.NEAREST)
        im.paste(s, (x, y), s)
    return im


# ---------------------------------------------------------------------------
def _quantise(colors):
    """5-bit DS colour."""
    return tuple((c >> 3) << 3 for c in colors[:3])


MAX_TILES = 0x6800 // 64   # 416
FIRST_FREE_SLOT = 113   # slots 113..255 of the shared palette are unused (magenta) in the original


class SharedPalette(dict):
    """The title palette is shared with other top-screen tile sets (menus, level HUD), so every
    original slot keeps its index; new colours go into the free slots."""

    def __init__(self, original):
        super().__init__()
        self.cols = list(original)
        for i in range(1, FIRST_FREE_SLOT):
            c = img.rgb(original[i])
            self.setdefault(_quantise(c), i)
        self.next = FIRST_FREE_SLOT

    def __missing__(self, c):
        raise KeyError(c)

    def index(self, c):
        if c not in self:
            assert self.next < 256, 'title palette full'
            self[c] = self.next; self.cols[self.next] = img.bgr(*c); self.next += 1
        return self[c]


def encode_layer(im, palette, tiles, tile_index, tw, th):
    """Split an RGBA image into 8x8 8bpp tiles (deduplicated into `tiles`) and return its map."""
    px = im.load()
    mp = bytearray()
    for ty in range(th):
        for tx in range(tw):
            t = bytearray(64)
            for y in range(8):
                for x in range(8):
                    X, Y = tx * 8 + x, ty * 8 + y
                    if X < im.width and Y < im.height:
                        r, g, b, a = px[X, Y]
                        if a >= 128:
                            t[y * 8 + x] = palette.index(_quantise((r, g, b)))
            t = bytes(t)
            if t not in tile_index:
                tile_index[t] = len(tiles); tiles.append(t)
            mp += struct.pack('<H', tile_index[t])
    return bytes(mp)


def build(p, gingham_png, logo_png, chars_png):
    """Re-encode the three title layers into the pak. Images are 256-wide RGBA renders."""
    original = list(struct.unpack_from('<256H', p.get(PALETTE)[0], 0))
    # recolour the gingham in place so every screen that shares it gets the new look
    for i in range(1, FIRST_FREE_SLOT):
        k = _quantise(img.rgb(original[i]))
        for src, dst in GINGHAM.items():
            if k == _quantise(src):
                original[i] = img.bgr(*dst)
    palette = SharedPalette(original)
    tiles_a, idx_a = [bytes(64)], {bytes(64): 0}
    m_g = encode_layer(Image.open(gingham_png).convert('RGBA'), palette, tiles_a, idx_a, 32, 32)
    m_l = encode_layer(Image.open(logo_png).convert('RGBA'), palette, tiles_a, idx_a, 32, 24)
    tiles_b, idx_b = [bytes(64)], {bytes(64): 0}
    m_c = encode_layer(Image.open(chars_png).convert('RGBA'), palette, tiles_b, idx_b, 32, 32)
    p.set(PALETTE, struct.pack('<256H', *palette.cols))
    # BG2's map uses absolute tile numbers: the character tiles are appended after the
    # gingham+logo tiles, so shift every entry (including the blank filler) by that count.
    base = len(tiles_a)
    m_c = b''.join(struct.pack('<H', struct.unpack_from('<H', m_c, k)[0] + base) for k in range(0, len(m_c), 2))
    # menus place the sub-screen maps at 0x6800, so the shared tile block must stay below it
    assert base + len(tiles_b) <= MAX_TILES, 'title uses %d tiles (max %d)' % (base + len(tiles_b), MAX_TILES)
    p.set(TILES_A, b''.join(tiles_a) + b''.join(tiles_b))
    p.set(MAP_GINGHAM, m_g); p.set(MAP_LOGO, m_l); p.set(MAP_CHARS, m_c)
    return palette.next - FIRST_FREE_SLOT, len(tiles_a), len(tiles_b)
