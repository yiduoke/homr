"""Build the run-3 candidate lists (run after select_candidates.py and relabel_run3.py).
Needs PYTHONPATH=/workspace/homr_acc (training vocabulary and data-loader filters, as used for the control lists).
Writes /workspace/run3/{cand_train,cand_train_nooct,cand_val,cand_val_hard}.txt, lists/added_*.txt, manifest.json.
"""
import collections, hashlib, json, os, random, re, subprocess, sys
from training.transformer.data_loader import MAX_ALLOWED_LEDGER_LINES
from training.transformer.training_vocabulary import check_token_lines, max_ledger_lines, read_tokens
from homr.transformer.configs import Config

S = "/workspace/run3/"
SEED = 20261118
SCRIABIN_COPIES = 2
sel = json.load(open(S + "lists/selection.json"))
role = sel["role"]
max_len = Config().max_seq_len - 2


def new_tok(t):
    return S + "tokens/" + t[len("/workspace/"):]


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


excl_hash = {l.strip() for l in open("/workspace/exclude_hashes_v2.txt") if l.strip()}
rows = {}       # set -> list of (png, newtok, role, flags)
drops = collections.defaultdict(collections.Counter)
for name in ["pdmx_hard", "asap", "kern_scriabin"]:
    out = []
    for ln in open(f"{S}lists/selected_{name}.txt"):
        png, tok = ln.strip().split(",")
        nt = new_tok(tok)
        r = role[png]
        if not os.path.exists(nt):
            drops[name][f"relabel failed ({r})"] += 1
            continue
        if name == "pdmx_hard":
            m = re.search(r"/(Qm[A-Za-z0-9]+)-", png)
            if m and m[1] in excl_hash:
                drops[name]["excluded hash (should not happen)"] += 1
                continue
        if name == "kern_scriabin":
            m = re.search(r"-vrv-\d+-(\d+)\.png$", png)
            if m and int(m[1]) >= 1:
                drops[name][f"Verovio crop of part >= 1: image shows 2-3 staves, label one ({r})"] += 1
                continue
        try:
            toks = read_tokens(nt)
            check_token_lines(toks)
        except Exception as e:  # noqa: BLE001
            drops[name][f"token not in vocabulary ({r})"] += 1
            continue
        if len(toks) > max_len:
            drops[name][f"longer than max_seq_len ({r})"] += 1
            continue
        if max_ledger_lines(toks) > MAX_ALLOWED_LEDGER_LINES:
            drops[name][f"too many ledger lines ({r})"] += 1
            continue
        if not os.path.exists(png) or not os.path.exists(png[:-4] + ".json"):
            drops[name][f"image or json missing ({r})"] += 1
            continue
        octs = "octaveShift" in open(nt).read()
        out.append((png, nt, r, octs))
    rows[name] = out

# held-out checks by score / piece
def group(name, png):
    if name == "pdmx_hard":
        return re.search(r"/(Qm[A-Za-z0-9]+)-", png)[1]
    return re.match(r"^(.*?)(?:-vrv)?-\d+-\d+$", os.path.basename(png)[:-4])[1]

for name in rows:
    g = collections.defaultdict(set)
    for png, nt, r, o in rows[name]:
        g[group(name, png)].add(r)
    mixed = [k for k, v in g.items() if len(v) > 1]
    assert not mixed, (name, mixed[:3])

control_train = [l.strip() for l in open(S + "run2_train_excl.txt") if l.strip()]
control_val = [l.strip() for l in open(S + "run2_val_excl.txt") if l.strip()]
control_pngs = {l.split(",")[0] for l in control_train + control_val}
for f in ["holdout_real_excl.txt", "holdout_inserted_excl.txt"]:
    control_pngs |= {l.split(",")[0] for l in open(S + f) if l.strip()}
for name in rows:
    assert not any(png in control_pngs for png, *_ in rows[name]), name + " overlaps a control list"
