"""FINAL comparison of the scan pilot: SCAN minus CTRL_RENDER, per seed (7 and 11), on (a) the 28 real scans and (b) the held-out passages.

Prepared 2026-11-17 (Pacific), NOT RUN until the four pilot models are evaluated by eval_run1/pilot_auto.sh (log eval_run1/pilot_auto.log).
Plan: run/PLAN.md section 1 items 3 and 5; spec: run/scan_pairs_virtuoso/PILOT_SPEC.md (sections 5 and 7).

(a) 28 real scans, GPU harness of the resolution experiment (res_eval.py, tags pilot_<ARM>_s<SEED>_gpu), edition-corrected references for every column
    (Schubert D. 899/4 re-scored against the edition reference by res_final_table.py's machinery, which this script imports), visible notes only:
    staff-sensitive pitch / +onset / full, pooled (staff-ignored) pitch / +onset / full, pieces at 97 (pooled, staff-sensitive, and on every staff),
    per-piece paired differences SCAN - CTRL_RENDER per seed (mean +- range of the two seeds, wins / losses, sign test), dense-bar recall (bars with >= 24 notes).
    Context columns: the released model (laptop CPU, after the merger fixes) and the run3 controls res_A_s7_gpu / res_A_s11_gpu (same recipe, NO pilot data).
(b) held-out read of the pilot validation passages (eval_run1/pilot_val/<model>/<list>.json, pilot_val_eval.py, GPU): the 72 v2 validation passages
    (Liszt TE3 = C1, Schubert D.899/2 = C3) and the independent 145-crop extension (batch2_val_v2: Gnomenreigen N2, Etude Op.10/5 N4, Beethoven Op.81a N11 and N12),
    each as scan and as rendered twin (the extension twin exists for the 134 crops that render), by work: mean pitch F1 and (pitch, rhythm) F1, both seeds,
    the spread between seeds, SCAN - CTRL_RENDER per crop (seeds averaged, bootstrap 95 % interval over crops) and per seed.

Single-run caveat (printed in the table): one training run per arm and seed. Differences that are inside the seed spread of the earlier controls
(res_A_s7_gpu vs res_A_s11_gpu: mean absolute pooled-pitch difference per piece, 0.70 points when written) are NOT evidence of an effect.

usage: /Users/yiduoke/Documents/homr/.venv/bin/python eval_run1/pilot_final_table.py [--ctrl7 TAG --ctrl11 TAG --scan7 TAG --scan11 TAG] [--name SUFFIX] [--date YYYY-MM-DD]
       [--no-heldout] [--no-scans] [--force-rescore]
  defaults: pilot_CTRL_RENDER_s7_gpu pilot_CTRL_RENDER_s11_gpu pilot_SCAN_s7_gpu pilot_SCAN_s11_gpu. (To test the machinery before the pilot exists:
  --ctrl7 res_A_s7_gpu --ctrl11 res_A_s11_gpu --scan7 res_B_s7_gpu --scan11 res_B_s11_gpu --name TEST; the held-out part then reports the models as missing.)
A missing tag, piece or list is reported as missing and left out; nothing is filled in.
Output: out/testset/PILOT-final-table-<date>[-<name>].md
"""
import argparse
import csv
import datetime
import json
import math
import os
import random
import statistics as st
import sys
import zoneinfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import res_lib as L  # noqa: E402
import res_final_table as F  # noqa: E402  (the loaders, the Schubert edition re-scoring, the sign test)

T, P = L.OUT, F.P
TIE = F.TIE
RUN = L.R
VAL = f"{HERE}/pilot_val"
YARD_NOTE = "0.70 (mean absolute pooled-pitch difference per piece between seeds 7 and 11 of the earlier controls)"


def fmt(x, nd=2, sign=False):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n/a"
    return f"{x:+.{nd}f}" if sign else f"{x:.{nd}f}"


