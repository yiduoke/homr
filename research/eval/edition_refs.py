"""The ONE list of test-set pieces that are scored against an edition-specific reference (D33, 2026-11-17, laptop).

An edition-specific reference is `out/testset/<piece>/<piece>-reference-edition.musicxml`, a copy of the original `-reference.musicxml` (never modified) with the printed
octave brackets added and the notes under them raised/lowered to match the print (method: octave_checks/make_schubert_edition.py, procedure octave_checks/REPORT.md and REFS_REPORT.md).
Every table/eval script imports EDITION from here instead of keeping its own copy; to add a piece, write its -reference-edition.musicxml and add one line below.
Scored files of such a piece carry the suffix `-edition` (note-scores-<tag>-edition.json, out/pooled/<piece>/<tag>-edition.json, res-dense-<tag>-edition.json);
`octave_checks/rescore_edition.py` writes them for every saved tag.
"""
import os

R = "/Users/yiduoke/Documents/homr/run"
OUT = f"{R}/out/testset"

# piece -> why (print has an 8va the ASAP reference lacks, and the reference holds written pitch under it)
EDITION_WHY = {
    "schubert-impromptu-d899-4": "one 8va over the RH of printed bars 57-64 and 231-236 (Breitkopf FB 4228); ASAP has written pitch and no octave-shift there (D32, octave_checks/REPORT.md)",
}
# D33 checked Hammerklavier, Wanderer, Liszt HR 6, Debussy Pour le piano, Kreisleriana, Scriabin Sonata 5 (and looked at Petrushka): their references hold the SOUNDING pitch under the
# printed brackets (the bracket directions are missing or orphaned), so no pitch edition copy is needed; see octave_checks/REFS_REPORT.md.
EDITION = frozenset(EDITION_WHY)


def suffix(piece: str) -> str:
    return "-edition" if piece in EDITION else ""


def reference_path(piece: str) -> str:
    return f"{OUT}/{piece}/{piece}-reference{suffix(piece)}.musicxml"


def tags_with_outputs(piece: str) -> list[str]:
    """Every tag that has a saved prediction `<piece>-<tag>.musicxml` (reference files excluded)."""
    pre = f"{piece}-"
    d = f"{OUT}/{piece}"
    tags = []
    for f in sorted(os.listdir(d)):
        if f.startswith(pre) and f.endswith(".musicxml") and "-reference" not in f:
            tags.append(f[len(pre):-len(".musicxml")])
    return tags
