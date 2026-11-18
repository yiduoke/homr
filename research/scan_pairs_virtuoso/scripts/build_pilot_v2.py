"""v2 label lists of the scan-versus-render pilot (D23). The frozen v1 lists are not changed; new files next to them.

usage: build_pilot_v2.py        (after twin_render.py wrote twins/ for the added crops: twins_report_v2add.json)

Pilot (both arms, same passages in the same line order, same token file):
  base          = lists/pilot_scan.txt (867) with the corrected token file wherever one exists (tokens_typeless_rest_fixed/: bar rests, 78 passages)
  + moved       = the 26 passages of Chopin Sonata 2 mvt 2 (C2) from val_scan.txt (all movements of one work on the train side)
  + octave      = lists/train_octave_verified.txt (34; 7 with tokens corrected to the print, twins from the XML with the bracket added)
  + tuplet      = lists/train_tuplet_fixed.txt (30, tokens_tuplet_fixed/)
  - printed notation mismatch (printed meter symbol / time signature differs from the label)   -> lists/pilot_printed_notation_mismatch.txt
  - clef disagreement (label clef differs from the print in every one of 19 checked)            -> lists/pilot_clef_key_removed.txt
Validation: val_scan.txt (98) with corrected tokens, minus C2 (moved), minus removals.
Batch 2: removal of the printed-notation candidates, corrected tokens under batch2/tokens_printed/ (see lists/batch2_printed_notation_candidates.txt).
"""
import csv, collections, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
REL = "scan_pairs_virtuoso/"; BOX = "/workspace/pilot/"
L = lambda p: [l.strip() for l in open(f"{ROOT}/{p}") if l.strip()]
name_of = lambda line: os.path.basename(line.split(",")[0])[:-4]

# ---- decisions made by eye (see PILOT_SPEC.md section 7) ----
PRINT_MISMATCH = {   # crop: (printed, label, class)
    "A5_p-01_s0": ("4/4 numerals", "common (C)", "S meter symbol"),
    "B1_p-50_s0": ("4/4 numerals", "common (C)", "S meter symbol"),
    "A7_p-05_s0": ("cut (C with a stroke)", "2/2 numerals", "S meter symbol"),
    "A9_p-57_s0": ("common (C)", "cut", "S meter symbol"),
    "A10_p-10_s4": ("cut (C with a stroke)", "4/4 numerals", "S meter symbol"),
    "A15_p-02_s3": ("common (C), reprinted at the Allegro", "none", "M time signature missing in the label"),
    "A18_p-11_s3": ("2/4 reprinted after the double bar", "none", "M time signature missing in the label"),
}
CLEF_KEY = json.load(open(f"{ROOT}/lists/pilot_clef_key_flags_v1.json"))   # name -> why (clef ... ; key ...), the 78 flagged crops of v1 (clef_disagree.py)

def build():
    scan, twin = L("lists/pilot_scan.txt"), L("lists/pilot_twin_render.txt")
    vscan, vtwin = L("lists/val_scan.txt"), L("lists/val_twin_render.txt")
    assert [name_of(a) for a in scan] == [name_of(b) for b in twin] and [name_of(a) for a in vscan] == [name_of(b) for b in vtwin]
    fixed = {name_of(l): l.split(",")[1] for l in L("lists/train_strong_typeless_rest_fixed.txt") + L("lists/val_strong_typeless_rest_fixed.txt")}
    tok_v2 = {"A10_p-03_s5": REL + "tokens_v2/A10_p-03_s5.tokens"}   # octave-verified crop with a typeless bar rest (rest_8 -> rest_1), see below
    entries = []     # (name, scan_line, twin_line, origin)
    def add(name, sc, tw, origin):
        tok = fixed.get(name) or tok_v2.get(name) or sc.split(",")[1]
        pid = name.split("_")[0]
        entries.append((name, f"{sc.split(',')[0]},{tok}", f"{tw.split(',')[0]},{tok}", origin))
    for sc, tw in zip(scan, twin): add(name_of(sc), sc, tw, "v1 pilot")
    moved = [(sc, tw) for sc, tw in zip(vscan, vtwin) if name_of(sc).startswith("C2_")]
    for sc, tw in moved: add(name_of(sc), sc, tw, "moved from val (Sonata 2 mvt 2)")
    rep = {r["name"]: r for r in json.load(open(f"{ROOT}/twins_report_v2add.json"))}
    for lst, origin in (("train_octave_verified", "octave-verified"), ("train_tuplet_fixed", "tuplet-fixed")):
        for l in L(f"lists/{lst}.txt"):
            n = name_of(l); assert rep[n]["status"] == "ok", n
            pid = n.split("_")[0]
            add(n, l, f"{REL}twins/{pid}/{n}.png,{l.split(',')[1]}", origin)
    val = [(name_of(sc), f"{sc.split(',')[0]},{fixed.get(name_of(sc)) or sc.split(',')[1]}", f"{tw.split(',')[0]},{fixed.get(name_of(sc)) or sc.split(',')[1]}")
           for sc, tw in zip(vscan, vtwin) if not name_of(sc).startswith("C2_")]
    return entries, val, len(moved)