# a held-out hard score must not appear in any control staff or in train
hard_val_scores = {group("pdmx_hard", p) for p, _, r, _ in rows["pdmx_hard"] if r == "val"}
hard_train_scores = {group("pdmx_hard", p) for p, _, r, _ in rows["pdmx_hard"] if r == "train"}
ctl_scores = {re.search(r"/(Qm[A-Za-z0-9]+)-", p)[1] for p in control_pngs if "/pdmx/" in p and re.search(r"/(Qm[A-Za-z0-9]+)-", p)}
assert not (hard_val_scores & hard_train_scores) and not (hard_val_scores & ctl_scores)

def lines(name, which, nooct=False):
    return [f"{p},{t}" for p, t, r, o in rows[name] if r == which and not (nooct and o)]

def build(nooct):
    added = lines("pdmx_hard", "train", nooct) + lines("asap", "train", nooct)
    scr = lines("kern_scriabin", "train", nooct)
    added_all = added + scr * SCRIABIN_COPIES
    train = control_train + added_all
    random.Random(SEED).shuffle(train)
    return train, added, scr

def write(path, ls):
    with open(path, "w") as f:
        f.write("\n".join(ls) + "\n")

cand_train, added, scr = build(False)
cand_train_no, added_no, scr_no = build(True)
val_hard = lines("pdmx_hard", "val") + lines("asap", "val") + lines("kern_scriabin", "val")
val_hard_no = [l for l in val_hard]  # held-out hard list keeps its brackets in both variants
random.Random(SEED + 1).shuffle(val_hard)
cand_val = control_val + val_hard
write(S + "cand_train.txt", cand_train)
write(S + "cand_train_nooct.txt", cand_train_no)
write(S + "cand_val_hard.txt", val_hard)
write(S + "cand_val.txt", cand_val)
for name in rows:
    write(S + f"lists/added_{name}_train.txt", lines(name, "train"))
    write(S + f"lists/added_{name}_val.txt", lines(name, "val"))

def cnt(name, which, nooct=False):
    return len(lines(name, which, nooct))

counts = {
    "control_train": len(control_train), "control_val": len(control_val),
    "added_train_staffs": {n: cnt(n, "train") for n in rows},
    "added_train_lines_in_cand_train": {"pdmx_hard": cnt("pdmx_hard", "train"), "asap": cnt("asap", "train"),
                                         "kern_scriabin (x%d)" % SCRIABIN_COPIES: cnt("kern_scriabin", "train") * SCRIABIN_COPIES},
    "held_out_hard": {n: cnt(n, "val") for n in rows},
    "cand_train": len(cand_train), "cand_val": len(cand_val), "cand_val_hard": len(val_hard),
    "cand_train_nooct": len(cand_train_no),
    "added_train_staffs_nooct": {n: cnt(n, "train", True) for n in rows},
    "added_staffs_with_octave_bracket": {n: sum(1 for p, t, r, o in rows[n] if o) for n in rows},
    "scores_or_pieces": {"hard_pdmx_train_scores": len(hard_train_scores), "hard_pdmx_val_scores": len(hard_val_scores),
                          "asap_val_pieces": len({group('asap', p) for p, _, r, _ in rows['asap'] if r == 'val'}),
                          "asap_train_pieces": len({group('asap', p) for p, _, r, _ in rows['asap'] if r == 'train'}),
                          "scriabin_val_pieces": len({group('kern_scriabin', p) for p, _, r, _ in rows['kern_scriabin'] if r == 'val'}),
                          "scriabin_train_pieces": len({group('kern_scriabin', p) for p, _, r, _ in rows['kern_scriabin'] if r == 'train'})},
    "dropped": {k: dict(v) for k, v in drops.items()},
}
def git(path):
    try:
        return subprocess.check_output(["git", "-C", path, "rev-parse", "--short", "HEAD"], text=True).strip() + (
            " (dirty)" if subprocess.check_output(["git", "-C", path, "status", "--porcelain"], text=True).strip() else "")
    except Exception as e:  # noqa: BLE001
        return repr(e)

