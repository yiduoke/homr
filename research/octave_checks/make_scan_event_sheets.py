"""D32: by-eye evidence sheets for events of the real-scan octave attribution: page band of the system holding a predicted bar, with a text header.
usage: make_scan_event_sheets.py <outdir> <piece>:<ref_bar> ...   (ref bar number 1-based as in the audit)"""
import sys, json, re, os
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
from PIL import Image, ImageDraw
HOME=Path('/Users/yiduoke/Documents/homr/run'); E1=HOME/'eval_run1'
D=json.load(open(HOME/'octave_checks/octave_causes_realscans.json'))['events']
A=json.load(open(E1/'brace_audit_relbrace3_gpu.json'))['audit']
TAG='relbrace3_gpu'
def pages_info(piece):
    pages=sorted(((int(re.search(r'page-(\d+)',f.name).group(1)),f) for f in (E1/'testset'/TAG/piece/'page-xml').glob('page-*.musicxml')))
    out=[]  # per bar: (page, idx in page, sysindex in page, nsys on page, pos in system, n in system)
    for num,f in pages:
        r=ET.parse(f).getroot(); p=r.findall('part')[0]; ms=p.findall('measure')
        starts=[i for i,m in enumerate(ms) if m.find('print') is not None]
        if not starts or starts[0]!=0: starts=[0]+starts
        for i,m in enumerate(ms):
            s=max(k for k,x in enumerate(starts) if x<=i); a=starts[s]; b=starts[s+1] if s+1<len(starts) else len(ms)
            out.append((num,i,s,len(starts),i-a,b-a))
    return out
def sheet(piece,ref_bar,outdir):
    a=A[piece]; pairs={i:j for i,j in a['pairs']}
    j=pairs[ref_bar-1]; info=pages_info(piece)[j]
    num,i,s,ns,pos,n=info
    img=Image.open(E1/'pages'/piece/f'page-{num:02d}.png' if (E1/'pages'/piece/f'page-{num:02d}.png').exists() else sorted((E1/'pages'/piece).glob(f'*{num}.png'))[0]).convert('RGB')
    H=img.height; band=H/ns
    y0=max(0,int(s*band-0.08*band)); y1=min(H,int((s+1)*band+0.08*band))
    reg=img.crop((0,y0,img.width,y1)); W=1500; reg=reg.resize((W,int(reg.height*W/reg.width)))
    evs=[e for e in D if e['piece']==piece and e['ref_bar']==ref_bar]
    cnt=Counter((e['cause'],e['sub'][:50]) for e in evs)
    txt=[f"{piece} ref bar {ref_bar} = pred bar {j+1}: page {num}, system {s+1} of {ns} on the page, bar {pos+1} of {n} in the system",
         f"events in the bar: {dict(cnt)}",
         "examples (ref->pred, staff, d, shift ref/pred): "+'; '.join(f"{e['ref']}->{e['pred']} s{e['staff']} d{e['d']:+d} {e['sr']}/{e['sp']}" for e in evs[:8])]
    out=Image.new('RGB',(W,reg.height+60),'white'); d=ImageDraw.Draw(out)
    for k,t in enumerate(txt): d.text((4,2+18*k),t,fill=(0,0,0))
    out.paste(reg,(0,58)); fn=Path(outdir)/f'{piece}_bar{ref_bar}.png'; out.save(fn); return fn
if __name__=='__main__':
    os.makedirs(sys.argv[1],exist_ok=True)
    for a in sys.argv[2:]:
        p,b=a.rsplit(':',1); print(sheet(p,int(b),sys.argv[1]))
