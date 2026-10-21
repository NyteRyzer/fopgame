import sys, os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy'); os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
from desmume.emulator import DeSmuME
emu = DeSmuME(); emu.open(sys.argv[1])
for _ in range(int(sys.argv[3])): emu.cycle(with_joystick=False)
m = emu.memory.unsigned
open(sys.argv[2], 'wb').write(bytes(m[0x02000000:0x02400000]))
