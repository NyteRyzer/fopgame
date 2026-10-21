"""Log which pak entries the game looks up in the 1i table (read watchpoint), per frame."""
import sys, os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy'); os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
from desmume.emulator import DeSmuME
BASE = int(sys.argv[3], 16)
emu = DeSmuME(); emu.open(sys.argv[1])
frame = [0]; log = []
def cb(addr, size):
    i = (addr - BASE - 4) // 4
    if 0 <= i < 33384:
        log.append((frame[0], i))
emu.memory.register_read(BASE, cb, 133540)
taps = {}
for t in sys.argv[5].split(';') if len(sys.argv) > 5 else []:
    f, x, y = map(int, t.split(',')); taps[f] = (x, y)
for f in range(int(sys.argv[4])):
    frame[0] = f
    if f in taps: emu.input.touch_set_pos(*taps[f])
    if f - 4 in taps: emu.input.touch_release()
    emu.cycle(with_joystick=False)
seen = []
for f, i in log:
    if not seen or seen[-1][1] != i:
        seen.append((f, i))
open(sys.argv[2], 'w').write('\n'.join('%d %d' % x for x in seen))
print(len(log), len(seen))
