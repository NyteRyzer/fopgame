import sys, os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy'); os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
from desmume.emulator import DeSmuME
emu = DeSmuME(); emu.open(sys.argv[1])
for _ in range(int(sys.argv[3])): emu.cycle(with_joystick=False)
m = emu.memory.unsigned
with open(sys.argv[2], 'wb') as f:
    for base, size in ((0x06000000, 0x80000), (0x06200000, 0x20000), (0x06400000, 0x40000), (0x06600000, 0x20000), (0x05000000, 0x800)):
        f.write(bytes(m[base:base + size]))
