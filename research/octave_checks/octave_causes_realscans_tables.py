"""D32 task 2 tables from octave_causes_realscans.json."""
import json
from collections import Counter, defaultdict
D=json.load(open('/Users/yiduoke/Documents/homr/run/octave_checks/octave_causes_realscans.json'))
ev=D['events']; pp=D['per_piece']
TOT=sum(p['nref']+p['npred'] for p in pp.values())
pts=lambda n: 100*2*n/TOT
names={'a':'(a) start','b':'(b) stop','c':'(c) continuation (bracket crosses a print system break)','d':'(d) wrong register, no bracket difference','ae':'read-only bracket: spurious start or (e) reference lacks the print\'s bracket','x':'mixed: bracket differs and register differs by another amount'}
cnt=Counter(e['cause'] for e in ev)
print('| cause | octave events (= note pairs) | notes (ref+pred) | micro F1 points | share of 3.02 |')
print('|---|---|---|---|---|')
for k in ['a','b','c','d','ae','x']:
    print(f"| {names[k]} | {cnt[k]} | {2*cnt[k]} | {pts(cnt[k]):.2f} | {100*cnt[k]/len(ev):.0f} % |")
print(f"| total | {len(ev)} | {2*len(ev)} | {pts(len(ev)):.2f} | |")
# sub
print()
sc=Counter((e['cause'],e['sub']) for e in ev)
print('| cause | sub-type | events | points |'); print('|---|---|---|---|')
for (c,s),n in sorted(sc.items(), key=lambda kv:(kv[0][0],-kv[1])):
    print(f"| {c} | {s} | {n} | {pts(n):.2f} |")
# ae by piece
print('\nread-only bracket events by piece:',Counter(e['piece'] for e in ev if e['cause']=='ae').most_common())
# per piece top 8
print()
rows=[]
for k,p in pp.items():
    n=p['events']; tot=p['nref']+p['npred']
    c=Counter(e['cause'] for e in ev if e['piece']==k)
    rows.append((100*2*n/tot,k,n,c))
rows.sort(reverse=True)
print('| piece | octave points | events | a | b | c | d | read-only | mixed | brackets (a+b+c+read-only+mixed) | dominant single cause | share of its events |')
print('|---|---|---|---|---|---|---|---|---|---|---|---|')
for r in rows[:10]:
    p,k,n,c=r
    br=c['a']+c['b']+c['c']+c['ae']+c['x']
    dom=max(c,key=c.get)
    print(f"| {k} | {p:.1f} | {n} | {c['a']} | {c['b']} | {c['c']} | {c['d']} | {c['ae']} | {c['x']} | {br} ({100*br/n:.0f} %) | {dom} | {100*c[dom]/n:.0f} % |")
# points by cause over top 8
