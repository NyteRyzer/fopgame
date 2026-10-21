"""Palette/pixel recolouring of the game's 4bpp sprites (Maxwell -> Timmy, fairies -> Cosmo/Wanda)."""
import struct
import img

HEX = lambda h: (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _key(c):
    return '%02x%02x%02x' % img.rgb(c)


def _pixels(d):
    pal, w, h, bpp, off = img.parse(d)
    stride = (w * bpp + 7) // 8
    px = [[(d[off + y * stride + x // 2] >> (4 * (x & 1))) & 15 for x in range(w)] for y in range(h)]
    return pal, w, h, off, stride, px


def _pack(d, off, stride, px):
    out = bytearray(d)
    for y, row in enumerate(px):
        for x in range(0, len(row), 2):
            lo = row[x]; hi = row[x + 1] if x + 1 < len(row) else 0
            out[off + y * stride + x // 2] = lo | hi << 4
    return bytes(out)


def remap_palette(d, mapping):
    """mapping: {'rrggbb': 'rrggbb'} on 5-bit-rounded palette colours."""
    pal = img.parse(d)[0]
    new = [img.bgr(*HEX(mapping[_key(c)])) if _key(c) in mapping else c for c in pal]
    return img.set_palette(d, new)


def paint_cap(d, helmet, cap_shades, face, spike_frac=0.45):
    """Turn the dome of each helmet into a cap: helmet pixels between the spike tips and the
    top of the face become the given cap palette entries (light, dark by original shade)."""
    pal, w, h, off, stride, px = _pixels(d)
    idx = {_key(c): i for i, c in enumerate(pal)}
    hel = [idx[c] for c in helmet if c in idx]
    cap = [idx[c] for c in cap_shades if c in idx]
    fac = {idx[c] for c in face if c in idx}
    if not hel or len(cap) < 2 or not fac:
        return d
    # each column: helmet pixels above the face top in that head
    seen = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if px[y][x] in fac and not seen[y][x]:
                # flood the face to get its bounding box
                stack = [(x, y)]; xs = []; ys = []
                while stack:
                    a, b = stack.pop()
                    if 0 <= a < w and 0 <= b < h and not seen[b][a] and px[b][a] in fac:
                        seen[b][a] = True; xs.append(a); ys.append(b)
                        stack += [(a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)]
                if len(xs) < 12:
                    continue
                x0, x1, top = min(xs), max(xs), min(ys)
                hy = [b for b in range(0, top + 1) for a in range(x0 - 2, x1 + 3)
                      if 0 <= a < w and px[b][a] in hel]
                if not hy:
                    continue
                tip = min(hy); base = tip + max(1, int((top - tip) * spike_frac))
                for b in range(base, top + 1):
                    for a in range(max(0, x0 - 3), min(w, x1 + 4)):
                        if px[b][a] in hel:
                            px[b][a] = cap[0] if px[b][a] == hel[0] else cap[1]
    return _pack(d, off, stride, px)


# --- Maxwell -> Timmy -------------------------------------------------------
MAXWELL_IMAGES = [8913, 8914, 8915, 8916, 32091, 32092, 32093]
MAX_HELMET = ['b41800', '7b1000', 'ac1800']  # light, dark, (alternate red in the menu art)
MAX_SHIRT = ['b4d5de', '83acb4', '5a8ba4', '416a7b']
MAX_FACE = ['fff69c', 'eecd73']
TIMMY = {
    'b41800': '8b5a29', '7b1000': '5a3010', 'ac1800': '8b5a29',  # helmet -> brown hair
    'fff69c': 'ffdcb4', 'eecd73': 'e6b083',               # skin
    'b4d5de': 'ff9cd0', '83acb4': 'ee62a8', '5a8ba4': 'c03c83', '416a7b': '83205a',  # pink shirt/cap
    'acd520': '6a94ff', '7b9c00': '3962cd', '628300': '29418b',                      # blue pants
}


def timmy(d):
    d = paint_cap(d, MAX_HELMET, MAX_SHIRT[:2], MAX_FACE)
    return remap_palette(d, TIMMY)


# the small full-body Maxwell beside SINGLE PLAYER uses its own palette
MENU_ICON = 26808
MENU_ICON_MAP = {
    'b41800': '8b5a29', '7b1000': '5a3010',               # helmet -> brown hair
    'f6e68b': 'ffd8b0', 'b4946a': 'e0a478',               # skin
    '5a94ac': 'ee62a8', '415a7b': 'a0286a',               # shirt -> pink
    '628b00': '3962cd',                                   # shorts -> blue jeans
}


def timmy_menu_icon(d):
    d = paint_cap(d, ['b41800', '7b1000'], ['5a94ac', '415a7b'], ['f6e68b'])
    return remap_palette(d, MENU_ICON_MAP)
