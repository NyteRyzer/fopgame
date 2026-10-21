"""Build the Fairly OddParents hack of Super Scribblenauts (USA)."""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pak import Pak
from dictparse import parse, build, rest_of
import fop_words
import fop_text
import fop_story
import script_text
import recolor
import timmy_build
import fairies
import fop_assets
import titlegen
import fop_ui
import poses
import os
import tempfile

MAXWELL_PART_SHEETS = (8914, 8915, 8916)   # the in-game puppet parts
MAXWELL_ART = (8913, 32091, 32092, 32093)  # menu icon and control-scheme pictures
MAXWELL_HEAD_ICON = 242                    # 32x32 head next to SINGLE PLAYER


def string_table(d):
    """Return the lines of a 'count byte + newline-separated strings' table, or None."""
    if len(d) < 3 or d[-1:] != b'\n' or not d[0]:
        return None
    lines = d[1:-1].split(b'\n')
    if len(lines) % d[0] or len(lines) // d[0] > 12:
        return None
    if not all(all(32 <= c < 127 or c >= 0xa0 for c in l) for l in lines):
        return None
    return lines


def story_for(secs, k):
    """The story objective for English message k//4, if it opens a level stage (HINT, every 3rd)."""
    m = k // 4
    parsed = script_text.message_lines(secs[k])
    if not parsed:
        return None
    key = ' '.join(l[2:-2].decode('latin1') for _, l in parsed[1])
    if parsed[0] == b'cHINTc':
        return fop_story.STORY.get(key) if m % 3 == 0 else None
    return fop_story.LINES.get(key)


def patch_text(p):
    scripts = tables = changed_lines = stories = 0
    for i in range(len(p.raw)):
        if i in (fop_words.DICT_EN, fop_words.OBJ_NAME_TABLE):
            continue
        d, _ = p.get(i)
        new = None
        if script_text.is_script(d):
            secs = script_text.sections(d)
            for k in range(0, len(secs), 4):          # English sections
                story = story_for(secs, k)
                if story:
                    new_sec = script_text.replace_message(secs[k], story)
                    if new_sec is not None:
                        secs[k] = new_sec; stories += 1
            secs = [script_text.rewrite_section(s, lambda t, en=(k % 4 == 0): fop_text.rewrite(t, en))
                    for k, s in enumerate(secs)]
            new = script_text.join(secs)
            scripts += new != d
        else:
            lines = string_table(d)
            if lines is not None:
                n = d[0]
                lines = [fop_text.rewrite(l, k < n) for k, l in enumerate(lines)]
                new = bytes([n]) + b'\n'.join(lines) + b'\n'
                tables += new != d
        if new is not None and new != d:
            p.set(i, new)
    print('text: %d scripts, %d string tables rewritten, %d story missions' % (scripts, tables, stories))


def patch_dictionary(p):
    d, _ = p.get(fop_words.DICT_EN)
    alpha, _, _, recs = parse(d)
    by_name = {nm: (pos, idx) for pos, nm, idx, _ in recs}
    entries = [(nm, idx, rest_of(d, pos), pos) for pos, nm, idx, _ in recs]
    for new, target in fop_words.ALIASES.items():
        nb, tb = new.encode('latin1'), target.encode('latin1')
        if nb in by_name:
            print('  skip (already a word):', new)
            continue
        assert all(c in alpha for c in nb), new
        pos, idx = by_name[tb]
        # Reuse the target's word id so per-word bookkeeping treats them as one word.
        entries.append((nb, idx, rest_of(d, pos), None))
    entries.sort(key=lambda e: e[0])
    out, offs = build(alpha, [e[:3] for e in entries])
    remap = {e[3]: o for e, o in zip(entries, offs) if e[3] is not None}
    p.set(fop_words.DICT_EN, out + b'\x00')
    # Object id -> name-record offsets must follow the records they point at.
    t, _ = p.get(fop_words.OBJ_NAME_TABLE)
    n = len(t) // 4
    vals = [remap[v] if v else 0 for v in struct.unpack_from('<%dI' % n, t, 0)]
    p.set(fop_words.OBJ_NAME_TABLE, struct.pack('<%dI' % n, *vals) + t[4 * n:])
    print('dictionary: %d -> %d words' % (len(recs), len(entries)))


def patch_sprites(p):
    timmy = timmy_build.encode(timmy_build.sheet())
    for i in MAXWELL_PART_SHEETS:
        p.set(i, timmy)
    for i in MAXWELL_ART:
        p.set(i, recolor.timmy(p.get(i)[0]))
    p.set(MAXWELL_HEAD_ICON, timmy_build.head_icon())
    p.set(recolor.MENU_ICON, recolor.timmy_menu_icon(p.get(recolor.MENU_ICON)[0]))
    p.set(fairies.COSMO_SHEET, fairies.cosmo(p.get(fairies.COSMO_SHEET)[0]))
    p.set(fairies.WANDA_SHEET, fairies.wanda(p.get(fairies.WANDA_SHEET)[0]))
    n = fop_assets.apply(p)
    print('sprites: Timmy parts + %d recoloured pictures, Cosmo, Wanda, %d asset recolours' % (len(MAXWELL_ART), n))


def patch_title(p):
    """Top screen of the title: FOP logo, Timmy/Cosmo/Wanda, cream-and-green gingham."""
    import bg8
    from PIL import Image
    tmp = tempfile.mkdtemp()
    pal = p.get(titlegen.PALETTE)[0]
    g = bg8.render(p.get(titlegen.TILES_A)[0], p.get(titlegen.MAP_GINGHAM)[0], pal)
    px = g.load()
    for y in range(g.height):
        for x in range(g.width):
            if px[x, y][3]:
                k = px[x, y][:3]
                best = min(titlegen.GINGHAM, key=lambda a: sum(abs(i - j) for i, j in zip(a, k)))
                px[x, y] = titlegen.GINGHAM[best] + (255,)
    g.save(os.path.join(tmp, 'g.png'))
    titlegen.logo_image().save(os.path.join(tmp, 'l.png'))
    poses.timmy().save(os.path.join(tmp, 't.png'))
    poses.cosmo(p.get(fairies.COSMO_SHEET)[0]).save(os.path.join(tmp, 'c.png'))
    poses.wanda(p.get(fairies.WANDA_SHEET)[0]).save(os.path.join(tmp, 'w.png'))
    titlegen.chars_image(*(os.path.join(tmp, f) for f in ('t.png', 'c.png', 'w.png'))).save(os.path.join(tmp, 'ch.png'))
    n = titlegen.build(p, *(os.path.join(tmp, f) for f in ('g.png', 'l.png', 'ch.png')))
    print('title: %d new colours, %d logo/gingham tiles, %d character tiles' % n)


def main(src, dst):
    p = Pak(src)
    patch_dictionary(p)
    patch_text(p)
    patch_sprites(p)
    patch_title(p)
    print('ui: %d palettes/images reskinned' % fop_ui.apply(p))
    p.save(dst)
    print('wrote', dst)


if __name__ == '__main__':
    main(*sys.argv[1:3])
