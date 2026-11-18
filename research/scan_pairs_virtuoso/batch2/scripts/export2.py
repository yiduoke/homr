"""Stage 2 (batch 2): from work/assign/<pid>.json make token files (FIXED tuplet converter), verification tiers, rhythm checks, octave roles, clef/key flags and quarantine reasons.
Same tier rules as the pilot export.py, plus: tuplet notes the converter cannot represent -> quarantine; rounded groups recorded; bars of the MusicXML longer than the meter,
token sums that differ from the true sums outside rounded groups -> quarantine; octave-bracket disagreement stays a separate, review-only class.
usage: PYTHONPATH=run/tuplet_wt python export2.py <pid> ...   -> work/export/<pid>.json"""
import sys, os, json, collections, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fractions import Fraction
import labels2 as labels
import rhythm_tools as rt
from pieces2 import BY
from training.transformer.training_vocabulary import check_token_lines, max_ledger_lines, read_tokens, token_lines_to_str
from training.transformer.data_loader import MAX_ALLOWED_LEDGER_LINES
from homr.transformer.configs import Config
from training.omr_datasets.convert_lieder import MeasureCutter
from training.omr_datasets.tuplet_tokens import REJECTED
from align import bar_counters, f1 as f1c
BASE = "/Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso/batch2/work"
TOK = f"{BASE}/tokens"; os.makedirs(TOK, exist_ok=True)
F1_STRONG = 0.8; TOL = Fraction(1, 100)

def trainer_filter(path):
    try:
        t = read_tokens(path); check_token_lines(t)
    except Exception as e:  # noqa: BLE001
        return "vocab:" + repr(e)[:60]
    if len(t) > Config().max_seq_len - 2: return "long"
    if max_ledger_lines(t) > MAX_ALLOWED_LEDGER_LINES: return "ledger"
    return "ok"

def seq_sim(model_bars, label_bars):
    if not model_bars or not label_bars: return 0.0
    n = max(len(model_bars), len(label_bars))
    return sum(f1c(a, b) for a, b in zip(label_bars, model_bars)) / n

def bar_agree(groups, first_x, unit, L):
    if groups is None: return None
    if groups == L + 1: return True
    if groups == L and first_x is not None and unit and first_x > 4 * unit: return True
    return False

def clefs(txt):
    out = {"upper": None, "lower": None}
    for line in txt.split("\n")[:3]:
        for el in line.split("&"):
            m = re.match(r"clef_(\S+) .* (upper|lower)$", el.strip())
            if m and out[m[2]] is None: out[m[2]] = m[1]
    return out
def keysig(txt):
    m = re.search(r"keySignature_(-?\d+)", "\n".join(txt.split("\n")[:4])); return m[1] if m else None
def n_shift_starts(txt): return len(re.findall(r"octaveShift_8v[ab]", txt))

