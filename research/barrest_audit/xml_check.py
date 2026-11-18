#!/usr/bin/env python3
"""
Read-only: for token files, find the MusicXML of the source score and count the rest forms the
converter reads differently:
  typeless   <rest/> (no measure attribute) in a <note> without <type>  -> rest_8 by the converter
  measure    <rest measure="yes"/>                                      -> rest_1 .. rest_8 by duration
  typed      <rest/> in a <note> with <type>                            -> typed token
Prints one line per token file and, for the first typeless rest, a snippet with its measure.

usage: xml_check.py FILE_WITH_TOKEN_PATHS   (one path per line)
"""
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOTS = {
    "pdmx": ["/workspace/homr566/datasets/pdmx/rendered_scores"],
    "pdmx_hard": ["/workspace/homr566/datasets/pdmx/hard/rendered_scores"],
    "lilypond": ["/workspace/aug_xml", "/workspace/aug_xml4", "/workspace/aug_xml5", "/workspace/homr/datasets/lilypond_round2"],
    "musescore_octave": ["/workspace/aug_xml", "/workspace/aug_xml4", "/workspace/aug_xml5"],
    "asap": ["/workspace/run3/ms_export/asap"],
    "scriabin": ["/workspace/run3/ms_export/kern_scriabin"],
    "meter_arm": ["/workspace/run4/meters/xml/a", "/workspace/run4/meters/xml/b", "/workspace/run4/meters/xml/c",
                  "/workspace/run4/meters/xml/d", "/workspace/run4/meters/xml/e", "/workspace/run4/meters/xml/f",
                  "/workspace/run4/meters/xml/g"],
}


def source_id(tok: str) -> tuple[str, str]:
    base = os.path.basename(tok)[: -len(".tokens")]
    ident = re.sub(r"(-vrv)?-\d+-\d+$", "", base)
    for key, name in (("pdmx/hard/", "pdmx_hard"), ("/pdmx/", "pdmx"), ("lilypond", "lilypond"),
                      ("musescore_octave", "musescore_octave"), ("/asap/", "asap"),
                      ("kern_scriabin", "scriabin"), ("meters/", "meter_arm"), ("Lieder", "lieder")):
        if key in tok:
            return name, ident
    return "other", ident


def find_xml(src: str, ident: str) -> str | None:
    for root in ROOTS.get(src, []):
        for ext in (".musicxml", ".xml"):
            p = os.path.join(root, ident + ext)
            if os.path.exists(p):
                return p
    if src == "meter_arm":
        return None
    for root in ROOTS.get(src, []):
        hits = glob.glob(os.path.join(root, ident + "*.musicxml"))
        if hits:
            return hits[0]
    if src == "lieder":
        for root in ("/workspace/aug_xml4", "/workspace/aug_xml", "/workspace/aug_xml5"):
            hits = glob.glob(os.path.join(root, ident + "*.musicxml"))
            if hits:
                return hits[0]
    return None


def check(path: str) -> dict:
    tree = ET.parse(path)
    root = tree.getroot()
    sw = [e.text for e in root.iter("software")]
    out = {"software": ";".join(s for s in sw if s)[:40], "typeless": 0, "measure": 0, "typed": 0, "snippet": ""}
    for part in root.iter("part"):
        for meas in part.iter("measure"):
            for note in meas.findall("note"):
                rest = note.find("rest")
                if rest is None:
                    continue
                if rest.get("measure") == "yes":
                    out["measure"] += 1
                elif note.find("type") is None:
                    out["typeless"] += 1
                    if not out["snippet"]:
                        dur = note.findtext("duration", "")
                        out["snippet"] = (
                            f'part {part.get("id")} measure {meas.get("number")}: '
                            f"<note><rest/><duration>{dur}</duration><voice>{note.findtext('voice', '')}</voice></note>"
                            " (no <type>, no measure attribute)"
                        )
                else:
                    out["typed"] += 1
    return out


def main() -> None:
    for line in open(sys.argv[1]):
        tok = line.strip()
        if not tok:
            continue
        src, ident = source_id(tok)
        xml = find_xml(src, ident)
        if xml is None:
            print(f"{tok}\t{src}\tXML_NOT_FOUND\t{ident}")
            continue
        try:
            r = check(xml)
        except Exception as e:  # noqa: BLE001
            print(f"{tok}\t{src}\tERROR {e}\t{xml}")
            continue
        print(f"{tok}\t{src}\t{xml}\t{r['software']}\ttypeless={r['typeless']}\tmeasure_yes={r['measure']}\ttyped={r['typed']}\t{r['snippet']}")


if __name__ == "__main__":
    main()
