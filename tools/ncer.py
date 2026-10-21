"""Super Scribblenauts UI sprite containers: header (u32 ncer_off, ncgr_off, nanr_off|end, end) +
Nintendo NCER (cells) / NCGR (tiles) / NANR (animation). Palettes are separate NCLR files."""
import struct
from PIL import Image
import img

SHAPES = {(0, 0): (8, 8), (0, 1): (16, 16), (0, 2): (32, 32), (0, 3): (64, 64),
          (1, 0): (16, 8), (1, 1): (32, 8), (1, 2): (32, 16), (1, 3): (64, 32),
          (2, 0): (8, 16), (2, 1): (8, 32), (2, 2): (16, 32), (2, 3): (32, 64)}


class Container:
    def __init__(self, d):
        self.d = bytearray(d)
        self.ncer_off, self.ncgr_off = struct.unpack_from('<II', d, 0)
        # NCGR: 'RGCN' header (16 bytes) then 'RAHC' section
        c = self.ncgr_off + 16
        assert d[c:c + 4] == b'RAHC', d[c:c + 4]
        self.th, self.tw, self.depth, self.mapping, self.tiled, self.tsize, toff = \
            struct.unpack_from('<HHIIIII', d, c + 8)
        self.tdata_off = c + 8 + toff
        self.bpp = 4 if self.depth == 3 else 8
        # NCER: 'RECN' header then 'KBEC'
        k = self.ncer_off + 16
        assert d[k:k + 4] == b'KBEC'
        self.ncells, self.ext = struct.unpack_from('<HH', d, k + 8)
        cell_off, self.cmap = struct.unpack_from('<II', d, k + 12)
        self.cells_at = k + 8 + cell_off
        self.cell_size = 16 if self.ext else 8
        self.oam_at = self.cells_at + self.ncells * self.cell_size

    def tiles(self):
        return self.d[self.tdata_off:self.tdata_off + self.tsize]

    def cell_objs(self, n):
        nobj, attr, ooff = struct.unpack_from('<HHI', self.d, self.cells_at + n * self.cell_size)
        out = []
        for j in range(nobj):
            a0, a1, a2 = struct.unpack_from('<HHH', self.d, self.oam_at + ooff + 6 * j)
            y = a0 & 0xff; y = y - 256 if y >= 128 else y
            x = a1 & 0x1ff; x = x - 512 if x >= 256 else x
            w, h = SHAPES[(a0 >> 14, a1 >> 14)]
            out.append(dict(x=x, y=y, w=w, h=h, tile=a2 & 0x3ff, pal=a2 >> 12,
                            hf=(a1 >> 12) & 1, vf=(a1 >> 13) & 1, bpp8=(a0 >> 13) & 1))
        return out

    def render_cell(self, n, pal):
        objs = self.cell_objs(n)
        if not objs:
            return None
        x0 = min(o['x'] for o in objs); y0 = min(o['y'] for o in objs)
        x1 = max(o['x'] + o['w'] for o in objs); y1 = max(o['y'] + o['h'] for o in objs)
        im = Image.new('RGBA', (x1 - x0, y1 - y0))
        px = im.load()
        t = self.tiles()
        unit = 32 << (self.cmap & 7)   # 1D mapping boundary
        for o in objs:
            bpp = 8 if o['bpp8'] else self.bpp
            tb = 64 if bpp == 8 else 32
            base = o['tile'] * unit
            tw = o['w'] // 8
            for ty in range(o['h'] // 8):
                for tx in range(tw):
                    toff = base + (ty * tw + tx) * tb
                    for y in range(8):
                        for x in range(8):
                            if bpp == 4:
                                b = toff + y * 4 + x // 2
                                if b >= len(t):
                                    continue
                                c = (t[b] >> (4 * (x & 1))) & 15
                                ci = o['pal'] * 16 + c
                            else:
                                b = toff + y * 8 + x
                                if b >= len(t):
                                    continue
                                c = t[b]; ci = c
                            if c and ci < len(pal):
                                X = tx * 8 + x; Y = ty * 8 + y
                                if o['hf']: X = o['w'] - 1 - X
                                if o['vf']: Y = o['h'] - 1 - Y
                                px[o['x'] - x0 + X, o['y'] - y0 + Y] = img.rgb(pal[ci]) + (255,)
        return im


def nclr(d):
    k = d.find(b'TTLP')
    depth, ext, size, off = struct.unpack_from('<IIII', d, k + 8)
    data = d[k + 8 + off:k + 8 + off + size]
    return list(struct.unpack_from('<%dH' % (len(data) // 2), data))
