"""Build Timmy's 64x64 parts sheet in the game's sprite format from timmy_art."""
import struct
import img, timmy_art as A
from recolor import HEX


def rows(art, w, h, name):
    out = []
    for r, line in enumerate(art):
        line = line.replace(' ', '')
        if len(line) > w:
            print('warning: %s row %d is %d wide (max %d), clipped' % (name, r, len(line), w))
        out.append(line[:w].ljust(w, '.'))
    if len(out) != h:
        print('warning: %s has %d rows (box %d)' % (name, len(out), h))
    return (out + ['.' * w] * h)[:h]


def sheet():
    px = [[0] * 64 for _ in range(64)]
    for k, (art, x, y, w, h) in enumerate(A.PARTS):
        for r, line in enumerate(rows(art, w, h, 'part%d' % k)):
            for c, ch in enumerate(line):
                if ch != '.':
                    px[y + r][x + c] = int(ch, 16)
    return px


def encode(px):
    pal = [img.bgr(*HEX(c)) for c in A.PALETTE]
    out = bytearray([16]) + struct.pack('<16H', *pal) + bytes([64, 64])
    for row in px:
        for x in range(0, 64, 2):
            out.append(row[x] | row[x + 1] << 4)
    return bytes(out)
