import sys,json,re,cv2,numpy as np,pypdfium2 as p
sys.path.insert(0,"/workspace/kern_check")
import step1
repo,piece,page,sidx=sys.argv[1],sys.argv[2],int(sys.argv[3]),[int(x) for x in sys.argv[4:]]
R=[r for r in json.load(open("/workspace/kern_check/step1_raw.json")) if r["piece"]==piece and r["repo"].startswith(repo)][0]
base=sum(len(x) for x in R["scan_pages"][:page])
d=p.PdfDocument(f"/workspace/extra_scores/kern/{R['repo']}/reference-edition/{piece}.pdf")
img=step1.render(None,d[page]);img2,a=step1.deskew(img)
an=step1.analyse(img)
print("scan page systems",len(an["systems"]),"krn global idx base",base)
# krn segments
segs=[[]];
for ln in open(f"/workspace/extra_scores/kern/{R['repo']}/kern/{piece}.krn",encoding="utf-8"):
    ln=ln.rstrip("\n")
    if (ln.startswith("!!LO:LB") or ln.startswith("!!LO:PB")) and "g=original" in ln:
        segs.append([]);continue
    if ln.startswith("!!!") : continue
    segs[-1].append(ln)
for s in sidx:
    sy=an["systems"][s]
    cv2.imwrite(f"/workspace/kern_check/crop_{piece}_p{page}_s{s}.png",img2[max(0,sy["top"]-60):sy["bot"]+60])
    g=base+s
    print(f"=== {piece} page{page} sys{s} global {g} measures_krn(raw bars {sy['raw']})")
    seg=segs[g]
    ms=[];cur=None
    for l in seg:
        c=l.split("\t")
        if c[0].startswith("="):
            cur=[c[0],[[] for _ in range(6)],[]]; ms.append(cur); continue
        if cur is None: 
            if l.startswith("*"): print("  ",";".join(x for x in c[:2]))
            continue
        if l.startswith("*"):
            if any(x not in ("*","*v") and not x.startswith("*^") for x in c[:3]): cur[2].append(";".join(c[:3]))
            elif "*^" in c or "*v" in c: cur[2].append("split/merge "+" ".join(c[:3]))
            continue
        for i,x in enumerate(c[:6]):
            if x!=".": cur[1][i].append(x)
    for m in ms:
        print(m[0],"| INTERP:",m[2])
        for i,col in enumerate(m[1]):
            if col: print("   c%d: %s"%(i," ".join(col)))
