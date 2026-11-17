import json, sys
r = json.load(open(sys.argv[1]))
src = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else {}
out = []
out.append("# Meter mining of the run-3 training lists (128,439 unique staffs)\n")
out.append(f"Staffs with any printed time signature: {r['with_any']} ({100*r['with_any']/r['n_staffs']:.1f}%); at the start: {r['with_start']}; "
           f"with a mid-staff change: {r['with_mid']}. Staff space (px, 1400 px pages): median {r['ss_all']['median']}, 5-95% {r['ss_all']['p5']}-{r['ss_all']['p95']} "
           "(GrandStaff images have no crop file).\n")
out.append("## By set\n\n| set | staffs | scores | with signature | mid-staff change | system start after change* | median staff space |\n|---|---|---|---|---|---|---|")
for k, v in r["by_set"].items():
    note = "n/a" if k in ("grandstaff", "lilypond") else v["after_change"]
    out.append(f"| {k} | {v['staffs']} | {v['scores']} | {v['with_any']} | {v['with_mid']} | {note} | {v['staff_space_median']:.1f} |")
out.append("\n*start signature different from the last meter seen earlier in the same score; GrandStaff/LilyPond excerpts restate the meter in every staff, so the number is not meaningful there.\n")
out.append("## By meter (staffs that print the meter at the start or after a change)\n\n| meter | staffs | at start | after change | scores | composers | staff space med (min-max) |" + (" real scores with >=2 clean bars* |" if src else "") + "\n|---|---|---|---|---|---|---|" + ("---|" if src else ""))
for k, v in sorted(r["meters"].items(), key=lambda kv: -kv[1]["staffs"]):
    row = f"| {k} | {v['staffs']} | {v['start']} | {v['mid_to']} | {v['scores']} | {v['composers']} | {v['ss_median']} ({v['ss_min']}-{v['ss_max']}) |"
    if src:
        row += f" {src.get(k, 0)} |"
    out.append(row)
if src:
    out.append("\n*train-pool scores that have at least two consecutive bars in this meter in which every bar adds up to the meter (source MusicXML check); the difference to the 'scores' column are scores whose printed meter does not fit their bars (irregular bars, cadenzas, encoding artefacts).\n")
out.append("\n## Meter changes inside a staff, before -> after (top 40 of %d pairs; '?' = the meter before is not on this staff)\n\n| pair | staffs | scores | composers |\n|---|---|---|---|" % len(r["pairs"]))
for i, (k, v) in enumerate(r["pairs"].items()):
    if i >= 40:
        break
    out.append(f"| {k} | {v['staffs']} | {v['scores']} | {v['composers']} |")
open(sys.argv[3] if len(sys.argv) > 3 else "mining_table.md", "w").write("\n".join(out) + "\n")
