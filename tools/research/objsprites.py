"""Find the sprite images an object's definition uses (by subtracting images shared with common objects)."""
import struct, os
from dictparse import parse
import img

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_d = open(BASE + '/pak/24063.bin', 'rb').read()
_, _, _, _recs = parse(_d)
BY = {x[1]: x for x in _recs}
IMGS = set(int(x) for x in open(BASE + '/img_ids.txt').read().split())
_cache = {}


def defid(word):
    return struct.unpack_from('<H', BY[word.encode()][3][0], 0)[0]


def refs(word):
    if word not in _cache:
        od = open(BASE + '/pak/%05d.bin' % defid(word), 'rb').read()
        _cache[word] = {struct.unpack_from('<H', od, i)[0] for i in range(len(od) - 1)} & IMGS
    return _cache[word]


COMMON = None


def sprites(word):
    global COMMON
    if COMMON is None:
        COMMON = set()
        for w in ('BOY', 'ZOMBIE', 'GIRL', 'TEACHER', 'DOG', 'MOM', 'NERD', 'BULLY', 'APPLE', 'CAR', 'TREE'):
            COMMON |= refs(w)
    out = []
    for i in sorted(refs(word) - COMMON):
        p = img.parse(open(BASE + '/pak/%05d.bin' % i, 'rb').read())
        if p and p[1] * p[2] >= 24 * 24:
            out.append(i)
    return out
