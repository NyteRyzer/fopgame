"""drive.py ROM OUTPREFIX 'cmd;cmd;...'  cmds: w N (wait) | t X Y [W] (tap) | s NAME (shot) | k KEY N (hold key) | l FILE / S FILE (load/save state)"""
import sys, os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy'); os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
from desmume.emulator import DeSmuME
from desmume.controls import Keys, keymask
from PIL import Image
emu = DeSmuME(); emu.open(sys.argv[1]); pre = sys.argv[2]
def step(n=1):
    for _ in range(n): emu.cycle(with_joystick=False)
def shot(name):
    emu.screenshot().convert('RGB').save(f'{pre}_{name}.png')
for c in sys.argv[3].split(';'):
    a = c.split()
    if not a: continue
    if a[0] == 'w': step(int(a[1]))
    elif a[0] == 't':
        emu.input.touch_set_pos(int(a[1]), int(a[2])); step(4); emu.input.touch_release(); step(int(a[3]) if len(a) > 3 else 20)
    elif a[0] == 's': shot(a[1])
    elif a[0] == 'l': emu.savestate.load_file(a[1])
    elif a[0] == 'S': emu.savestate.save_file(a[1])
    elif a[0] == 'k':
        k = keymask(getattr(Keys, 'KEY_' + a[1])); emu.input.keypad_add_key(k); step(int(a[2]) if len(a) > 2 else 5); emu.input.keypad_rm_key(k); step(15)
emu.savestate.save_file(f'{pre}.dst') if hasattr(emu, 'savestate') else None