def export(pid):
    cfg = BY[pid]; a = json.load(open(f"{BASE}/assign/{pid}.json"))
    voices, report, bad_shift = labels.load(cfg["asap"]); v = voices[0]
    led = rt.ledger(cfg["asap"]); met = rt.meters(cfg["asap"]); ost = labels.octave_state(cfg["asap"])
    mc = MeasureCutter(list(v)); pos = 0; out = []
    reads = {}
    rf = f"{BASE}/reads/{cfg['pdf']}.jsonl"
    if os.path.exists(rf):
        for l in open(rf):
            r = json.loads(l); reads[r["id"]] = r
    for s in a["systems"]:
        rec = dict(pid=pid, id=s.get("id"), page=s.get("page"), sys=s.get("sys"), crop=s.get("crop"), bbox=s.get("bbox"),
                   page_shape=s.get("page_shape"), pdf=cfg["pdf"], reasons=[], tier=None, verification=None, rflags=[])
        if s.get("missing"): continue
        if not s.get("eligible"):
            rec["reasons"].append("skipped:" + s["skipped"] if s.get("skipped") else "crop:not_one_grand_staff"); out.append(rec); continue
        if "L" not in s: rec["reasons"].append("align:none"); out.append(rec); continue
        if s["L"] == 0: rec["reasons"].append("not_piece_music (before start/after end of the piece)"); out.append(rec); continue
        start, L = s["start"], s["L"]; meas = range(start, start + L)
        try:
            if start > pos: mc.extract_measures(start - pos); pos = start
            syms = mc.extract_measures(L); pos += L
        except Exception as e:  # noqa: BLE001
            rec["reasons"].append("conversion error: " + repr(e)[:80]); out.append(rec)
            pos = start + L; mc = MeasureCutter(list(v)[pos:]) if pos < len(v) else mc
            continue
        try:
            txt = token_lines_to_str(syms)
        except Exception as e:  # noqa: BLE001
            rec["reasons"].append("conversion error: " + repr(e)[:60]); out.append(rec); continue
        name = f"{pid}_{s['page']}_s{s['sys']}"
        tp = f"{TOK}/{name}.tokens"; open(tp, "w").write(txt)
        rec.update(tokens=tp, measures=[start, start + L], L=L, gap=s["gap"], f1=s.get("f1"), f1_pc=s.get("f1_pc"),
                   label_notes=s.get("label_notes"), model_notes=s.get("model_notes_n"), groups=s.get("groups"), name=name)
        rd = reads.get(s["id"])
        rec["model_bars"] = rd["n_bars"] if rd and "n_bars" in rd else None
        rec["trainer"] = trainer_filter(tp)
        # --- tuplets / rhythm (independent of the tier)
        ev = report.events_in(meas)
        rec["rounded"] = "; ".join(f"{k} x{c}" for k, c in collections.Counter(f"{e.written} {e.actual}:{e.normal}->note_{e.choice.kern}" for e in ev if e.choice.status in ("rounded", "rest_equivalent")).items())
        rounded_m = {e.measure for e in ev if e.choice.status in ("rounded", "rest_equivalent")}
        rej = [e for e in ev if e.choice.status == REJECTED]
        if rej: rec["rflags"].append("tuplet not representable: " + rej[0].choice.reason[:70] + (" (x%d)" % len(rej) if len(rej) > 1 else ""))
        bm = [m for m in meas if m in bad_shift]
        if bm: rec["rflags"].append(bad_shift[bm[0]])
        info = rt.bar_info(txt)
        over, diff = [], []
        for i in range(L):
            inf = info[i] if i < len(info) else {}
            for tag in ("upper", "lower"):
                true = led[start + i].get(tag)
                if true is None: continue
                t = inf.get(tag, dict(sum=Fraction(0), lines=0, rests=0))
                if t["lines"] == 1 and t["rests"] == 1: continue      # a bar rest
                if met[start + i] is not None and true > met[start + i] + TOL: over.append(start + i)
                if abs(t["sum"] - true) > TOL and (start + i) not in rounded_m: diff.append(start + i)
        if over: rec["rflags"].append("rhythm: MusicXML bar longer than the meter (cadenza) at measure %d" % (over[0] + 1))
        elif diff: rec["rflags"].append("rhythm: token duration sum differs from the MusicXML in measure %d (outside a rounded group)" % (diff[0] + 1))
        # --- octave roles from the XML brackets
        so, eo = ost[start][0], ost[start + L - 1][1]
        has_tok = n_shift_starts(txt) > 0 or "octaveShiftStop" in txt
        rec["oct_start_inside"] = bool(so); rec["oct_end_inside"] = bool(eo); rec["oct_in_label"] = bool(has_tok)
        rec["oct_stop_in_crop"] = bool(so and "octaveShiftStop" in txt)
        rec["bars_ok"] = bar_agree(s.get("groups"), s.get("first_x"), s.get("unit"), L)
        # --- agreement of the free read (pitch / pitch+onset)
        if rd and rd.get("tokens"):
            m = rt.agreement(txt, rd["tokens"]); rec["read_pitch_f1"] = round(m["pitch_f1"], 4); rec["read_onset_f1"] = round(m["onset_f1"], 4)
            cl, cr = clefs(txt), clefs(rd["tokens"]); kl, kr = keysig(txt), keysig(rd["tokens"])
            ck = [w for w, x, y in (("clef", cl, cr), ("key", kl, kr)) if x != y]
            rec["clef_key"] = ck; rec["clef_label"] = cl; rec["clef_read"] = cr; rec["key_label"] = kl; rec["key_read"] = kr
            rec["oct_n_label"] = n_shift_starts(txt); rec["oct_n_read"] = n_shift_starts(rd["tokens"])
        out.append(rec)
    asg = [r for r in out if "tokens" in r]
    for r in asg:
        f1 = r["f1"]
        if r["trainer"] != "ok":
            r["reasons"].append("trainer:" + r["trainer"].split(":")[0]); continue
        if f1 is None: r["reasons"].append("no model read"); continue
        if r["bars_ok"] and f1 >= F1_STRONG: r["tier"], r["verification"] = "strong", "bars+model"
        elif r["bars_ok"] is not True and f1 >= F1_STRONG and r["model_bars"] is not None and abs(r["model_bars"] - r["L"]) <= 1: r["tier"], r["verification"] = "strong", "model_bars"
        elif r["bars_ok"]:
            if r["f1_pc"] is not None and r["f1_pc"] >= 0.9 and r["f1_pc"] - f1 >= 0.25: (r["reasons"].append("octave shift (pitch classes agree, octaves differ)"), r.__setitem__("octave_pre_tier", "hard"))
            else: r["tier"], r["verification"] = "hard", "bars"
        elif r["bars_ok"] is None and r["model_bars"] is not None and abs(r["model_bars"] - r["L"]) <= 1: r["tier"], r["verification"] = "hard", "model_bars"
        else: r["reasons"].append("bar mismatch")
    for r in asg:
        if r["tier"] == "hard" and r.get("id") in reads and "tokens" in reads[r["id"]]:
            lk = re.findall(r"keySignature_(-?\d+)", open(r["tokens"]).read()); mk = re.findall(r"keySignature_(-?\d+)", reads[r["id"]]["tokens"])
            if lk and mk and lk[0] != mk[0]:
                r["tier"], r["verification"] = None, None
                r["reasons"].append("edition mismatch (key signature %s in the label, %s in the scan read)" % (lk[0], mk[0]))
    # octave brackets: label and the released model's read must agree on whether the system carries an 8va/8vb sign; otherwise OCTAVE-UNVERIFIED (eye review, not trained unreviewed)
    for r in asg:
        if r["tier"] and r.get("id") in reads and "tokens" in reads[r["id"]]:
            lab_has = bool(re.search("octaveShift", open(r["tokens"]).read())); mod_has = bool(re.search("octaveShift", reads[r["id"]]["tokens"]))
            r["octave_label"], r["octave_model"] = lab_has, mod_has
            if lab_has != mod_has:
                r["octave_pre_tier"] = r["tier"]
                r["tier"], r["verification"] = None, None
                r["reasons"].append("octave-bracket disagreement (label %s an 8va/8vb sign, the released model's read %s one)" % ("has" if lab_has else "lacks", "has" if mod_has else "lacks"))
    meas_c = [collections.Counter(sym.pitch for sym in m if sym.rhythm.startswith("note")) for m in v]
    for r in asg:
        if r["tier"] != "hard": continue
        rd = reads.get(r["id"]); mb = bar_counters(rd["notes"]); st, en = r["measures"]
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
    # rhythm flags demote (the crop's pitch/bar verification stays recorded in octave_pre_tier / tier_before_rhythm)
    for r in asg:
        if r["rflags"]:
            r["tier_before_rhythm"] = r["tier"]
            r["tier"], r["verification"] = None, None
            r["reasons"].extend(r["rflags"])
        if r["tier"] is None and not r["reasons"]: r["reasons"].append("unclassified")
    for i, r in enumerate(asg):
        if r["tier"] is None and r["gap"] and "bar mismatch" in r["reasons"]:
            r["reasons"].append("edition mismatch? (measures skipped before this system)")
    os.makedirs(f"{BASE}/export", exist_ok=True)
    json.dump(dict(pid=pid, n_measures=len(v), end=a["end"], records=out), open(f"{BASE}/export/{pid}.json", "w"), default=str)
    c = collections.Counter(r["tier"] or "quarantine" for r in asg)
    nou = sum(1 for r in asg if r["reasons"] and all(x.startswith(("octave-bracket disagreement", "octave shift (pitch")) for x in r["reasons"]))
    print(pid, cfg["title"], dict(c), "octave-unverified-only:", nou, "non-assigned:", len(out) - len(asg), "end", a["end"], "/", len(v))

if __name__ == "__main__":
    for pid in sys.argv[1:]: export(pid)
