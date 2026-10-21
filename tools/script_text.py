"""Rewrite the length-prefixed text lines in Super Scribblenauts' per-language script files."""
import re, struct

OPS = (0x0c, 0x0e, 0x0f)  # 0x0e title, 0x0f line, 0x0c last line


def is_script(d):
    if len(d) < 8:
        return False
    n = struct.unpack_from('<H', d, 0)[0]
    if not 1 <= n <= 400 or len(d) < 2 + 6 * n:
        return False
    offs = [struct.unpack_from('<HI', d, 2 + 6 * i) for i in range(n)]
    return offs[0][1] == 2 + 6 * n and all(l == i for i, (l, _) in enumerate(offs)) \
        and all(a[1] <= b[1] <= len(d) for a, b in zip(offs, offs[1:]))


def sections(d):
    n = struct.unpack_from('<H', d, 0)[0]
    offs = [struct.unpack_from('<HI', d, 2 + 6 * i)[1] for i in range(n)] + [len(d)]
    return [d[offs[i]:offs[i + 1]] for i in range(n)]


def join(secs):
    n = len(secs)
    head = bytearray(struct.pack('<H', n)); o = 2 + 6 * n
    for i, s in enumerate(secs):
        head += struct.pack('<HI', i, o); o += len(s)
    return bytes(head) + b''.join(secs)


def is_text(s):
    return len(s) >= 2 and s[:1] in (b'c', b'm') and s[-1:] in (b'c', b'm') and \
        all(32 <= c < 127 or c >= 0xc0 for c in s)


def strings(sec):
    """Yield (pos, text) for each text line in a section."""
    i = 0
    while i < len(sec) - 2:
        if sec[i] in OPS:
            L = sec[i + 1]; s = sec[i + 2:i + 2 + L]
            if len(s) == L and is_text(s):
                yield i, s
                i += 2 + L
                continue
        i += 1


def rewrite_section(sec, fn):
    out = bytearray(); last = 0
    for pos, s in strings(sec):
        new = fn(s)
        assert len(new) < 256
        out += sec[last:pos] + bytes([sec[pos], len(new)]) + new
        last = pos + 2 + len(s)
    out += sec[last:]
    return bytes(out)
