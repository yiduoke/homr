import json,csv,collections
R=json.load(open("/workspace/kern_check/step1_raw.json"))
rows=[]
for r in R:
    if 'error' in r or not r.get('krn'): rows.append(dict(repo=r['repo'],piece=r['piece'],status='error' if 'error' in r else 'nokrn',note=r.get('error',''))); continue
    sp=r['scan_pages']; S=[s for p in sp for s in p]
    K=r['krn_meas']
    ns,nk=len(S),len(K)
    row=dict(repo=r['repo'],piece=r['piece'],pages=len(sp),scan_sys=ns,krn_sys=nk,hasLB=r['hasLB'],hasPB=r['hasPB'],
             sys_pages=str([len(p) for p in sp]))
    if not r['hasLB'] and not r['hasPB']:
        row['status']='no_markers'
    elif ns==nk:
        row['status']='sys_equal'
    else:
        row['status']='sys_diff'
    # measure compare: best offset alignment of strict and raw
    for name,idx in (('strict',0),('raw',1)):
        seq=[s[idx] for s in S]
        if ns>=nk:
            best=max((sum(a==b for a,b in zip(seq[o:o+nk],K)),o) for o in range(ns-nk+1))
        else:
            best=(sum(a==b for a,b in zip(seq,K)),0)
        row['bars_match_'+name]=best[0]; row['offset']=best[1]
    row['per_page_krn_PB']=''
    if r['hasPB']:
        c=collections.Counter(r['krn_page']); kp=[c[i] for i in sorted(c)]
        row['krn_pb_pages']=str(kp)
        sc=[len(p) for p in sp]
        row['pb_match']=any(sc[o:o+len(kp)-0]==kp or sc[o:o+len(kp)][:-1]==kp[:-1] for o in range(0,max(1,len(sc)-len(kp)+1)))
    # extra pages: pages with zero systems
    row['empty_pages']=sum(1 for p in sp if not p)
    hs=sorted(x[2] for x in S); med=hs[len(hs)//2] if hs else 0
    row['odd_staves']=sum(1 for x in S if x[2]>1.4*med or x[2]<0.65*med)
    rows.append(row)
keys=sorted({k for r in rows for k in r})
w=csv.DictWriter(open("/workspace/kern_check/step1_results.csv","w"),fieldnames=keys);w.writeheader();w.writerows(rows)
json.dump(rows,open("/workspace/kern_check/step1_results.json","w"),indent=1)
for repo in ["mozart-piano-sonatas","chopin-mazurkas","beethoven-piano-sonatas"]:
    rr=[r for r in rows if r['repo']==repo]
    c=collections.Counter(r['status'] for r in rr)
    ok=[r for r in rr if r.get('status')=='sys_equal']
    full_s=sum(1 for r in ok if r['bars_match_strict']==r['krn_sys'])
    full_r=sum(1 for r in ok if r['bars_match_raw']==r['krn_sys'])
    tot=sum(r['krn_sys'] for r in ok); ms=sum(r['bars_match_strict'] for r in ok); mr=sum(r['bars_match_raw'] for r in ok)
    emp=sum(1 for r in rr if r.get('empty_pages',0)>0)
    nonc=sum(1 for r in rr if r.get('odd_staves',0)>0)
    flag=sum(1 for r in rr if r.get('status')=='sys_equal' and r['odd_staves']>0)
    longer=sum(1 for r in rr if r.get('status')=='sys_diff' and r['scan_sys']>r['krn_sys'])
    shorter=sum(1 for r in rr if r.get('status')=='sys_diff' and r['scan_sys']<r['krn_sys'])
    pbs=[r for r in rr if r.get('hasPB')]; pbm=sum(1 for r in pbs if r.get('pb_match'))
    print('  equal-with-outlier',flag,'scan longer',longer,'scan shorter',shorter,'PB pieces',len(pbs),'PB match',pbm)
    print(repo,len(rr),dict(c),'strict-all-match',full_s,'raw',full_r,'sys-level',ms,mr,'/',tot,'withEmptyPages',emp,'oddStaff',nonc)