def staff_f1s(tag: str, piece: str):
    """Per printed staff pitch F1 (percent) of the staff-sensitive score of one GPU-harness tag; None if not available."""
    path = f"{P}/{piece}/{tag}-edition.json" if piece in F.EDITION else L.score_path(tag, piece)
    if not os.path.exists(path):
        return None
    m = json.load(open(path))["results"][0]["metrics"]["pitch_inventory"]
    return [s["f1"] * 100 for s in m["staves"]] if "staves" in m else None


# ------------------------------------------------------------------ held-out
def works():
    """pid -> work name from the manifests of the pilot (A-C) and of batch 2 (N)."""
    out = {}
    for f in (f"{RUN}/scan_pairs_virtuoso/manifest.csv", f"{RUN}/scan_pairs_virtuoso/batch2/manifest.csv"):
        for r in csv.DictReader(open(f)):
            out.setdefault(r["pid"], r["piece"])
    return out


def load_val(model: str, key: str):
    f = f"{VAL}/{model}/{key}.json"
    return json.load(open(f)) if os.path.exists(f) else None


def boot_ci(d, n=5000, seed=20261118):
    rnd = random.Random(seed)
    m = len(d)
    if m == 0:
        return None
    bs = sorted(sum(d[rnd.randrange(m)] for _ in range(m)) / m for _ in range(n))
    return bs[int(0.025 * n)], bs[int(0.975 * n)]


