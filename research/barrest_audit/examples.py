#!/usr/bin/env python3
"""
Excerpts for the report: for the sampled flagged staves (xml_find_out.txt lines: source, token file, ...)
print the flagged bar of the staff (detail TSV row) as token lines, with the XML finding next to it.
usage: examples.py det_train.tsv xml_find_out.txt
"""
import sys
sys.path.insert(0, "/workspace/audit_barrest")
import detect_barrest as D

det = {}
for l in open(sys.argv[1]):
    f = l.rstrip("\n").split("\t")
    if f[0] == "source" or f[4] != "bug_rest8":
        continue
    det.setdefault(f[1].split("/")[-1], f)
for l in open(sys.argv[2]):
    f = l.rstrip("\n").split(" ", 2)
    src, base, rest = f[0], f[1], f[2] if len(f) > 2 else ""
    d = det.get(base)
    if d is None:
        continue
    ms = D.parse_staff(open(d[1]).read())
    bar = int(d[2])
    lines = ms[bar]["text"][:6]
    print(f"### {src} | {base} | bar {bar} of {d[3]} | kind {d[4]} | bar length {d[6]} ({d[7]}) | tracks {d[5][:80]}")
    for t in lines:
        print("    " + t[:150])
    print("    XML: " + rest[:300])
