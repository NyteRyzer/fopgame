import sys, os, struct
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy'); os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
from desmume.emulator import DeSmuME
emu = DeSmuME(); emu.open(sys.argv[1])
TAPS = [tuple(map(int, t.split(','))) for t in sys.argv[4].split(';')] if len(sys.argv) > 4 else [(400, 205, 127), (460, 205, 127)]
for f in range(int(sys.argv[2])):
    for (tf, x, y) in TAPS:
        if f == tf: emu.input.touch_set_pos(x, y)
        if f == tf + 4: emu.input.touch_release()
    emu.cycle(with_joystick=False)
m = emu.memory.unsigned
rd16 = lambda a: m[a] | m[a + 1] << 8
rd32 = lambda a: rd16(a) | rd16(a + 2) << 16
for eng, base in (('A', 0x04000000), ('B', 0x04001000)):
    print(eng, 'DISPCNT %08x' % rd32(base), 'BGCNT', ['%04x' % rd16(base + 8 + 2 * i) for i in range(4)],
          'HOFS', [rd16(base + 0x10 + 4 * i) & 0x1ff for i in range(4)], 'VOFS', [rd16(base + 0x12 + 4 * i) & 0x1ff for i in range(4)])
print('VRAMCNT', ['%02x' % m[0x04000240 + i] for i in range(10)])
open(sys.argv[3], 'wb').write(bytes(m[0x06000000:0x06080000]) + bytes(m[0x06200000:0x06220000]))