def heldout(out, models, labels, ctrl, scan, wk):
    """models: ordered list of model names; ctrl/scan: {seed: model}."""
    out += ["## 6. Held-out passages (never trained on; free generation per staff crop, GPU)", "",
            "`pilot_val_eval.py`: per crop the pitch-multiset F1 and the (pitch, rhythm-token) F1 of the read against the label, bar-count agreement, exact multiset match; means over crops. "
            "These are NOT the onset-based scores of section 3. Lists: **val** = the 72 v2 validation passages (Liszt TE3 = C1, Schubert D.899/2 = C3); **ext** = the independent "
            "145-crop extension `batch2_val_v2` (four works). Each as the scan crop and as the rendered twin; the twins of the extension exist for 134 of the 145 crops (11 did not render: "
            "octave-bracket mismatch or touching notes), `ext scan (134)` is the scan of exactly those crops. Seeds: s7 / s11; spread = |s7 - s11|.", ""]
    lists = [("val_scan_v2", "val scan (72)"), ("val_twin_v2", "val twin (72)"), ("b2_scan", "ext scan (145)"), ("b2_scan_matched", "ext scan (134)"), ("b2_twin", "ext twin (134)")]
    data = {m: {k: load_val(m, k) for k, _ in lists} for m in models}
    miss = [f"{labels[m]} {k}" for m in models for k, _ in lists if not data[m][k]]
    out += ["Missing held-out results: " + (", ".join(miss) if miss else "none"), ""]

    def crops(m, k):
        d = data[m][k]
        return d["crops"] if d else {}

    # overall and per work, per model and list
    for metric, title in (("pitch_f1", "pitch F1"), ("pitch_rhythm_f1", "(pitch, rhythm) F1")):
        out += [f"### 6.{1 if metric == 'pitch_f1' else 2} Mean {title} by work (crops with a read; all values x100)", ""]
        for k, ktitle in lists:
            pids = sorted({n.split("_")[0] for m in models for n in crops(m, k)}, key=lambda p: (p[0] != "C", p))
            if not pids:
                continue
            out += [f"**{ktitle}**", "", "| work | crops | " + " | ".join(labels[m] for m in models) + " | spread CTRL (s7-s11) | spread SCAN |", "|---" * (len(models) + 4) + "|"]
            for pid in pids + ["ALL"]:
                cells = []
                for m in models:
                    c = crops(m, k)
                    v = [x[metric] for n, x in c.items() if pid == "ALL" or n.split("_")[0] == pid]
                    cells.append(fmt(100 * st.mean(v), 1) if v else "missing")
                nn = max((len([1 for n in crops(m, k) if pid == "ALL" or n.split("_")[0] == pid]) for m in models), default=0)
                sp = []
                for arms in (ctrl, scan):
                    a, b = [crops(arms.get(s), k) for s in (7, 11)] if 7 in arms and 11 in arms else ({}, {})
                    va = [x[metric] for n, x in a.items() if pid == "ALL" or n.split("_")[0] == pid]
                    vb = [x[metric] for n, x in b.items() if pid == "ALL" or n.split("_")[0] == pid]
                    sp.append(fmt(100 * abs(st.mean(va) - st.mean(vb)), 1) if va and vb else "n/a")
                name = "all crops" if pid == "ALL" else f"{pid} {wk.get(pid, '')}"
                out.append(f"| {name} | {nn} | " + " | ".join(cells) + f" | {sp[0]} | {sp[1]} |")
            out.append("")

    out += ["### 6.3 SCAN minus CTRL_RENDER on the same crops (paired per crop)", "",
            "Per crop d = SCAN - CTRL_RENDER (x100). `seeds avg` first averages the two seeds of each arm per crop (the contrast of the spec), then the mean and a bootstrap 95 % interval "
            "over crops (5,000 resamples, crops treated as independent although they come from few works: the interval is optimistic). `s7`, `s11`: the same with one seed. "
            "Wins / losses use a +-0.5 point band per crop.", ""]
    out += ["| list | metric | work | crops | s7 | s11 | seeds avg [95 % interval] | better / worse / equal (seeds avg) |", "|---|---|---|---|---|---|---|---|"]
    verdicts = []
    for k, ktitle in lists:
        for metric, mt in (("pitch_f1", "pitch"), ("pitch_rhythm_f1", "pitch+rhythm")):
            pids = sorted({n.split("_")[0] for n in crops(scan.get(7), k)} | {n.split("_")[0] for n in crops(scan.get(11), k)}, key=lambda p: (p[0] != "C", p))
            for pid in pids + ["ALL"]:
                def sel(m):
                    return {n: x[metric] for n, x in crops(m, k).items() if pid == "ALL" or n.split("_")[0] == pid}
                per = {}
                for s in (7, 11):
                    a, b = sel(ctrl.get(s)), sel(scan.get(s))
                    com = sorted(set(a) & set(b))
                    per[s] = {n: b[n] - a[n] for n in com}
                both = sorted(set(per[7]) & set(per[11]))
                avg = [(per[7][n] + per[11][n]) / 2 * 100 for n in both]
                if not per[7] and not per[11]:
                    continue
                s7 = fmt(100 * st.mean(per[7].values()), 2, True) if per[7] else "n/a"
                s11 = fmt(100 * st.mean(per[11].values()), 2, True) if per[11] else "n/a"
                if avg:
                    ci = boot_ci(avg)
                    wins, loss = sum(x > 0.5 for x in avg), sum(x < -0.5 for x in avg)
                    cell = f"{st.mean(avg):+.2f} [{ci[0]:+.2f}, {ci[1]:+.2f}]"
                    bw = f"{wins} / {loss} / {len(avg) - wins - loss}"
                    if pid == "ALL":
                        verdicts.append((ktitle, mt, st.mean(avg), ci, per))
                else:
                    cell, bw = "n/a", "n/a"
                out.append(f"| {ktitle} | {mt} | {'all' if pid == 'ALL' else pid + ' ' + wk.get(pid, '')} | {len(both) if both else max(len(per[7]), len(per[11]))} | {s7} | {s11} | {cell} | {bw} |")
    out.append("")
    return verdicts