idx = {}
for s in ["grandstaff", "Lieder-main", "pdmx", "pdmx/hard", "asap", "kern_scriabin"]:
    p = f"/workspace/homr566/datasets_meter/{s}/index_excl_v2.txt"
    idx[s] = {"path": p, "lines": sum(1 for _ in open(p)), "sha256": sha(p)}
scripts = {f: sha(S + f) for f in ["export_ms.py", "staff_stats3.py", "select_candidates.py", "relabel_run3.py", "verify_run3.py",
                                      "make_view.py", "image_stats3.py", "analyze_img.py", "analyze_crops.py", "build_cand_lists.py"] if os.path.exists(S + f)}
manifest = {
    "built": subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip(),
    "counts": counts,
    "seeds": {"selection (select_candidates.py)": sel["seed"], "list shuffle (build_cand_lists.py)": SEED,
              "val_hard shuffle": SEED + 1, "verification sample (make_view.py)": 11},
    "selection": {k: sel[k] for k in ["target_total", "hold", "max_score_staffs", "min_density", "rare_quota", "common_meters", "median_density",
                                      "pool_scores", "eligible_scores", "chosen_scores", "heldout_hard_scores", "asap_heldout_pieces", "scriabin_heldout_pieces",
                                      "meters_selected_scores", "meters_selected_staffs", "meters_train_staffs", "meter_note"]},
    "indexes_used": idx,
    "control_lists": {f: {"lines": sum(1 for _ in open(S + f)), "sha256": sha(S + f)} for f in
                      ["run2_train_excl.txt", "run2_val_excl.txt", "holdout_real_excl.txt", "holdout_inserted_excl.txt"]},
    "exclusion": {"exclude_ids.txt": sha(S + "exclude_ids.txt"), "exclude_hashes_v2.txt": sha("/workspace/exclude_hashes_v2.txt"),
                  "note": "hard PDMX / ASAP / Scriabin come only from the index_excl_v2 files; selected keys checked against exclude_hashes_v2.txt"},
    "filters_applied_to_added_staffs": ["relabel_run3.py status ok (exact match of every non-lift field to the run-1 file)",
                                         "token vocabulary check (check_token_lines)", "sequence <= max_seq_len-2 and ledger lines <= %d (data_loader._filter_valid_samples)" % MAX_ALLOWED_LEDGER_LINES,
                                         "Scriabin Verovio crops of part >= 1 dropped (image shows more staves than the label)",
                                         "hard PDMX: score with > %d pool staffs or mean notes/staff < %s not eligible" % (sel["max_score_staffs"], sel["min_density"])],
    "scripts_sha256": scripts,
    "box_state": {"homr_acc (parser, vocabulary)": git("/workspace/homr_acc"), "homr566 (datasets, MuseScore export code)": git("/workspace/homr566")},
    "label_source": {"pdmx_hard": "MuseScore export datasets/pdmx/hard/rendered_scores (as run 2)",
                     "asap": "MuseScore export re-made from r6_extra/asap_mxl by export_ms.py into run3/ms_export/asap (original deleted)",
                     "kern_scriabin": "MuseScore export re-made from r6_extra/kern_mxl (music21 conversion of the kern) into run3/ms_export/kern_scriabin; NOT Verovio MEI"},
    "lists": {"cand_train.txt": "control train (run2_train_excl) + added train staffs + Scriabin x%d, shuffled" % SCRIABIN_COPIES,
              "cand_train_nooct.txt": "same, without added staffs that contain an octaveShift line (the control's original sets have none)",
              "cand_val.txt": "control val (run2_val_excl) + cand_val_hard", "cand_val_hard.txt": "held-out hard PDMX, ASAP, Scriabin (by score / piece)"},
}
json.dump(manifest, open(S + "manifest.json", "w"), indent=1)
print(json.dumps(counts, indent=1))
