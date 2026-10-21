import sys
from PIL import Image
fs=sys.argv[2:]
ims=[Image.open(f) for f in fs]
o=Image.new('RGB',(256*len(ims),384))
for i,im in enumerate(ims): o.paste(im,(256*i,0))
o.save(sys.argv[1])
