import sys, struct, subprocess, re
ELEM=24016
def load(f):
    raw=open(f,"rb").read()
    out=subprocess.check_output(["readelf","-SW",f]).decode()
    m=re.search(r"\.data\s+PROGBITS\s+(\w+)\s+(\w+)\s+(\w+)", out)
    off=int(m.group(2),16); size=int(m.group(3),16); return raw[off:off+size]
def regs(d,start):
    ent=[struct.unpack_from("<HHI",d,start+i*8) for i in range(3000)]
    while ent and ent[-1]==(0,0,0): ent.pop()
    pad,at,dt,dl=struct.unpack_from("<IIII",d,start+24000)
    return ent,(pad,at,dt,dl)
INIT=0x9f70; RES=0x5c0d4; OUT=0xae238
def info(d):
    name=d[8:40].split(b"\0")[0].decode(); slave,freq,at=struct.unpack_from("<III",d,40)
    idreg,sid=struct.unpack_from("<HH",d,0x38)
    return name,slave,idreg,sid
def modes(d):
    n=struct.unpack_from("<I",d,OUT-4)[0]; r=[]
    for k in range(n):
        o=OUT+k*96
        x,y,llp,fll=struct.unpack_from("<HHHH",d,o)
        pclk,binf=struct.unpack_from("<II",d,o+12)
        minfps,maxfps=struct.unpack_from("<dd",d,o+24+0) if False else (struct.unpack_from("<d",d,o+0x1c-4)[0], struct.unpack_from("<d",d,o+0x24)[0])
        r.append(dict(x=x,y=y,llp=llp,fll=fll,pclk=pclk,bin=binf,raw=d[o:o+96].hex()))
    return r
if __name__=="__main__":
    d=load(sys.argv[1]); print(info(d))
    e,t=regs(d,INIT); print("init",len(e),t)
    ms=modes(d)
    for k,m in enumerate(ms):
        e,t=regs(d,RES+k*ELEM); print("mode",k,{a:b for a,b in m.items() if a!="raw"},"regs",len(e),t, "fps=%.2f"%(m["pclk"]/(m["llp"]*m["fll"]) if m["llp"] else 0))
    if len(sys.argv)>2:
        k=sys.argv[2]
        e,t=regs(d,INIT if k=="init" else RES+int(k)*ELEM)
        for r,v,dl in e: print("0x%04x 0x%04x %d"%(r,v,dl))
