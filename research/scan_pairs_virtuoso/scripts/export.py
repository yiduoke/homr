"""Stage 2: from work/assign/<pid>.json make token files, verification tiers and the quarantine list.
usage: HOMR_FIXED_MARGIN=1 PYTHONPATH=integration_wt python export.py <pid> ...   -> work/export/<pid>.json (per system record)"""
import sys, os, json, collections, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import labels
from pieces import BY
from training.transformer.training_vocabulary import check_token_lines, max_ledger_lines, read_tokens
from training.transformer.data_loader import MAX_ALLOWED_LEDGER_LINES
from homr.transformer.configs import Config
from training.omr_datasets.convert_lieder import MeasureCutter
BASE = "/Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso/work"
TOK = f"{BASE}/tokens"; os.makedirs(TOK, exist_ok=True)
F1_STRONG = 0.8

def trainer_filter(path):
    try:
        t = read_tokens(path); check_token_lines(t)
    except Exception as e:  # noqa: BLE001
        return "vocab:" + repr(e)[:60]
    if len(t) > Config().max_seq_len - 2: return "long"
    if max_ledger_lines(t) > MAX_ALLOWED_LEDGER_LINES: return "ledger"
    return "ok"

def bar_lists(notes):
    """model notes [[bar, pitch],...] -> list of Counters per non-empty bar, in order"""
    from align import bar_counters
    return bar_counters(notes)

def seq_sim(model_bars, label_bars):
    """bar-by-bar multiset F1 averaged, penalising a different number of bars (order-sensitive at bar level)"""
    from align import f1
    if not model_bars or not label_bars: return 0.0
    n = max(len(model_bars), len(label_bars))
    return sum(f1(a, b) for a, b in zip(label_bars, model_bars)) / n

def bar_agree(groups, first_x, unit, L):
    if groups is None: return None
    if groups == L + 1: return True
    if groups == L and first_x is not None and unit and first_x > 4 * unit: return True
    return False

