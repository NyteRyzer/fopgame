import struct, sys, os, collections
import ndspy.lz10 as lz10
idx=open(sys.argv[1],'rb').read(); pak=open(sys.argv[2],'rb').read(); out=sys.argv[3]
n=struct.unpack_from('<I',idx,0)[0]
offs=struct.unpack_from('<%dI'%(n+1),idx,4)
print(n, offs[-1], len(pak))
os.makedirs(out,exist_ok=True)
kinds=collections.Counter(); ok=0
for i in range(n):
    b=pak[offs[i]:offs[i+1]]
    try: d=lz10.decompress(b); ok+=1
    except Exception as e: d=b
    open(f"{out}/{i:05d}.bin",'wb').write(d)
    kinds[bytes(d[:4])]+=1
print('lz ok',ok); print(kinds.most_common(30))
