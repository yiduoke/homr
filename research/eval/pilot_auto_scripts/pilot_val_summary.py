"""One line per held-out list of a model: python pilot_val_summary.py eval_run1/pilot_val/<NAME>"""
import json, os, sys
d = sys.argv[1]
out = []
for k in ("val_scan_v2", "val_twin_v2", "b2_scan", "b2_scan_matched", "b2_twin"):
    f = f"{d}/{k}.json"
    if os.path.exists(f):
        s = json.load(open(f))["summary"]
        out.append(f"{k} n={s['n']} pitch {s['pitch_f1']:.4f} pitch+rhythm {s['pitch_rhythm_f1']:.4f} bars {s['bars_ok']:.3f}")
print("; ".join(out))
