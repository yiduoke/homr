#!/usr/bin/env python3
"""
Read-only. For every source score of a training list (token paths), find its MusicXML and count
the rest forms the converter reads differently (regex scan, no XML parse):
  typeless   a <rest/> (no measure attribute) in a <note> without <type>  -> rest_8 by the converter
  measure    <rest measure="yes"/>                                        -> rest_1 .. rest_8 by duration
  typed      <rest/> in a <note> with <type>
Output TSV: source, id, xml, software, typeless, measure_yes, typed, first typeless snippet.

usage: xml_scan.py LIST [LIST ...] --out out.tsv     (lines `image,tokens` or `tokens`)
"""
import argparse
import glob
import os
import re
import sys

LIED = "/workspace/homr566/datasets/Lieder-main/rendered_scores"
PDMX = "/workspace/homr566/datasets/pdmx/rendered_scores"
PDMXH = "/workspace/homr566/datasets/pdmx/hard/rendered_scores"
ROOTS = {
    "pdmx": [PDMX], "pdmx_hard": [PDMXH],
    "lieder": [LIED],
    "lilypond": ["/workspace/aug_xml", "/workspace/aug_xml4", "/workspace/aug_xml5", LIED, PDMX, PDMXH, "/workspace/sq_xml"],
    "musescore_octave": [LIED, "/workspace/sq_xml", PDMX, PDMXH, "/workspace/aug_xml", "/workspace/aug_xml4", "/workspace/aug_xml5"],
    "asap": ["/workspace/run3/ms_export/asap"],
    "scriabin": ["/workspace/run3/ms_export/kern_scriabin"],
    "meter_arm": [f"/workspace/run4/meters/xml/{c}" for c in "abcdefgvwx"],
}


def source_id(tok):
    base = os.path.basename(tok)[: -len(".tokens")]
    ident = re.sub(r"(-vrv)?-\d+-\d+$", "", base)
    for key, name in (("pdmx/hard/", "pdmx_hard"), ("/pdmx/", "pdmx"), ("lilypond", "lilypond"),
                      ("musescore_octave", "musescore_octave"), ("/asap/", "asap"),
                      ("kern_scriabin", "scriabin"), ("meters/", "meter_arm"), ("Lieder", "lieder")):
        if key in tok:
            return name, ident
    return "other", ident


def find_xml(src, ident):
    cands = [ident]
    for suf in ("oct4", "oct5", "oct", "v2"):
        if ident.endswith(suf):
            cands.append(ident[: -len(suf)])
    if src == "meter_arm" and ident.endswith("x"):
        cands.append(ident[:-1])
    for c in cands:
        for root in ROOTS.get(src, []):
            for ext in (".musicxml", ".xml"):
                p = os.path.join(root, c + ext)
                if os.path.exists(p):
                    return p
    for c in cands:
        for root in ROOTS.get(src, []):
            hits = glob.glob(os.path.join(root, c + "*.musicxml"))
            if hits:
                return hits[0]
    return None


REST = re.compile(r"<rest\s*/>|<rest>|<rest\s+measure=\"yes\"\s*/>|<rest\s+measure=\"yes\"\s*>")


def scan(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    out = {"typeless": 0, "measure": 0, "typed": 0, "snippet": "", "software": ""}
    m = re.search(r"<software>([^<]*)</software>", text)
    if m:
        out["software"] = m.group(1)[:30]
    for r in REST.finditer(text):
        end = text.find("</note>", r.end())
        body = text[r.end(): end if end >= 0 else r.end() + 400]
        if "measure" in r.group(0):
            out["measure"] += 1
        elif "<type" in body:
            out["typed"] += 1
        else:
            out["typeless"] += 1
            if not out["snippet"]:
                start = text.rfind("<note", 0, r.start())
                meas = text.rfind("<measure ", 0, r.start())
                mm = re.match(r'<measure[^>]*number="([^"]*)"', text[meas: meas + 120]) if meas >= 0 else None
                snip = re.sub(r"\s+", " ", text[start: end + 7])[:160]
                out["snippet"] = f"measure {mm.group(1) if mm else '?'}: {snip}"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lists", nargs="+")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    seen = set()
    with open(args.out, "w") as out:
        out.write("source\tid\txml\tsoftware\ttypeless\tmeasure_yes\ttyped\tsnippet\n")
        for lst in args.lists:
            for line in open(lst):
                line = line.strip()
                if not line:
                    continue
                img, _, tok = line.partition(",")
                tok = tok or img
                src, ident = source_id(img + " " + tok)
                if (src, ident) in seen or src in ("other", "grandstaff"):
                    continue
                seen.add((src, ident))
                xml = find_xml(src, ident)
                if xml is None:
                    out.write(f"{src}\t{ident}\tNOT_FOUND\t\t\t\t\t\n")
                    continue
                r = scan(xml)
                out.write(f"{src}\t{ident}\t{xml}\t{r['software']}\t{r['typeless']}\t{r['measure']}\t{r['typed']}\t{r['snippet']}\n")


if __name__ == "__main__":
    main()
