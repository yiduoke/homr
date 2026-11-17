"""Add the pre-filter counts, relabel status, label checks and crop-audit files to manifest.json (run last)."""
import collections, json, os
S = "/workspace/run3/"
m = json.load(open(S + "manifest.json"))
pre = {}
for n in ["pdmx_hard", "asap", "kern_scriabin"]:
    idx = sum(1 for _ in open(f"{S}lists/idx_{n}.txt"))
    valid = sum(1 for _ in open(f"{S}lists/valid_{n}.txt"))
    st = json.load(open(f"{S}status/{n}.json"))
    pre[n] = {"index_excl_v2_staffs": idx, "pass_training_filters": valid,
              "removed_by_filters": idx - valid,
              "filters": "valid_staffs.py: vocabulary check, sequence <= max_seq_len-2, <= 5 ledger lines" + (", Scriabin Verovio part >= 1 left out" if n == "kern_scriabin" else "")}
    # relabel status of the staffs that were attempted in the last run (selected lists)
    sel = {l.strip().split(",")[1] for l in open(f"{S}lists/selected_{n}.txt")}
    c = collections.Counter(st[t][0] for t in sel if t in st)
    pre[n]["relabel_status_of_selected"] = dict(c)
m["pre_filter_and_relabel"] = pre
m["label_checks"] = {n: open(f"{S}status/verify_{n}.txt").read().split("\n")[0] for n in ["pdmx_hard", "asap", "kern_scriabin"]}
m["label_checks"]["control_hard_run2_sample_4000"] = "see status/verify_control_hard.json: 0.047% notes, 1.55% staffs (same checker, run-2 labels)"
import hashlib
m["scripts_sha256"] = {f: hashlib.sha256(open(S + f, "rb").read()).hexdigest() for f in sorted(os.listdir(S)) if f.endswith(".py")}
m["audit_files"] = ["audit_crops.txt", "audit_images.txt", "status/verify_*.txt", "view/ (montages)"]
json.dump(m, open(S + "manifest.json", "w"), indent=1)
print(json.dumps(pre, indent=1))
