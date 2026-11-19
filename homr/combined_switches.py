"""Switches of the opt-in "combined" pipeline variant. All are off by default.

A  strict bracket-aware staff crop v2    HOMR_STRICT_BRACKET_CUT=2 (1 is the first version)
B  cross-staff beam export               HOMR_BEAM_EXPORT=1 (page writer here; the stitching after
                                         the merge is run/combined_post.py, HOMR_BEAM_STITCH=chains)
C  page-level tuplet continuation pass   HOMR_TUPLET_PASS=1 (research_scripts/tuplet_pass.py)

HOMR_COMBINED=1 switches A, B and C on together. HOMR_COMBINED_OFF=A,B,C (comma separated
letters) leaves single ones off for an ablation. An individual variable which is set always
wins over HOMR_COMBINED.
"""

import os


def _combined_on(letter: str) -> bool:
    if os.environ.get("HOMR_COMBINED") != "1":
        return False
    off = {x.strip().upper() for x in os.environ.get("HOMR_COMBINED_OFF", "").split(",")}
    return letter not in off


def strict_cut_level() -> str:
    """Return "" (off), "1" or "2"."""
    explicit = os.environ.get("HOMR_STRICT_BRACKET_CUT", "")
    if explicit:
        return explicit
    return "2" if _combined_on("A") else ""


def beam_export() -> bool:
    explicit = os.environ.get("HOMR_BEAM_EXPORT", "")
    if explicit:
        return explicit == "1"
    return _combined_on("B")


def tuplet_pass() -> bool:
    explicit = os.environ.get("HOMR_TUPLET_PASS", "")
    if explicit:
        return explicit == "1"
    return _combined_on("C")
