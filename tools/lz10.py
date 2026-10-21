"""LZ10 (Nintendo LZ77 type 0x10) compressor with optimal parsing and exact-size output."""
import struct

MIN_LEN, MAX_LEN, MAX_DISP = 3, 18, 4096


def _matches(data):
    """For each position, the longest match (length, disp)."""
    n = len(data)
    best = [(0, 0)] * n
    heads = {}
    for i in range(n):
        if i + MIN_LEN <= n:
            key = data[i:i + MIN_LEN]
            bl, bd = 0, 0
            for j in reversed(heads.get(key, ())):
                d = i - j
                if d > MAX_DISP:
                    break
                if d < 2:  # the original data never uses distance 1 (VRAM-safe)
                    continue
                L = MIN_LEN
                while L < MAX_LEN and i + L < n and data[j + L] == data[i + L]:
                    L += 1
                if L > bl:
                    bl, bd = L, d
                    if L == MAX_LEN:
                        break
            best[i] = (bl, bd)
            heads.setdefault(key, []).append(i)
    return best


def _parse(data):
    """Token list minimising size: ('L', byte) or ('R', length, disp)."""
    n = len(data)
    best = _matches(data)
    INF = 1 << 60
    # cost in bits: literal 9, reference 17
    cost = [INF] * (n + 1); cost[n] = 0
    choice = [None] * (n + 1)
    for i in range(n - 1, -1, -1):
        cost[i] = cost[i + 1] + 9; choice[i] = ('L',)
        bl, bd = best[i]
        for L in range(MIN_LEN, bl + 1):
            c = cost[i + L] + 17
            if c < cost[i]:
                cost[i] = c; choice[i] = ('R', L, bd)
    toks, i = [], 0
    while i < n:
        ch = choice[i]
        if ch[0] == 'L':
            toks.append(('L', data[i])); i += 1
        else:
            toks.append(ch); i += ch[1]
    return toks


def _emit(n, toks):
    out = bytearray(struct.pack('<I', 0x10 | n << 8))
    for k in range(0, len(toks), 8):
        group = toks[k:k + 8]
        flags = 0
        body = bytearray()
        for b, t in enumerate(group):
            if t[0] == 'L':
                body.append(t[1])
            else:
                flags |= 0x80 >> b
                L, d = t[1] - 3, t[2] - 1
                body += bytes([(L << 4) | (d >> 8), d & 0xff])
        out.append(flags); out += body
    return bytes(out)


def _size(toks):
    return 4 + (len(toks) + 7) // 8 + sum(1 if t[0] == 'L' else 2 for t in toks)


def compress(data, size=None):
    """Compress; with size, return exactly that many bytes by de-optimising some references.

    Available de-optimisations and their (token, byte) deltas:
      A  ref(L>=4) -> literal + ref(L-1)   (+1, +1)
      B  ref(3)    -> 3 literals           (+2, +1)
      C  ref(L>=6) -> ref(3) + ref(L-3)    (+1, +2)
    """
    toks = _parse(data)
    if size is None:
        return _emit(len(data), toks)
    try:
        return _pad(data, list(toks), size)
    except LookupError:
        return _exact(data, size)


def _exact(data, size):
    """Dynamic programme over (position, tokens mod 8) with bitsets of reachable byte totals."""
    n = len(data); best = _matches(data); target = size - 4
    mask = (1 << (target + 1)) - 1
    # R[i][m]: bit f set if bytes f (flag bytes + token bytes) can encode data[i:] with T%8 == m now
    R = [[0] * 8 for _ in range(n + 1)]
    R[n] = [1] * 8
    for i in range(n - 1, -1, -1):
        bl = best[i][0]
        for m in range(8):
            nxt = (m + 1) & 7; f = 1 if m == 0 else 0
            acc = R[i + 1][nxt] << (1 + f)
            for L in range(MIN_LEN, bl + 1):
                acc |= R[i + L][nxt] << (2 + f)
            R[i] [m] = acc & mask
    if not R[0][0] >> target & 1:
        raise ValueError('cannot hit %d exactly' % size)
    toks, i, m, need = [], 0, 0, target
    while i < n:
        nxt = (m + 1) & 7; f = 1 if m == 0 else 0
        if need - 1 - f >= 0 and R[i + 1][nxt] >> (need - 1 - f) & 1:
            toks.append(('L', data[i])); i += 1; need -= 1 + f
        else:
            bl, bd = best[i]
            for L in range(bl, MIN_LEN - 1, -1):
                if need - 2 - f >= 0 and R[i + L][nxt] >> (need - 2 - f) & 1:
                    toks.append(('R', L, bd)); i += L; need -= 2 + f; break
            else:
                raise AssertionError('reconstruction failed')
        m = nxt
    out = _emit(n, toks)
    assert len(out) == size
    return out


def _pad(data, toks, size):
    T = len(toks); B = _size(toks) - 4 - (T + 7) // 8
    if 4 + (T + 7) // 8 + B > size:
        raise ValueError('compressed %d > target %d' % (_size(toks), size))
    refs = [k for k, t in enumerate(toks) if t[0] == 'R']
    nA = sum(1 for k in refs if toks[k][1] >= 4); nB = len(refs) - nA
    nC = sum(1 for k in refs if toks[k][1] >= 6)
    plan = None
    for total in range(0, 4 * (size - _size(toks)) + 16):
        for c in range(0, total + 1):
            for bb in range(0, total - c + 1):
                aa = total - c - bb
                if aa + c > nA or bb > nB or c > nC:
                    continue
                t2, b2 = T + aa + 2 * bb + c, B + aa + bb + 2 * c
                if 4 + (t2 + 7) // 8 + b2 == size:
                    plan = (aa, bb, c); break
            if plan: break
        if plan: break
    if plan is None:
        raise LookupError(size)
    aa, bb, c = plan
    pos, starts = 0, []
    for t in toks:
        starts.append(pos); pos += 1 if t[0] == 'L' else t[1]
    out = []
    for t, p in zip(toks, starts):
        if t[0] == 'R':
            _, L, d = t
            if c and L >= 6:
                out += [('R', 3, d), ('R', L - 3, d)]; c -= 1; continue
            if aa and L >= 4:
                out += [('L', data[p]), ('R', L - 1, d)]; aa -= 1; continue
            if bb and L == 3:
                out += [('L', x) for x in data[p:p + 3]]; bb -= 1; continue
        out.append(t)
    res = _emit(len(data), out)
    assert len(res) == size
    return res


def decompress(b):
    n = struct.unpack_from('<I', b, 0)[0] >> 8
    out = bytearray(); i = 4
    while len(out) < n:
        flags = b[i]; i += 1
        for k in range(8):
            if len(out) >= n:
                break
            if flags & (0x80 >> k):
                L = (b[i] >> 4) + 3; d = ((b[i] & 15) << 8 | b[i + 1]) + 1; i += 2
                for _ in range(L):
                    out.append(out[-d])
            else:
                out.append(b[i]); i += 1
    return bytes(out)
