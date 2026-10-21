import sys, os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy'); os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
from desmume.emulator import DeSmuME
from PIL import Image
emu = DeSmuME(); emu.open(sys.argv[1]); emu.savestate.load_file(sys.argv[2])
for _ in range(3): emu.cycle(with_joystick=False)
emu.screenshot().save(sys.argv[3])
