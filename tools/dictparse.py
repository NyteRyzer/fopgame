import struct
def parse(d):
    n=d[0]; alpha=d[1:1+n]
    cnt=struct.unpack_from('<I',d,1+n)[0]
    tbl=struct.unpack_from('<%dI'%(n*n),d,5+n)
    p=5+n+4*n*n
    recs=[]
    while p<len(d) and d[p]!=0:
        L=d[p]; sl=d[p+1]; name=d[p+2:p+2+sl]; q=p+2+sl
        idx=struct.unpack_from('<I',d,q)[0]; k=d[q+4]; q+=5
        ms=[d[q+6*i:q+6*i+6] for i in range(k)]
        assert 2+sl+5+6*k==L, (hex(p),L,sl,k,name)
        recs.append((p,name,idx,ms)); p+=L
    return alpha,cnt,tbl,recs

def build(alpha, recs):
    """recs: list of (name, idx, rest_bytes) sorted by name. Returns (bytes, offsets list)."""
    n=len(alpha)
    body=bytearray(); offs=[]
    base=5+n+4*n*n
    for name,idx,rest in recs:
        offs.append(base+len(body))
        L=2+len(name)+4+len(rest)
        assert L<256
        body+=bytes([L,len(name)])+name+struct.pack('<I',idx)+rest
    tbl=[0]*(n*n)
    for o,(name,_,_) in zip(offs,recs):
        a=alpha.index(name[0]); b=alpha.index(name[1])
        if tbl[a*n]==0: tbl[a*n]=o
        if tbl[a*n+b]==0: tbl[a*n+b]=o
    out=bytes([n])+alpha+struct.pack('<I',len(recs))+struct.pack('<%dI'%(n*n),*tbl)+body
    return out, offs

def rest_of(d, p):
    L=d[p]; sl=d[p+1]
    return d[p+2+sl+4:p+L]
