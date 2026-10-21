"""Minimal BPS patch creator/applier (byuu's format) using block matching against the source."""
import sys
import zlib

BLOCK = 32


def _num(n):
    out = bytearray()
    while True:
        x = n & 0x7f
        n >>= 7
        if n == 0:
            out.append(0x80 | x)
            return bytes(out)
        out.append(x)
        n -= 1


def _rnum(b, i):
    data, shift = 0, 1
    while True:
        x = b[i]; i += 1
        data += (x & 0x7f) * shift
        if x & 0x80:
            return data, i
        shift <<= 7
        data += shift


def create(src, dst, meta=b''):
    index = {}
    for i in range(0, len(src) - BLOCK + 1, BLOCK):
        index.setdefault(src[i:i + BLOCK], i)
    out = bytearray(b'BPS1') + _num(len(src)) + _num(len(dst)) + _num(len(meta)) + meta
    src_rel = 0
    lit_start = None
    o = 0

    def flush_lit(end):
        nonlocal lit_start
        if lit_start is not None and end > lit_start:
            out.extend(_num(((end - lit_start - 1) << 2) | 1))  # TargetRead
            out.extend(dst[lit_start:end])
        lit_start = None

    while o < len(dst):
        # SourceRead: same offset matches
        if o < len(src) and src[o] == dst[o]:
            n = 0
            while o + n < len(dst) and o + n < len(src) and src[o + n] == dst[o + n]:
                n += 1
            if n >= 8:
                flush_lit(o)
                out.extend(_num(((n - 1) << 2) | 0))
                o += n
                continue
        s = index.get(dst[o:o + BLOCK]) if o + BLOCK <= len(dst) else None
        if s is not None:
            n = BLOCK
            while o + n < len(dst) and s + n < len(src) and src[s + n] == dst[o + n]:
                n += 1
            flush_lit(o)
            out.extend(_num(((n - 1) << 2) | 2))  # SourceCopy
            d = s - src_rel
            out.extend(_num((abs(d) << 1) | (1 if d < 0 else 0)))
            src_rel = s + n
            o += n
            continue
        if lit_start is None:
            lit_start = o
        o += 1
    flush_lit(o)
    out += zlib.crc32(src).to_bytes(4, 'little') + zlib.crc32(dst).to_bytes(4, 'little')
    out += zlib.crc32(out).to_bytes(4, 'little')
    return bytes(out)


def apply(src, patch):
    assert patch[:4] == b'BPS1'
    i = 4
    ss, i = _rnum(patch, i); ts, i = _rnum(patch, i); ms, i = _rnum(patch, i); i += ms
    dst = bytearray(); src_rel = tgt_rel = 0
    end = len(patch) - 12
    while i < end:
        d, i = _rnum(patch, i)
        cmd, n = d & 3, (d >> 2) + 1
        if cmd == 0:
            dst += src[len(dst):len(dst) + n]
        elif cmd == 1:
            dst += patch[i:i + n]; i += n
        else:
            off, i = _rnum(patch, i)
            off = -(off >> 1) if off & 1 else off >> 1
            if cmd == 2:
                src_rel += off; dst += src[src_rel:src_rel + n]; src_rel += n
            else:
                tgt_rel += off
                for _ in range(n):
                    dst.append(dst[tgt_rel]); tgt_rel += 1
    assert zlib.crc32(dst) == int.from_bytes(patch[-8:-4], 'little'), 'output CRC mismatch'
    return bytes(dst)


if __name__ == '__main__':
    src, dst, out = sys.argv[1:4]
    a, b = open(src, 'rb').read(), open(dst, 'rb').read()
    p = create(a, b, b'The Fairly OddParents: Magic Words! (Super Scribblenauts USA hack)')
    assert apply(a, p) == b
    open(out, 'wb').write(p)
    print('patch', len(p), 'bytes, verified')
