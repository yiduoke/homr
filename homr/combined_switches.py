"""Switches of the "combined" pipeline variant. B and C are on by default, A is opt-in.

A  strict bracket-aware staff crop v2    HOMR_STRICT_BRACKET_CUT=2 (1 is the first version)
B  cross-staff beam export               HOMR_BEAM_EXPORT=1 (page writer here; the stitching after
                                         the merge is run/combined_post.py, HOMR_BEAM_STITCH=chains)
C  page-level tuplet continuation pass   HOMR_TUPLET_PASS=1 (research_scripts/tuplet_pass.py)

B and C are on without any environment variable (the Polish scores benchmark showed no change
of any page, see the commit message). HOMR_BEAM_EXPORT=0 / HOMR_TUPLET_PASS=0 or the letter in
HOMR_COMBINED_OFF=B,C (comma separated) turn them off. A stays off unless HOMR_COMBINED=1 or
HOMR_STRICT_BRACKET_CUT is set; HOMR_COMBINED=1 switches A on as well. An individual variable
which is set always wins.
"""

import os


def _left_off(letter: str) -> bool:
    off = {x.strip().upper() for x in os.environ.get("HOMR_COMBINED_OFF", "").split(",")}
    return letter in off


def _combined_on(letter: str) -> bool:
    """Opt-in switch (A): needs HOMR_COMBINED=1."""
    return os.environ.get("HOMR_COMBINED") == "1" and not _left_off(letter)


def _default_on(letter: str) -> bool:
    """Switches B and C: on unless left off."""
    return not _left_off(letter)


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
    return _default_on("B")


def tuplet_pass() -> bool:
    explicit = os.environ.get("HOMR_TUPLET_PASS", "")
    if explicit:
        return explicit == "1"
    return _default_on("C")
