import json
E="/Users/yiduoke/Documents/homr/run/eval_run1/merge_by_role"
r=json.load(open(f"{E}/results.json"))
names={"relctl":"shipped model","relbrace":"realbrace-1","relB0":"realbrace-2 (B0)","relC0":"realbrace-3 (C0)"}
import re
def f1(row,kind):
    j=row[kind]
    if not j: return "n/a"
    r0=j['results'][0]
    m=r0['metrics']
    if kind=="pooled":
        sa=(r0.get('staff_agnostic') or {}).get('metrics')
        if not sa: return "n/a"
        m=sa
    k=m['pitch_inventory']; k=k['combined'] if 'combined' in k else k
    return f"{k['f1']*100:.2f}"
def hs(row):
    m=re.search(r"'pct': ([\d.]+)",row["hand_sync"]); return f"{float(m.group(1)):.0f}%" if m else "?"
def bars(row):
    j=row["staff"]; res=j["results"][0]
    parts=re.findall(r"parts=(\d+)",row["parts_log"][0])[0]
    return f"{res['predicted_measures']}/{res['reference_measures']} ({parts}p)"
print("| piece | model | merger | staff-sens | pooled | bars out/ref (parts after merge) | hands same bar |\n|---|---|---|---|---|---|---|")
for p in ["liszt-sonata","liszt-te-5","liszt-te-10"]:
    for t in ["relctl","relbrace","relB0","relC0"]:
        for w in ["old","new"]:
            row=r[t][p][w]
            print(f"| {p} | {names[t]} | {w} | {f1(row,'staff')} | {f1(row,'pooled')} | {bars(row)} | {hs(row)} |")