# ------------------------------------------------------------------ main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ctrl7", default="pilot_CTRL_RENDER_s7_gpu")
    ap.add_argument("--ctrl11", default="pilot_CTRL_RENDER_s11_gpu")
    ap.add_argument("--scan7", default="pilot_SCAN_s7_gpu")
    ap.add_argument("--scan11", default="pilot_SCAN_s11_gpu")
    ap.add_argument("--run3-7", default="res_A_s7_gpu")
    ap.add_argument("--run3-11", default="res_A_s11_gpu")
    ap.add_argument("--baseline", default="layout1")
    ap.add_argument("--name", default="")
    ap.add_argument("--date", default=datetime.datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d"))
    ap.add_argument("--force-rescore", action="store_true")
    ap.add_argument("--no-heldout", action="store_true")
    ap.add_argument("--no-scans", action="store_true")
    ap.add_argument("--val-models", nargs=7, metavar="M", help="held-out model names: released run3_s7 run3_s11 ctrl7 ctrl11 scan7 scan11 (default derived from the tags)")
    a = ap.parse_args()
    pieces = L.pieces28()
    n_all = len(pieces)
    out_lines = []
    tags_ctrl, tags_scan = {7: a.ctrl7, 11: a.ctrl11}, {7: a.scan7, 11: a.scan11}
    tags_r3 = {7: a.run3_7, 11: a.run3_11}
    tag_all = [a.run3_7, a.run3_11, a.ctrl7, a.ctrl11, a.scan7, a.scan11]
    label = {a.baseline: "released", a.run3_7: "run3 ctrl s7", a.run3_11: "run3 ctrl s11", a.ctrl7: "CTRL_RENDER s7", a.ctrl11: "CTRL_RENDER s11",
             a.scan7: "SCAN s7", a.scan11: "SCAN s11"}
    cols = [a.baseline] + tag_all
    pacific = datetime.datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d %H:%M %Z")
    out = [f"# Scan pilot, final comparison: SCAN minus CTRL_RENDER, seeds 7 and 11, {a.date}", "",
           f"Generated {pacific} by `eval_run1/pilot_final_table.py`. Question (advisor): do real engravings add value beyond the notes themselves? Both arms start from the released `run2s7` weights, "
           "use the run3 recipe (6,716 updates, 256x1280) and see the same 881 passages 15 times in the mixture (R = 8), as the scanned crop (SCAN) or as the rendered twin (CTRL_RENDER). "
           "Spec: `scan_pairs_virtuoso/PILOT_SPEC.md`; plan: `PLAN.md` section 1, items 3 and 5. The training lists exclude every test piece and every validation work.", "",
           "**Single run per arm and seed.** The earlier controls (same recipe, different seeds) differ per piece by " + YARD_NOTE + ". A difference between the arms that is inside this spread, "
           "or that has a different sign in the two seeds, is not evidence of an effect; the tables mark it. Per-seed numbers are never averaged away: the spread is printed next to every mean.", ""]

    status = {}
    data = {}
    if not a.no_scans:
        for t in tag_all:
            for ep in sorted(F.EDITION & set(pieces)):
                status[t] = F.rescore_edition_piece(ep, t, a.force_rescore)
        data = {t: {p: F.load_res_tag(t, p) for p in pieces} for t in tag_all}
        data[a.baseline] = {p: F.load_baseline(a.baseline, p, True) for p in pieces}
        present = {c: [p for p in pieces if data[c][p]] for c in cols}
        missing = {c: [p for p in pieces if not data[c][p]] for c in cols}
        sf = {t: {p: staff_f1s(t, p) for p in present[t]} for t in tag_all}

        out += ["## 1. Runs (28 real scans)", "", "| column | tag | pieces scored | Schubert re-score | missing |", "|---|---|---|---|---|"]
        for c in cols:
            out.append(f"| {label[c]} | `{c}` | {len(present[c])} of {n_all}{' (partial)' if len(present[c]) < n_all else ''} | {status.get(c, 'existing -edition files')} | "
                       f"{', '.join(missing[c]) if missing[c] else 'none'} |")
        out.append("")

        # ---- 2 summary
        def summ(c):
            rows = {p: data[c][p] for p in present[c]}
            if not rows:
                return None
            pr = lambda f: F.mean(f(r) for r in rows.values())  # noqa: E731
            worst = min(rows, key=lambda p: rows[p]["pooled"]["f1"])
            ds = [r["dense"] for r in rows.values() if r["dense"]]
            notes, missed = sum(d["dense_reference_notes"] for d in ds), sum(d["dense_missed_pitch"] for d in ds)
            every = None
            if c in sf:
                every = sum(1 for p in rows if sf[c].get(p) and all(x >= 97 for x in sf[c][p]))
            return dict(n=len(rows), sens=pr(lambda r: r["sens"]["f1"]), sens_po=pr(lambda r: r["sens"]["po"]), sens_full=pr(lambda r: r["sens"]["full"]),
                        pool=pr(lambda r: r["pooled"]["f1"]), po=pr(lambda r: r["pooled"]["po"]), full=pr(lambda r: r["pooled"]["full"]),
                        at97=sum(r["pooled"]["f1"] >= 97 for r in rows.values()), at97s=sum(r["sens"]["f1"] >= 97 for r in rows.values()), every=every,
                        worst=worst, worstv=rows[worst]["pooled"]["f1"], beq=sum(r["bars_equal"] for r in rows.values()),
                        recall=100 * (notes - missed) / notes if notes else None, missed=missed)
        S = {c: summ(c) for c in cols}
        out += ["## 2. Summary per run (macro means over the pieces scored)", "",
                "| run | pieces | staff-sens pitch | staff-sens +onset | staff-sens full | pooled pitch | pooled +onset | pooled full | at 97 staff-sens | at 97 on every staff | at 97 pooled | worst piece (pooled) | bar count = ref | dense recall % | dense missed |",
                "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for c in cols:
            s = S[c]
            if not s:
                out.append(f"| {label[c]} | 0 | missing |" + " |" * 12)
                continue
            part = "" if s["n"] == n_all else f" (partial {s['n']} of {n_all})"
            out.append(f"| {label[c]}{part} | {s['n']} | {s['sens']:.2f} | {s['sens_po']:.2f} | {s['sens_full']:.2f} | {s['pool']:.2f} | {s['po']:.2f} | {s['full']:.2f} | {s['at97s']} | "
                       f"{s['every'] if s['every'] is not None else 'n/a'} | {s['at97']} | {s['worst']} {s['worstv']:.1f} | {s['beq']} of {s['n']} | "
                       f"{fmt(s['recall'], 2)} | {s['missed']} |")
        out += ["", "The released column is the laptop CPU run of the released model after the merger fixes (not the same hardware as the GPU columns; context only). The run3 columns are the same "
                "recipe with no pilot data. Petrushka is provisional (three reference staves against two of ours). `at 97 on every staff` = both printed staves at or above 97 staff-sensitive pitch F1.", ""]

        # seed spreads of the same arm
        def macro(t, f):
            return F.mean(f(data[t][p]) for p in present[t])
        yard = {}
        for nm, t7, t11 in (("run3 ctrl", a.run3_7, a.run3_11), ("CTRL_RENDER", a.ctrl7, a.ctrl11), ("SCAN", a.scan7, a.scan11)):
            both = [p for p in pieces if data[t7][p] and data[t11][p]]
            if both:
                d = [data[t11][p]["pooled"]["f1"] - data[t7][p]["pooled"]["f1"] for p in both]
                yard[nm] = dict(mean_abs=F.mean(abs(x) for x in d), macro=F.mean(d), n=len(both))
        out += ["### Seed spread of each arm (pooled pitch, s11 - s7 per piece)", "", "| arm | pieces | mean absolute difference per piece | difference of the macro means |", "|---|---|---|---|"]
        for nm, y in yard.items():
            out.append(f"| {nm} | {y['n']} | {y['mean_abs']:.2f} | {y['macro']:+.2f} |")
        out.append("")
        ctl_yard = yard.get("run3 ctrl", {}).get("mean_abs")

        # ---- 3 paired
        pairs = [(s, tags_ctrl[s], tags_scan[s]) for s in (7, 11)]
        usable = {s: [p for p in pieces if data[ta][p] and data[tb][p]] for s, ta, tb in pairs}
        METRICS = [("pooled pitch F1", lambda r: r["pooled"]["f1"]), ("staff-sensitive pitch F1", lambda r: r["sens"]["f1"]),
                   ("staff-sensitive pitch+onset F1", lambda r: r["sens"]["po"]), ("staff-sensitive full F1", lambda r: r["sens"]["full"]),
                   ("pooled pitch+onset F1", lambda r: r["pooled"]["po"]), ("pooled full F1", lambda r: r["pooled"]["full"]),
                   ("dense-bar recall of pitches", lambda r: None if not r["dense"] or r["dense"]["dense_recall_pitch"] is None else 100 * r["dense"]["dense_recall_pitch"])]
        out += ["## 3. SCAN minus CTRL_RENDER on the 28 scans (same seed = same start weights, list, steps and data order; only scanned crop against rendered twin differs)", ""]
        for s, ta, tb in pairs:
            out.append(f"* seed {s}: CTRL_RENDER `{ta}`, SCAN `{tb}`, {len(usable[s])} of {n_all} pieces in both"
                       + ("" if len(usable[s]) == n_all else " (left out: " + ", ".join(p for p in pieces if p not in usable[s]) + ")"))
        out.append("")
        summary_lines = []
        paired = {}
        for title, fn in METRICS:
            per = {}
            for s, ta, tb in pairs:
                for p in usable[s]:
                    x, y = fn(data[ta][p]), fn(data[tb][p])
                    if x is not None and y is not None:
                        per.setdefault(p, {})[s] = (x, y)
            if not per:
                continue
            paired[title] = per
            seeds = [s for s, *_ in pairs]
            hdr = ["piece"] + [f"CTRL s{s}" for s in seeds] + [f"SCAN s{s}" for s in seeds] + [f"d s{s}" for s in seeds] + ["mean d +- range", "verdict"]
            out += [f"### 3.{len(paired)} {title}", "", "| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
            win = loss = tie = agree = 0
            per_seed = {s: [] for s in seeds}
            for p in pieces:
                if p not in per:
                    continue
                pp = per[p]
                ds = {s: pp[s][1] - pp[s][0] for s in pp}
                m = F.mean(ds.values())
                sdv = abs(max(ds.values()) - min(ds.values())) if len(ds) == 2 else None
                v = "SCAN better" if m > TIE else "SCAN worse" if m < -TIE else "tie"
                ag = len(ds) == 2 and (all(d > TIE for d in ds.values()) or all(d < -TIE for d in ds.values()))
                win, loss, tie, agree = win + (v == "SCAN better"), loss + (v == "SCAN worse"), tie + (v == "tie"), agree + ag
                for s in ds:
                    per_seed[s].append(ds[s])
                row = [p] + [f"{pp[s][0]:.1f}" if s in pp else "n/a" for s in seeds] + [f"{pp[s][1]:.1f}" if s in pp else "n/a" for s in seeds]
                row += [f"{ds[s]:+.2f}" if s in ds else "n/a" for s in seeds] + [f"{m:+.2f}" + (f" +- {sdv / 2:.2f}" if sdv is not None else ""), v + (" (both seeds)" if ag else "")]
                out.append("| " + " | ".join(row) + " |")
            D = {s: F.mean(v) for s, v in per_seed.items() if v}
            line = (f"Mean SCAN - CTRL per seed: " + ", ".join(f"s{s} {D[s]:+.2f} ({len(per_seed[s])} pieces)" for s in D)
                    + (f"; mean {F.mean(D.values()):+.2f}, spread between the seeds' differences {abs(D[7] - D[11]):.2f}" if len(D) == 2 else "")
                    + f". SCAN better on {win}, worse on {loss}, tie {tie} (band {TIE}); both seeds agree beyond the band on {agree}; sign test over the {win + loss} decided pieces p = {F.sign_test(win, loss):.3f}.")
            out += ["", line, ""]
            summary_lines.append((title, D, win, loss, agree, F.sign_test(win, loss)))

        # ---- regressions (AGENTS.md: original scans must not get worse)
        pp = paired.get("pooled pitch F1", {})
        pps = paired.get("staff-sensitive pitch F1", {})
        out += ["### 3.x Pieces where SCAN is worse than CTRL_RENDER by 1 point or more", "",
                "Rule: change of at least -1.0 point in the same direction in both seeds (a single-seed drop is listed separately). The repository rule is that original scans must not get worse; "
                "a better average does not excuse a worse page.", ""]
        for nm, perm in (("pooled pitch", pp), ("staff-sensitive pitch", pps)):
            both_w = [p for p in pieces if p in perm and len(perm[p]) == 2 and all(v[1] - v[0] <= -1 for v in perm[p].values())]
            one_w = [p for p in pieces if p in perm and p not in both_w and any(v[1] - v[0] <= -1 for v in perm[p].values())]
            desc = lambda p, perm=perm: ", ".join(f"s{s} {v[1] - v[0]:+.1f}" for s, v in sorted(perm[p].items()))  # noqa: E731
            out.append(f"* {nm}, both seeds: " + (", ".join(f"{p} ({desc(p)})" for p in both_w) if both_w else "none")
                       + "; one seed only: " + (", ".join(f"{p} ({desc(p)})" for p in one_w) if one_w else "none"))
        out.append("")
        out += ["### 3.y Where SCAN is better by 1 point or more in both seeds (pooled pitch)", ""]
        better = [(p, pp[p]) for p in pieces if p in pp and len(pp[p]) == 2 and all(v[1] - v[0] >= 1 for v in pp[p].values())]
        out.append(", ".join(f"{p} ({', '.join(f's{s} {v[1] - v[0]:+.1f}' for s, v in sorted(x.items()))})" for p, x in better) if better else "none")
        out.append("")

        # ---- context vs run3 control
        out += ["## 4. Context: both pilot arms against the run3 control (same recipe, no pilot data) and the released model", "",
                "Mean over pieces scored in both runs of the pair, difference of the macro means per seed (pooled pitch, staff-sensitive pitch, pooled +onset, pooled full, dense recall). "
                "The run3 control saw the base list 2.00 times, the pilot arms 1.88 times plus 15 passes over the 881 pilot passages.", "",
                "| pair | pooled pitch s7 | s11 | staff-sens pitch s7 | s11 | pooled +onset s7 | s11 | pooled full s7 | s11 | dense recall s7 | s11 |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        fns = [lambda r: r["pooled"]["f1"], lambda r: r["sens"]["f1"], lambda r: r["pooled"]["po"], lambda r: r["pooled"]["full"],
               lambda r: None if not r["dense"] or r["dense"]["dense_recall_pitch"] is None else 100 * r["dense"]["dense_recall_pitch"]]
        for nm, tg in (("CTRL_RENDER - run3 ctrl", tags_ctrl), ("SCAN - run3 ctrl", tags_scan)):
            cells = []
            for fn in fns:
                for s in (7, 11):
                    com = [p for p in pieces if data[tg[s]][p] and data[tags_r3[s]][p] and fn(data[tg[s]][p]) is not None and fn(data[tags_r3[s]][p]) is not None]
                    cells.append(fmt(F.mean(fn(data[tg[s]][p]) - fn(data[tags_r3[s]][p]) for p in com), 2, True) if com else "n/a")
            out.append(f"| {nm} | " + " | ".join(cells) + " |")
        out.append("")

        # ---- per piece, all columns
        def piece_table(title, fn, note=""):
            out.extend([f"### {title}", ""] + ([note, ""] if note else []))
            out.append("| piece | " + " | ".join(label[c] for c in cols) + " |")
            out.append("|---" * (1 + len(cols)) + "|")
            for p in pieces:
                mark = " *" if p in F.SCHOTT else (" (provisional)" if p == F.PETRUSHKA else "")
                out.append(f"| {p}{mark} | " + " | ".join("**missing**" if not data[c][p] else fn(data[c][p]) for c in cols) + " |")
            out.append("")
        out += ["## 5. Per piece, all columns", "", "Percent F1. `*` = Schott scan (released column re-merged). Bold = below 97 in the pooled table."]
        out.append("")
        piece_table("5a. Pooled sounding-pitch F1", lambda r: f"{r['pooled']['f1']:.1f}" if r["pooled"]["f1"] >= 97 else f"**{r['pooled']['f1']:.1f}**")
        piece_table("5b. Staff-sensitive pitch F1", lambda r: f"{r['sens']['f1']:.1f}")
        piece_table("5c. Staff-sensitive pitch + onset F1", lambda r: f"{r['sens']['po']:.1f}")
        piece_table("5d. Pooled pitch + onset F1", lambda r: f"{r['pooled']['po']:.1f}")
        piece_table("5e. Pooled full F1", lambda r: f"{r['pooled']['full']:.1f}")
        piece_table("5f. Dense-bar recall of pitches % (bars with >= 24 notes; missed in brackets)",
                    lambda r: "n/a" if not r["dense"] or r["dense"]["dense_recall_pitch"] is None else f"{100 * r['dense']['dense_recall_pitch']:.1f} ({r['dense']['dense_missed_pitch']})")
        piece_table("5g. Bars: ours / reference", F.bars_str)
    else:
        summary_lines, ctl_yard, yard, S = [], None, {}, {}

    # ---- held-out
    verdicts = []
    if not a.no_heldout:
        vm = a.val_models or ["released", "run3_ctrl_s7", "run3_ctrl_s11", a.ctrl7.removesuffix("_gpu"), a.ctrl11.removesuffix("_gpu"), a.scan7.removesuffix("_gpu"), a.scan11.removesuffix("_gpu")]
        vlabel = dict(zip(vm, ["released", "run3 ctrl s7", "run3 ctrl s11", "CTRL_RENDER s7", "CTRL_RENDER s11", "SCAN s7", "SCAN s11"]))
        verdicts = heldout(out, vm, vlabel, {7: vm[3], 11: vm[4]}, {7: vm[5], 11: vm[6]}, works())

    # ---- plain reading
    out += ["## 7. Reading (generated from the numbers above; check against the tables)", ""]
    if summary_lines:
        for title, D, win, loss, agree, p in summary_lines:
            if len(D) == 2:
                same = (D[7] > 0) == (D[11] > 0)
                ymax = max([abs(y["macro"]) for y in yard.values()] or [0.0])
                bigger = [s for s in (7, 11) if abs(D[s]) > ymax]
                out.append(f"* 28 scans, {title}: SCAN - CTRL_RENDER {D[7]:+.2f} (s7) and {D[11]:+.2f} (s11); the sign is {'the same' if same else 'different'} in the two seeds; "
                           f"{win} pieces better, {loss} worse, {agree} agreeing in both seeds; sign test p = {p:.3f}. "
                           f"The largest seed-to-seed difference of a macro mean in any arm of this experiment (pooled pitch, section 2) is {ymax:.2f}: "
                           + ("both differences are inside it, so they cannot be told from seed noise." if not bigger else
                              f"the difference of seed{'s' if len(bigger) == 2 else ''} {' and '.join(map(str, bigger))} is larger, but with one run per arm and seed that is still not a confidence statement."))
            elif D:
                s = next(iter(D))
                out.append(f"* 28 scans, {title}: one seed only (s{s}) {D[s]:+.2f}; provisional.")
    for ktitle, mt, m, ci, per in verdicts:
        sign_same = per[7] and per[11] and ((st.mean(per[7].values()) > 0) == (st.mean(per[11].values()) > 0))
        out.append(f"* held-out {ktitle}, {mt}: SCAN - CTRL_RENDER {m:+.2f} points over crops (seeds averaged), interval [{ci[0]:+.2f}, {ci[1]:+.2f}]; "
                   f"{'interval excludes 0' if ci[0] > 0 or ci[1] < 0 else 'interval includes 0'}; sign {'same' if sign_same else 'different'} in the two seeds.")
    if not summary_lines and not verdicts:
        out.append("No comparison available yet.")
    out += ["", "Everything above is one training run per arm and seed, 28 scans from 28 works, 72 + 145 held-out crops from six works. Two seeds give a range, not a confidence interval."]
    path = f"{T}/PILOT-final-table-{a.date}{'-' + a.name if a.name else ''}.md"
    open(path, "w").write("\n".join(out) + "\n")
    print("\n".join(out[: out.index("## 3. SCAN minus CTRL_RENDER on the 28 scans (same seed = same start weights, list, steps and data order; only scanned crop against rendered twin differs)")] if not a.no_scans else out[:20]))
    print("wrote", path)


if __name__ == "__main__":
    main()