def main():
    entries, val, nmoved = build()
    os.makedirs(f"{ROOT}/tokens_v2", exist_ok=True)
    # A10_p-03_s5: the one octave-verified crop with a typeless bar rest (regression of the converter with typeless rests on: line differs only by rest_8 -> rest_1)
    old = open(f"{ROOT}/tokens/A10_p-03_s5.tokens").read().split("\n"); new = open(f"{ROOT}/work/tuplet/regress_A10_p-03_s5.tokens").read().split("\n")
    assert len(old) == len(new) and sum(a != b for a, b in zip(old, new)) == 1
    open(f"{ROOT}/tokens_v2/A10_p-03_s5.tokens", "w").write("\n".join(new))
    clef_flag = {n for n, w in CLEF_KEY.items() if "clef" in w}
    clef_flag |= {"A14_p-03_s5"}                                   # key signature label wrong by eye (print 2 sharps, label -3)
    clef_flag |= {"A2_p-081_s2", "A6_p-04_s4", "A16_p-24_s0", "A9_p-57_s2"}   # added crops with the same clef disagreement (not eye-checked individually)
    removed_pn, removed_ck = [], []
    keep, vkeep = [], []
    for e in entries:
        if e[0] in PRINT_MISMATCH: removed_pn.append(e); continue
        if e[0] in clef_flag: removed_ck.append(e); continue
        keep.append(e)
    vk = []
    for e in val:
        if e[0] in PRINT_MISMATCH: removed_pn.append(e + ("val",)); continue
        if e[0] in clef_flag: removed_ck.append(e + ("val",)); continue
        vk.append(e)
    out = {}
    out["pilot_scan_v2"] = [e[1] for e in keep]; out["pilot_twin_render_v2"] = [e[2] for e in keep]
    out["val_scan_v2"] = [e[1] for e in vk]; out["val_twin_render_v2"] = [e[2] for e in vk]
    for k, v in list(out.items()):
        out["box/" + k] = [l.replace(REL, BOX) for l in v]
        for l in v:
            for p in l.split(","):
                assert os.path.exists(f"{ROOT}/{p.replace(REL, '')}"), p
    out["pilot_printed_notation_mismatch"] = [f"{e[0]}\t{PRINT_MISMATCH[e[0]][0]}\tlabel: {PRINT_MISMATCH[e[0]][1]}\t{PRINT_MISMATCH[e[0]][2]}" for e in removed_pn]
    out["pilot_clef_key_removed"] = [f"{e[0]}\t{(CLEF_KEY or {}).get(e[0], 'added crop / eye')}" for e in removed_ck]
    os.makedirs(f"{ROOT}/lists/box", exist_ok=True)
    for k, v in out.items():
        open(f"{ROOT}/lists/{k}.txt", "w").write("\n".join(v) + "\n")
    cnt = collections.Counter(e[3] for e in keep)
    summ = dict(pilot_v2=len(keep), val_v2=len(vk), by_origin=dict(cnt), moved_C2=nmoved, removed_printed=len(removed_pn), removed_clef=len(removed_ck),
                tokens_replaced_in_v1_pilot=sum(1 for e, s in zip(entries[:867], L("lists/pilot_scan.txt")) if e[1] != s),
                pilot_by_piece=dict(collections.Counter(e[0].split("_")[0] for e in keep)), val_by_piece=dict(collections.Counter(e[0].split("_")[0] for e in vk)))
    json.dump(summ, open(f"{ROOT}/pilot_v2_summary.json", "w"), indent=1)
    print(json.dumps(summ, indent=1))

if __name__ == "__main__":
    main()
