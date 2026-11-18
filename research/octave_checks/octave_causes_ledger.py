"""D32: how many d-type (wrong register) notes of the dev crops sit on 3+ ledger lines / after a clef change; ledger statistics of the admitted training lists."""
import json, re, sys, os
from collections import Counter
sys.path.insert(0,'/Users/yiduoke/Documents/homr/run/octave_checks')
import octave_causes_crops as O
import octave_causes_gap as G
LET='CDEFGAB'
def step(p): return int(p[1:])*7+LET.index(p[0])
def ledger(p,clef):
    s=step(p)
    if clef=='G2': top,bot=38,30
    elif clef=='F4': top,bot=26,18
    else: return 0
    if s>=top+2: return (s-top)//2
    if s<=bot-2: return (bot-s)//2
    return 0
def notes_with_ledger(tokens):
    clef={'upper':'G2','lower':'F4'}; out={'upper':[],'lower':[]}; nclef=0
    for line in tokens.strip().split('\n'):
        if line.startswith('barline'): continue
        parts=[p.split(' ') for p in line.split('&')]
        for f in parts:
            st=f[-1] if f[-1] in('upper','lower') else None
            if f[0].startswith('clef_') and st:
                if f[0][5:]!=clef[st]: nclef+=1
                clef[st]=f[0][5:]
        for f in parts:
            st=f[-1] if f[-1] in('upper','lower') else None
            if f[0].startswith('note') and len(f)>1 and st and re.match(r'^[A-G]-?\d+$',f[1]):
                out[st].append((f[1],ledger(f[1],clef[st]),clef[st]))
    return out,nclef
res=json.load(open(O.OUT+'octave_causes_notes.json'))
crops={c['name']:c for c in O.load_all()}
tot=Counter(); dl=Counter()
for r in res:
    if r['usable']!='yes' or r['pc_f1']<0.8 or not r.get('events'): continue
    lab,nclef=notes_with_ledger(crops[r['name']]['label'])
    for e in r['events']:
        if e['cls']!='d': continue
        p,l,c=lab[e['staff']][e['i']]
        dl[min(l,4)]+=1
        dl['clefchange_crop']+= nclef>0
        tot['d']+=1
print('d notes (dev crops) by ledger lines of the label note (0,1,2,3,4+):',{k:dl[k] for k in range(5)},'in crops with a clef change:',dl['clefchange_crop'],'of',tot['d'])
# all notes baseline in analysed crops
base=Counter(); 
for r in res:
    if r['usable']!='yes' or r['pc_f1']<0.8: continue
    lab,_=notes_with_ledger(crops[r['name']]['label'])
    for st in lab:
        for p,l,c in lab[st]: base[min(l,4)]+=1
print('all label notes in analysed crops by ledger lines:',{k:base[k] for k in range(5)})
print('d rate per 1000 notes by ledger lines:',{k:round(1000*dl[k]/base[k],1) for k in range(5)})
# training lists: crops with max ledger >=3 /4
for k,mem in G.members.items():
    c3=c4=n=0
    for nme in mem:
        lab,_=notes_with_ledger(G.label_text(nme)); mx=max([l for st in lab for _,l,_ in lab[st]] or [0])
        c3+=mx>=3; c4+=mx>=4; n+=1
    print(k,n,'crops with >=3 ledger lines',c3,'>=4',c4)
