"""D28 task 3: where do the remaining note errors come from, per category, for tags audited with pitch_audit_brace.py.
usage: python brace_audit_summary.py TAG [TAG ...]  -> prints markdown, writes brace_models/audit_<tag>.md
Loss unit: F1 points = (missed reference notes + extra output notes of the category) / (reference + output notes), micro over the pieces
(sum over pieces) and macro (mean of the per-piece figures). Lost bars = category 1. 'Repeated-note runs': reference notes in a run of
>= 4 successive events of one staff with the same pitch set (one bar), counted among the missed notes of categories 7a/7b."""
import json
import os
import sys
from collections import Counter, defaultdict

os.environ["AUDIT_VISIBLE"] = "1"
sys.path.insert(0, "/Users/yiduoke/Documents/homr/run/eval_run1")
import pitch_audit as PA  # noqa: E402

E = "/Users/yiduoke/Documents/homr/run/eval_run1"
T = "/Users/yiduoke/Documents/homr/run/out/testset"
CATS = PA.CATS
SCHOTT = {"liszt-sonata", "liszt-te-5", "liszt-te-10"}


def run_notes(piece, ignore):
    """set of (ref_bar, name, onset) of reference notes inside a run of >= 4 equal events on one staff."""
    parts, _ = PA.read_file(f"{T}/{piece}/{piece}-reference{'-edition' if piece == 'schubert-impromptu-d899-4' else ''}.musicxml")
    nb = len(parts[0][0])
    out, total = set(), 0
    for i in range(nb):
        by = defaultdict(lambda: defaultdict(list))
        for bars, _, _ in parts:
            for n in bars[i].notes:
                if not n.grace:
                    by[1 if ignore else n.staff][round(n.onset, 3)].append(n)
                    total += 1
        for st, ev in by.items():
            seq = sorted(ev)
            k = 0
            while k < len(seq):
                j = k
                key = tuple(sorted(n.pitch for n in ev[seq[k]]))
                while j + 1 < len(seq) and tuple(sorted(n.pitch for n in ev[seq[j + 1]])) == key:
                    j += 1
                if j - k + 1 >= 4:
                    for o in seq[k:j + 1]:
                        out.update((i + 1, n.name(), o) for n in ev[o])
                k = j + 1
    return out, total


def summarize(tag):
    d = json.load(open(f"{E}/brace_audit_{tag}.json"))["audit"]
    lines = [f"## {tag}\n"]
    micro, macro = Counter(), Counter()
    den_all = 0
    ev = Counter()
    lost_bars = ref_bars = 0
    run_ref = run_missed = run_total_missed = 0
    fam_den = 0
    n = 0
    rows = []
    for p in sorted(d):
        a = d[p]
        den = a["nref"] + a["npred"]
        den_all += den
        n += 1
        for c in CATS:
            micro[c] += a["loss_notes"][c]
            macro[c] += 100 * a["loss_notes"][c] / den
            ev[c] += a["events"][c]
        lb = a["ref_bars"] - a["aligned_bars"]
        lost_bars += lb
        ref_bars += a["ref_bars"]
        rn, tot = run_notes(p, a["ignore_staff"])
        for r in a["recs"]:
            if r["cat"] in ("7a chord member missing", "7b whole event missing") and r["ref_bar"] is not None:
                for s, name, on, _ in r["ref"]:
                    run_total_missed += 1
                    if (r["ref_bar"], name, round(on, 3)) in rn:
                        run_missed += 1
        run_ref += len(rn)
        rows.append((p, a, den, lb))
    short = {c: c.split(" ", 1)[1] for c in CATS}
    tot_loss = sum(micro.values())
    lines.append(f"{n} pieces audited, {sum(a['nref'] for _, a, _, _ in rows)} reference notes, {sum(a['npred'] for _, a, _, _ in rows)} output notes; micro F1 loss {100 * tot_loss / den_all:.2f} points; "
                 f"lost bars {lost_bars} of {ref_bars} reference bars.\n")
    lines.append("| category | events | F1 points lost, micro | macro (mean over pieces) | share of loss |")
    lines.append("|---|---|---|---|---|")
    for c in sorted(CATS, key=lambda c: -micro[c]):
        lines.append(f"| {short[c]} | {ev[c]} | {100 * micro[c] / den_all:.2f} | {macro[c] / n:.2f} | {100 * micro[c] / tot_loss:.0f} % |")
    lines.append(f"\nRepeated-note runs (>= 4 equal events on a staff in one bar): {run_ref} reference notes in runs; missed notes (7a+7b) {run_total_missed}, of them {run_missed} "
                 f"({100 * run_missed / max(run_total_missed, 1):.0f} %) inside such runs = {100 * run_missed / den_all:.2f} F1 points.\n")
    lines.append("| piece | F1 audit | reading-only | lost bars | octave | accidental | step | wrong staff | missing event | missing chord member | extra | other | top two |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for p, a, den, lb in rows:
        ls = {c: 100 * a["loss_notes"][c] / den for c in CATS}
        top = sorted(((v, short[c]) for c, v in ls.items()), reverse=True)[:2]
        lines.append(f"| {p}{'*' if a['ignore_staff'] else ''} | {a['f1_audit']:.1f} | {a['f1_reading_only']:.1f} | {ls['1 unaligned bar']:.1f}/{lb} | " + " | ".join(
            f"{ls[c]:.1f}" for c in ("2 octave", "3 accidental", "4 step", "6 staff assignment", "7b whole event missing", "7a chord member missing", "8 extra", "9 other")) +
            " | " + ", ".join(f"{s} {v:.1f}" for v, s in top) + " |")
    return "\n".join(lines)


if __name__ == "__main__":
    for tag in sys.argv[1:]:
        txt = summarize(tag)
        open(f"{E}/brace_models/audit_{tag}.md", "w").write(txt + "\n")
        print(txt)
