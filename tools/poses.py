"""Assemble full-body pictures of Timmy, Cosmo and Wanda from their puppet part sheets."""
from PIL import Image
import img, timmy_build, fairies


def _crop(sheet, box):
    x, y, w, h = box
    return sheet.crop((x, y, x + w, y + h))


def _compose(parts, size):
    out = Image.new('RGBA', size, (0, 0, 0, 0))
    for im, (x, y) in parts:
        out.paste(im, (x, y), im)
    return out


def timmy(sheet_bytes=None):
    s = img.to_image(sheet_bytes or timmy_build.encode(timmy_build.sheet()))
    head, torso = _crop(s, (0, 0, 28, 25)), _crop(s, (0, 26, 15, 14))
    armf, armb = _crop(s, (19, 26, 7, 16)), _crop(s, (27, 36, 7, 15))
    leg = _crop(s, (0, 41, 8, 14))
    return _compose([(armb, (21, 22)), (leg, (7, 34)), (leg, (13, 34)), (torso, (7, 22)),
                     (armf, (4, 22)), (head, (0, 0))], (30, 50))


def cosmo(sheet_bytes):
    s = img.to_image(sheet_bytes)
    head = _crop(s, (0, 0, 28, 27)); body = _crop(s, (0, 42, 24, 22))
    arm1, arm2 = _crop(s, (6, 29, 8, 12)), _crop(s, (16, 29, 8, 12))
    return _compose([(body, (3, 24)), (arm1, (0, 26)), (arm2, (21, 26)), (head, (1, 0))], (30, 48))


def wanda(sheet_bytes):
    s = img.to_image(sheet_bytes)
    wl, wr = _crop(s, (2, 6, 14, 20)), _crop(s, (18, 6, 14, 20))
    head, dress = _crop(s, (37, 8, 23, 17)), _crop(s, (42, 38, 14, 12))
    arm = _crop(s, (8, 32, 4, 8)); leg = _crop(s, (9, 48, 6, 7))
    return _compose([(wl, (0, 10)), (wr, (18, 10)), (arm, (6, 17)), (arm, (22, 17)),
                     (leg, (8, 26)), (leg, (16, 26)), (dress, (9, 15)), (head, (5, 0))], (32, 34))
