import json, collections, sys, glob, re
c=collections.Counter()
for pid in sys.argv[1:]:
    d=json.load(open(f'/Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso/batch2/work/export/{pid}.json'))
    cc=collections.Counter()
    for r in d['records']:
        if r.get('tier'): cc['KEPT '+r['tier']]+=1
        else:
            for x in r['reasons']: cc[re.sub(r'\(.*|KeyError.*|measure \d+.*|at measure.*','',x).strip()[:70]]+=1
            if not r['reasons']: cc['??']+=1
    print(pid, dict(cc))