def export(pid):
    cfg = BY[pid]; a = json.load(open(f"{BASE}/assign/{pid}.json"))
    v = labels.load(cfg["asap"])[0]
    mc = MeasureCutter(list(v)); pos = 0
    out = []
    reads = {}
    rf = f"{BASE}/reads/{cfg['pdf']}.jsonl"
    if os.path.exists(rf):
        for l in open(rf):
            r = json.loads(l); reads[r["id"]] = r
    for s in a["systems"]:
        rec = dict(pid=pid, id=s["id"] if "id" in s else None, page=s.get("page"), sys=s.get("sys"), crop=s.get("crop"), bbox=s.get("bbox"),
                   page_shape=s.get("page_shape"), pdf=cfg["pdf"], reasons=[], tier=None, verification=None)
        if s.get("missing"): continue
        if not s.get("eligible"):
            rec["reasons"].append("skipped:" + s["skipped"] if s.get("skipped") else "crop:not_one_grand_staff"); out.append(rec); continue
        if "L" not in s: rec["reasons"].append("align:none"); out.append(rec); continue
        if s["L"] == 0: rec["reasons"].append("not_piece_music (before start/after end of the piece)"); out.append(rec); continue
        # advance the cutter to the start of this system
        try:
            if s["start"] > pos: mc.extract_measures(s["start"] - pos); pos = s["start"]
            syms = mc.extract_measures(s["L"]); pos += s["L"]
        except Exception as e:  # noqa: BLE001
            rec["reasons"].append("conversion error: " + repr(e)[:80]); out.append(rec)
            pos = s["start"] + s["L"]; mc = MeasureCutter(list(v)[pos:]) if pos < len(v) else mc  # state restart (clef/key lost)
            continue
        from training.transformer.training_vocabulary import token_lines_to_str
        try:
            txt = token_lines_to_str(syms)
        except Exception as e:  # noqa: BLE001
            rec["reasons"].append("conversion error: " + repr(e)[:60]); out.append(rec); continue
        name = f"{pid}_{s['page']}_s{s['sys']}"
        tp = f"{TOK}/{name}.tokens"; open(tp, "w").write(txt)
        rec.update(tokens=tp, measures=[s["start"], s["start"] + s["L"]], L=s["L"], gap=s["gap"], f1=s.get("f1"), f1_pc=s.get("f1_pc"),
                   label_notes=s.get("label_notes"), model_notes=s.get("model_notes_n"), groups=s.get("groups"), name=name)
        rd = reads.get(s["id"])
        rec["model_bars"] = rd["n_bars"] if rd and "n_bars" in rd else None
        rec["trainer"] = trainer_filter(tp)
        bad = [labels.ROUNDED[cfg["asap"]][m] for m in range(s["start"], s["start"] + s["L"]) if m in labels.ROUNDED.get(cfg["asap"], {})]
        if bad: rec["trainer"] = "conversion error: " + bad[0]
        rec["bars_ok"] = bar_agree(s.get("groups"), s.get("first_x"), s.get("unit"), s["L"])
        out.append(rec)
    # tiers
    asg = [r for r in out if "tokens" in r]
    for r in asg:
        f1 = r["f1"]
        if r["trainer"] != "ok":
            r["reasons"].append(r["trainer"] if r["trainer"].startswith("conversion") else "trainer:" + r["trainer"].split(":")[0]); continue
        if f1 is None: r["reasons"].append("no model read"); continue
        if r["bars_ok"] and f1 >= F1_STRONG: r["tier"], r["verification"] = "strong", "bars+model"
        elif r["bars_ok"] is not True and f1 >= F1_STRONG and r["model_bars"] is not None and abs(r["model_bars"] - r["L"]) <= 1: r["tier"], r["verification"] = "strong", "model_bars"
        elif r["bars_ok"]:
            if r["f1_pc"] is not None and r["f1_pc"] >= 0.9 and r["f1_pc"] - f1 >= 0.25: r["reasons"].append("octave shift (pitch classes agree, octaves differ)")
            else: r["tier"], r["verification"] = "hard", "bars"
        elif r["bars_ok"] is None and r["model_bars"] is not None and abs(r["model_bars"] - r["L"]) <= 1:
            r["tier"], r["verification"] = "hard", "model_bars"     # barline counter undetermined, the model's own bar count agrees; the shift check below applies
        else: r["reasons"].append("bar mismatch")
    # key signature printed in the scan (the released model's read) vs the label's: a different spelling/key means another edition text
    for r in asg:
        if r["tier"] == "hard" and r.get("id") in reads and "tokens" in reads[r["id"]]:
            lk = re.findall(r"keySignature_(-?\d+)", open(r["tokens"]).read()); mk = re.findall(r"keySignature_(-?\d+)", reads[r["id"]]["tokens"])
            if lk and mk and lk[0] != mk[0]:
                r["tier"], r["verification"] = None, None
                r["reasons"].append("edition mismatch (key signature %s in the label, %s in the scan read)" % (lk[0], mk[0]))
    # octave brackets: the label and the released model's read must agree on whether the system carries an 8va/8vb sign
    # (the ASAP scores often lack the brackets of the print, or add ones the edition does not print; see README)
    for r in asg:
        if r["tier"] and r.get("id") in reads and "tokens" in reads[r["id"]]:
            lab_has = bool(re.search("octaveShift", open(r["tokens"]).read())); mod_has = bool(re.search("octaveShift", reads[r["id"]]["tokens"]))
            r["octave_label"], r["octave_model"] = lab_has, mod_has
            if lab_has != mod_has:
                r["tier"], r["verification"] = None, None
                r["reasons"].append("octave-bracket disagreement (label %s an 8va/8vb sign, the released model's read %s one)" % ("has" if lab_has else "lacks", "has" if mod_has else "lacks"))
    # local shift check of the hard systems: bar-by-bar similarity of the assigned window vs shifted windows
    meas_c = [collections.Counter(sym.pitch for sym in m if sym.rhythm.startswith("note")) for m in v]
    for r in asg:
        if r["tier"] != "hard": continue
        rd = reads.get(r["id"])
        mb = bar_lists(rd["notes"]); st, en = r["measures"]
        base = seq_sim(mb, meas_c[st:en]); best = (base, 0, 0)
        for ds in range(-3, 4):
            for dl in range(-2, 3):
                a0, a1 = st + ds, en + ds + dl
                if (ds, dl) == (0, 0) or a0 < 0 or a1 > len(v) or a1 <= a0: continue
                sc = seq_sim(mb, meas_c[a0:a1])
                if sc > best[0]: best = (sc, ds, dl)
        r["seq_sim"] = round(base, 3); r["seq_best_alt"] = [round(best[0], 3), best[1], best[2]]
        if base < 0.35 or best[0] > base + 0.05:
            r["tier"], r["verification"] = None, None
            r["reasons"].append("alignment ambiguous (a shifted measure window matches the read better, or bar-wise similarity < 0.35)")
    # anchoring: segments split by gaps; a hard system needs a strong system within 6 systems in its segment
    seg = 0; segs = []
    for r in asg:
        if r["gap"]: seg += 1
        segs.append(seg)
    seglen = collections.Counter(segs)
    for i, r in enumerate(asg):
        if r["tier"] and seglen[segs[i]] < 6 and len(seglen) > 1:
            r["tier"], r["verification"] = None, None; r["reasons"].append("cumulative bar counts inconsistent (short run next to a measure gap)")
    strong_idx = [(i, segs[i]) for i, r in enumerate(asg) if r["tier"] == "strong"]
    for i, r in enumerate(asg):
        if r["tier"] == "hard":
            d = min([abs(i - j) for j, sg in strong_idx if sg == segs[i]] or [99])
            r["anchor_dist"] = d
            if d > 6: r["tier"], r["verification"] = None, None; r["reasons"].append("alignment unanchored (no strong system within 6 systems)")
        if r["tier"] is None and not r["reasons"]: r["reasons"].append("unclassified")
    # a system right after a gap with a failed read: edition mismatch candidate
    for i, r in enumerate(asg):
        if r["tier"] is None and r["gap"] and "bar mismatch" in r["reasons"]:
            r["reasons"].append("edition mismatch? (measures skipped before this system)")
    os.makedirs(f"{BASE}/export", exist_ok=True)
    json.dump(dict(pid=pid, n_measures=len(v), end=a["end"], records=out), open(f"{BASE}/export/{pid}.json", "w"))
    c = collections.Counter(r["tier"] or "quarantine" for r in asg)
    print(pid, cfg["title"], dict(c), "non-assigned:", len(out) - len(asg), "end", a["end"], "/", len(v))

if __name__ == "__main__":
    for pid in sys.argv[1:]: export(pid)
