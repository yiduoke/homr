import json, sys
def share(path):
    n=c=0
    for l in open(path):
        t=l.strip().split(",")[-1]
        try: lines=open(t).read().split("\n")
        except Exception: continue
        n+=1
        seen=False; ch=False
        for ln in lines:
            if not ln: continue
            first=ln.split("&")[0].split(" ")[0]
            if first.startswith("note") or first.startswith("rest"): seen=True
            elif seen and any(p.split(" ")[0].startswith("clef_") for p in ln.split("&")): ch=True
        c+=ch
    return n,100*c/max(n,1)
for name,p in [("hard added","lists/img_pdmx_hard.txt"),("asap","lists/img_asap.txt"),("scriabin","lists/img_kern_scriabin.txt"),("control mixed 6000","lists/control_sample6000.txt"),("control hard 3000","lists/control_hard_sample3000.txt")]:
    print(name, "staffs with a clef change inside: %d staffs, %.1f%%" % share(p))
