"""Fairly OddParents rewrite rules for the game's text."""
import re

LINE_MAX = 32  # widest centred ('ci...ic') line the original text uses

# Applied to every language: character and title names.
NAMES = [
    (rb'SUPER SCRIBBLENAUTS', b'FAIRLY ODDPARENTS'),
    (rb"MAXWELL'S", b"TIMMY'S"),
    (rb'MAXWELLS', b'TIMMYS'),
    (rb'MAXWELL', b'TIMMY'),
]

# English only. Each entry: (pattern, preferred replacement, shorter fallback).
ENGLISH = [
    # the title is split across two lines in a couple of messages
    (rb'(WELCOME TO|WORD THAT) SUPER(?=ic$)', rb'\1 FAIRLY', rb'\1 FAIRLY'),
    (rb'SCRIBBLENAUTS 2', b'FAIRLY ODDPARENTS', b'ODDPARENTS'),
    (rb'SECRET FAIRLY ODDPARENTS ADJECTIVE', b'SECRET MAGIC WORDS ADJECTIVE', b'SECRET MAGIC ADJECTIVE'),
    (rb'STARITE GET', b'WISH GRANTED', b'GOT A WISH'),
    (rb'STARITES', b'WISHES', b'WISHES'),
    (rb'STARITE', b'WISH', b'WISH'),
    (rb'SCRIBBLENAUTS(?!\.COM)', b'ODDPARENTS', b'ODDPARENTS'),
    (rb'(?<![A-Z])SCRIBBLENAUT(?![A-Z.])', b'GODCHILD', b'GODCHILD'),
    (rb'(?<![A-Z])OLLARS', b'FAIRY BUCKS', b'BUCKS'),
    (rb'(?<![A-Z])OLLAR(?![A-Z])', b'FAIRY BUCK', b'BUCK'),
]


def _apply(s, rules, short):
    for pat, *reps in rules:
        s = re.sub(pat, reps[-1] if short else reps[0], s)
    return s


def rewrite(s, english):
    """Rewrite one line, keeping it no wider than the original or LINE_MAX."""
    width = max(visible_len(s), LINE_MAX)
    out = _apply(s, NAMES, False)
    if english:
        long = _apply(out, ENGLISH, False)
        if visible_len(long) <= width:
            return long
        out = _apply(out, ENGLISH, True)
    return out


def visible_len(s):
    """Length without the lowercase formatting tags ('ci', 'ic', 'mc', ...)."""
    return len(s.strip(b'abcdefghijklmnopqrstuvwxyz'))

