"""Stage 3 (batch 2): copy crops/pages/tokens of the kept pairs into batch2/{images,pages,tokens,lists}, write lists, manifest, quarantine.
Inputs: work/export/*.json; work/eye_verdicts.json (name -> "ok" | "wrong: why"; wrong -> quarantine);
work/octave_decisions.json (name -> {decision: admit|corrected|quarantine, note, tokens: path of corrected tokens}).
Groups (pieces2.py): T train, V validation extension (never trained on), D Ravel Une barque (Demets reprint, own list)."""
import os, sys, json, glob, shutil, csv, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pieces2 import P, BY
ROOT = "/Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso/batch2"; BASE = ROOT + "/work"
REL = "scan_pairs_virtuoso/batch2/"
eye = json.load(open(f"{BASE}/eye_verdicts.json")) if os.path.exists(f"{BASE}/eye_verdicts.json") else {}
octd = json.load(open(f"{BASE}/octave_decisions.json")) if os.path.exists(f"{BASE}/octave_decisions.json") else {}
for d in ("images", "pages", "tokens", "tokens_uncorrected", "lists"):
    shutil.rmtree(f"{ROOT}/{d}", ignore_errors=True); os.makedirs(f"{ROOT}/{d}")
rows, quar, L = [], [], collections.defaultdict(list)
clefkey, roles = [], []
partial_q = []
def is_oct_only(reasons): return bool(reasons) and all(x.startswith(("octave-bracket disagreement", "octave shift (pitch")) for x in reasons)
for pc in P:
    f = f"{BASE}/export/{pc['pid']}.json"
    if not os.path.exists(f): continue
    d = json.load(open(f)); g = pc["group"]
    for r in d["records"]:
        if not r.get("crop"): continue
        name = r.get("name") or f"{pc['pid']}_{r['page']}_s{r['sys']}"
        img_rel = f"images/{pc['pid']}/{name}.png"; os.makedirs(f"{ROOT}/images/{pc['pid']}", exist_ok=True)
        shutil.copy(r["crop"], f"{ROOT}/{img_rel}")
        pg_rel = f"pages/{pc['pdf']}/{r['page']}.png"
        if not os.path.exists(f"{ROOT}/{pg_rel}"):
            os.makedirs(os.path.dirname(f"{ROOT}/{pg_rel}"), exist_ok=True); shutil.copy(f"{BASE}/pages/{pc['pdf']}/{r['page']}.png", f"{ROOT}/{pg_rel}")
        tier, reasons = r.get("tier"), list(r["reasons"])
        ev = eye.get(name, "")
        octrev = ""
        tok_rel = ""
        if r.get("tokens"):
            tok_rel = f"tokens/{name}.tokens"; shutil.copy(r["tokens"], f"{ROOT}/{tok_rel}")
        if tier and ev.startswith("wrong"): tier = None; reasons.append("by eye: " + ev[7:])
        # octave review
        dec = octd.get(name)
        if dec and dec.get("partial") and tier:
            tier = None; reasons.append("octave review: " + dec["note"].replace(";", ",")); octrev = "quarantined: " + dec["note"]; r["octave_pre_tier"] = r.get("tier")
            gk0 = {"T": "train", "V": "val", "D": "demets"}[g]
            partial_q.append((gk0, name))
        if is_oct_only(reasons) and r.get("octave_pre_tier"):
            if dec and dec["decision"] in ("admit", "corrected") and not ev.startswith("wrong"):
                tier = "octave_verified"; octrev = dec["decision"]; reasons = []
                if dec["decision"] == "corrected":
                    shutil.copy(r["tokens"], f"{ROOT}/tokens_uncorrected/{name}.tokens"); shutil.copy(dec["tokens"], f"{ROOT}/{tok_rel}")
            elif dec: octrev = "quarantined: " + dec.get("note", ""); reasons = reasons + ["octave review: " + dec.get("note", "label wrong / edition difference").replace(";", ",")]
            else: octrev = "unreviewed"
        mr = f"{r['measures'][0]+1}-{r['measures'][1]}" if r.get("measures") else ""
        role = ""
        if r.get("measures"):
            role = ("starts_inside_8va " if r.get("oct_start_inside") else "") + ("ends_inside_8va " if r.get("oct_end_inside") else "") + ("has_8va_token" if r.get("oct_in_label") else "")
        row = dict(crop=img_rel, page_image=pg_rel, page_bbox_xyxy=" ".join(map(str, r["bbox"])) if r.get("bbox") else "", system_index=r["sys"],
                   piece=pc["title"], pid=pc["pid"], edition=pc["edition"], group=g, asap_measure_range=mr,
                   tier=tier or "quarantine", verification=r.get("verification") or ("octave eye review" if tier == "octave_verified" else ""),
                   pitch_f1=("%.3f" % r["f1"]) if r.get("f1") is not None else "", read_pitch_f1=r.get("read_pitch_f1", ""), read_onset_f1=r.get("read_onset_f1", ""),
                   bar_counter_groups=r.get("groups") if r.get("groups") is not None else "", label_bars=r.get("L", ""), rounded_groups=r.get("rounded", ""),
                   octave_roles=role.strip(), octave_review=octrev, clef_key_disagree=",".join(r.get("clef_key", [])), eye=ev, reasons=";".join(reasons))
        rows.append(row)
        item = f"{REL}{img_rel},{REL}{tok_rel}"
        if tier:
            gk = {"T": "train", "V": "val", "D": "demets"}[g]
            L[f"{gk}_{tier}"].append(item)
            if r.get("rounded"): L[f"{gk}_rounded"].append(item)
            if r.get("clef_key"): clefkey.append(f"{item},{'+'.join(r['clef_key'])},label clefs {r['clef_label']} key {r['key_label']}; read clefs {r['clef_read']} key {r['key_read']}")
        else:
            quar.append(f"{REL}{img_rel},{REL}{tok_rel},{';'.join(reasons)}")
            if is_oct_only(r["reasons"]) and tok_rel:
                gk = {"T": "train", "V": "val", "D": "demets"}[g]
                L[f"{gk}_octave_unverified"].append(item)
                if octrev.startswith("quarantined"): L[f"{gk}_octave_quarantine_final"].append(item)
        if r.get("octave_pre_tier") and is_oct_only(r["reasons"]) and tok_rel: pass
