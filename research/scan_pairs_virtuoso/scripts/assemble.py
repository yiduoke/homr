"""Stage 3: copy crops/pages/tokens of the kept pairs into run/scan_pairs_virtuoso/{images,pages,tokens}, write lists, manifest, quarantine.
Reads work/export/*.json and optional work/eye_wrong.json (list of crop names found wrong by eye -> quarantine)."""
import os, sys, json, glob, shutil, csv, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pieces import P, BY
ROOT = "/Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso"; BASE = ROOT + "/work"
REL = "scan_pairs_virtuoso/"      # list paths are relative to run/ (the git root of the research repo)
wrong = json.load(open(f"{BASE}/eye_wrong.json")) if os.path.exists(f"{BASE}/eye_wrong.json") else {}
for d in ("images", "pages", "tokens", "lists"):
    shutil.rmtree(f"{ROOT}/{d}", ignore_errors=True); os.makedirs(f"{ROOT}/{d}")
rows, quar, lists = [], [], collections.defaultdict(list)
used_pages = set()
for pc in P:
    f = f"{BASE}/export/{pc['pid']}.json"
    if not os.path.exists(f): continue
    d = json.load(open(f))
    for r in d["records"]:
        if not r.get("crop"): continue
        name = r.get("name") or f"{pc['pid']}_{r['page']}_s{r['sys']}"
        img_rel = f"images/{pc['pid']}/{name}.png"
        os.makedirs(f"{ROOT}/images/{pc['pid']}", exist_ok=True)
        shutil.copy(r["crop"], f"{ROOT}/{img_rel}")
        pg_src = f"{BASE}/pages/{pc['pdf']}/{r['page']}.png"
        pg_rel = f"pages/{pc['pdf']}/{r['page']}.png"
        if not os.path.exists(f"{ROOT}/{pg_rel}"):
            os.makedirs(os.path.dirname(f"{ROOT}/{pg_rel}"), exist_ok=True); shutil.copy(pg_src, f"{ROOT}/{pg_rel}")
        tier, reasons = r.get("tier"), list(r["reasons"])
        if tier and name in wrong: tier = None; reasons.append(wrong[name])
        tok_rel = ""
        if r.get("tokens"):
            tok_rel = f"tokens/{name}.tokens"; shutil.copy(r["tokens"], f"{ROOT}/{tok_rel}")
        mr = f"{r['measures'][0]+1}-{r['measures'][1]}" if r.get("measures") else ""   # 1-based index in the ASAP part
        rows.append(dict(crop=img_rel, page_image=pg_rel, page_bbox_xyxy=" ".join(map(str, r["bbox"])) if r.get("bbox") else "", system_index=r["sys"],
                         piece=pc["title"], pid=pc["pid"], edition=pc["edition"], group=pc["group"], asap_measure_range=mr,
                         tier=tier or "quarantine", verification=r.get("verification") or "", pitch_f1=("%.3f" % r["f1"]) if r.get("f1") is not None else "",
                         bar_counter_groups=r.get("groups") if r.get("groups") is not None else "", label_bars=r.get("L", ""), reasons=";".join(reasons)))
        if tier:
            g = "val" if pc["group"] == "C" else "train"
            lists[f"{g}_{tier}"].append(f"{REL}{img_rel},{REL}{tok_rel}")
            lists[f"{pc['group']}_{tier}"].append(f"{REL}{img_rel},{REL}{tok_rel}")
        else:
            quar.append(f"{REL}{img_rel},{REL}{tok_rel},{';'.join(reasons)}")
            if any(x.startswith("octave-bracket disagreement") for x in reasons) and tok_rel:
                lists[f"{'val' if pc['group']=='C' else 'train'}_octave_unverified"].append(f"{REL}{img_rel},{REL}{tok_rel}")
lists["val"] = lists["val_strong"] + lists["val_hard"]
for k, v in lists.items(): open(f"{ROOT}/lists/{k}.txt", "w").write("\n".join(v) + ("\n" if v else ""))
open(f"{ROOT}/quarantine.txt", "w").write("\n".join(quar) + "\n")
with open(f"{ROOT}/manifest.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print({k: len(v) for k, v in sorted(lists.items())}, "quarantine", len(quar), "pages", len(list(glob.glob(f"{ROOT}/pages/*/*.png"))))
