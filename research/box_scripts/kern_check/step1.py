import sys, os, re, json, glob, csv
import numpy as np, cv2
import pypdfium2 as pdfium
ROOT="/workspace/extra_scores/kern"
OUT="/workspace/kern_check"
REPOS=["mozart-piano-sonatas","chopin-mazurkas","beethoven-piano-sonatas"]
DPI=150

def render(pdf, page):
    return np.array(page.render(scale=DPI/72).to_pil().convert("L"))

def groups(mask):
    """runs of True -> list of (start,end)"""
    out=[];s=None
    for i,v in enumerate(mask):
        if v and s is None: s=i
        if not v and s is not None: out.append((s,i-1)); s=None
    if s is not None: out.append((s,len(mask)-1))
    return out

def deskew(img):
    H,W=img.shape
    sm=cv2.resize(255-img,(W//2,H//2),interpolation=cv2.INTER_AREA)
    best=(-1,0)
    for a in np.arange(-2.0,2.01,0.1):
        M=cv2.getRotationMatrix2D((sm.shape[1]/2,sm.shape[0]/2),a,1)
        r=cv2.warpAffine(sm,M,(sm.shape[1],sm.shape[0]))
        v=np.var(np.diff(r.sum(axis=1).astype(np.float64)))
        if v>best[0]: best=(v,a)
    a=best[1]
    M=cv2.getRotationMatrix2D((W/2,H/2),a,1)
    return cv2.warpAffine(img,M,(W,H),flags=cv2.INTER_CUBIC,borderValue=255),a

def analyse(img):
    img,ang=deskew(img)
    H,W=img.shape
    B=(img<150).astype(np.uint8)
    kh=max(40,int(0.04*H))
    Bd=cv2.dilate(B,np.ones((1,3),np.uint8))
    V=cv2.morphologyEx(Bd,cv2.MORPH_OPEN,np.ones((kh,1),np.uint8))
    Vb_=cv2.morphologyEx(Bd,cv2.MORPH_OPEN,np.ones((int(0.3*H),1),np.uint8))
    V[:,Vb_.any(axis=0)]=0
    V[:,:int(0.03*W)]=0
    left=V[:,:int(0.3*W)].any(axis=1)
    gs=groups(left)
    # merge groups with small gaps
    mg=[]
    for s_,e_ in gs:
        if mg and s_-mg[-1][1]<=15: mg[-1]=(mg[-1][0],e_)
        else: mg.append((s_,e_))
    mg=[g for g in mg if g[1]-g[0]>=kh]
    kwb=max(30,int(0.05*W))
    Hl2=cv2.morphologyEx(B,cv2.MORPH_OPEN,np.ones((1,kwb),np.uint8))
    Bn_all=B&(1-cv2.dilate(Hl2,np.ones((3,1),np.uint8)))
    res=[]
    for top,bot in mg:
        h=bot-top+1
        u=h/13.5
        band=V[top:bot+1,:int(0.3*W)].any(axis=0)
        xs=np.where(band)[0]; x0=int(xs.min())
        crop=B[top:bot+1,:]
        cr=cv2.dilate(crop,np.ones((1,5),np.uint8))
        Vb=cv2.erode(cr,np.ones((int(0.85*h),1),np.uint8))
        cols=np.where(Vb.sum(axis=0)>0)[0]
        cols=[c for c in cols if c>x0+2]
        cl=[]
        for c in cols:
            if cl and c-cl[-1][-1]<=1.5*u: cl[-1].append(c)
            else: cl.append([c])
        centers=[np.mean(c) for c in cl]
        Bn=Bn_all[top:bot+1]
        bars=[];nraw=0
        for c in centers:
            if c<=x0+6*u: continue
            ci=int(c)
            L=Bn[:,max(0,ci-12):max(0,ci-4)].any(axis=1);R=Bn[:,ci+5:ci+13].any(axis=1)
            nraw+=1
            if L.mean()+R.mean()<=0.24: bars.append(c)
        res.append(dict(nstaff=2 if 11<=u*0+h/ (h/13.5)<=16 else 0,top=top,bot=bot,x0=x0,u=u,bars=len(bars),raw=nraw,hgt=h))
    return dict(nstaves=0,systems=res,W=W,H=H,angle=float(ang))

def parse_krn(path):
    segs=[0];pages=[0];page=0;cur=0
    meas=[0];pg=[0]; hasLB=hasPB=False; started=False
    for ln in open(path,encoding="utf-8",errors="replace"):
        ln=ln.rstrip("\n")
        if ln.startswith("!!LO:LB") and "g=original" in ln:
            hasLB=True
            if meas[-1]>0: meas.append(0);pg.append(page)
        elif ln.startswith("!!LO:PB") and "g=original" in ln:
            hasPB=True; page+=1
            if meas[-1]>0: meas.append(0)
            pg.append(page) if len(pg)<len(meas) else None
            pg[-1]=page
        elif ln.startswith("="):
            tok=ln.split("\t")[0]
            if re.match(r"=\d",tok) or re.match(r"=[^=]",tok) and False:
                meas[-1]+=1
    # pages list aligned to meas
    while len(pg)<len(meas): pg.append(page)
    if meas and meas[-1]==0: meas.pop();pg.pop()
    return dict(meas=meas,page=pg,hasLB=hasLB,hasPB=hasPB)

def align(S,K):
    """S scan measure counts, K krn; return best offset, matches"""
    best=(-1,0)
    n=len(K)
    for o in range(0,max(1,len(S)-n+1)) if len(S)>=n else [0]:
        m=sum(1 for a,b in zip(S[o:o+n],K) if a==b)
        if m>best[0]: best=(m,o)
    return best

if __name__=="__main__":
    results=[]
    for repo in REPOS:
        for pdf in sorted(glob.glob(f"{ROOT}/{repo}/reference-edition/*.pdf")):
            base=os.path.basename(pdf)[:-4]
            krn=f"{ROOT}/{repo}/kern/{base}.krn"
            rec=dict(repo=repo,piece=base,krn=os.path.exists(krn))
            try:
                d=pdfium.PdfDocument(pdf)
                pages=[]
                for i in range(len(d)):
                    a=analyse(render(pdf,d[i])); pages.append(a)
                rec['scan_pages']=[[ (s['bars'],s['raw'],s['hgt']) for s in p['systems']] for p in pages]
                rec['scan_nstaves']=[len(p['systems']) for p in pages]
            except Exception as e:
                rec['error']=repr(e)
            if rec['krn']:
                k=parse_krn(krn); rec['krn_meas']=k['meas'];rec['krn_page']=k['page'];rec['hasLB']=k['hasLB'];rec['hasPB']=k['hasPB']
            results.append(rec)
            print(repo,base,[len(p) for p in rec.get('scan_pages',[])],len(rec.get('krn_meas',[])),flush=True)
            json.dump(results,open(f"{OUT}/step1_raw.json","w"))