for gk0, nm in partial_q:
    img = f"{REL}images/{nm.split('_')[0]}/{nm}.png"; it = f"{img},{REL}tokens/{nm}.tokens"
    L[f"{gk0}_octave_unverified"].append(it); L[f"{gk0}_octave_quarantine_final"].append(it)
# octave_unverified = every octave-only disagreement, including those since admitted
for row in rows:
    if row["octave_review"] in ("admit", "corrected"):
        gk = {"T": "train", "V": "val", "D": "demets"}[row["group"]]
        L[f"{gk}_octave_unverified"].append(f"{REL}{row['crop']},{REL}tokens/{os.path.basename(row['crop'])[:-4]}.tokens")
for gk in ("train", "val", "demets"):
    L[f"{gk}_all"] = L[f"{gk}_strong"] + L[f"{gk}_hard"] + L[f"{gk}_octave_verified"]
# the single Demets list
L["train_demets_unebarque"] = L.pop("demets_all")
for k in ("strong", "hard", "octave_verified", "octave_unverified", "octave_quarantine_final", "rounded"):
    if f"demets_{k}" in L: L[f"train_demets_unebarque_{k}"] = L.pop(f"demets_{k}")
L["val"] = L.pop("val_all")
L["train_all"] = L["train_all"]
for k, v in L.items(): open(f"{ROOT}/lists/batch2_{k}.txt", "w").write("\n".join(v) + ("\n" if v else ""))
open(f"{ROOT}/lists/clef_key_disagree.txt", "w").write("\n".join(clefkey) + "\n")
open(f"{ROOT}/quarantine.txt", "w").write("\n".join(quar) + "\n")
with open(f"{ROOT}/manifest.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print({k: len(v) for k, v in sorted(L.items())}, "quarantine", len(quar), "clef/key", len(clefkey), "pages", len(list(glob.glob(f"{ROOT}/pages/*/*.png"))))
