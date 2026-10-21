"""Turn a word into drive.py taps for the Scribblenauts notepad keyboard."""
import sys
rows = [('QWERTYUIOP', 34, 62), ('ASDFGHJKL', 48, 97), ('ZXCVBNM', 68, 130)]
KEYS = {}
for letters, x0, y in rows:
    for i, ch in enumerate(letters):
        KEYS[ch] = (x0 + i * 21, y)
KEYS[' '] = (158, 175)
def taps(word):
    return ';'.join('t %d %d 12' % KEYS[c] for c in word.upper())
OPEN = 'w 400;t 205 127 60;t 205 127;w 500;t 240 16 90'
SUBMIT = 't 240 175 240'
if __name__ == '__main__':
    print(';'.join([OPEN] + sum(([taps(w), 's typed_%s' % w.replace(' ', '_'), SUBMIT, 'w 200', 's spawn_%s' % w.replace(' ', '_'), 't 240 16 90'] for w in sys.argv[1:]), [])))
