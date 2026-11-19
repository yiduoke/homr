"""Printed accidentals and the sounding alteration they stand for.

The lift of a note token is the accidental sign printed immediately before the note: "#", "b",
"N" (natural), "##", "bb", or "_" if no sign is printed (see Vocabulary.md). The sounding
alteration of a note follows from the printed sign, the key signature and the signs printed
earlier in the bar. Both directions live here so that the training labels and the decoding of
the model output apply the same rule:

- AccidentalState.printed_sign: sounding alteration -> printed sign (labels from sources
  which only know what sounds, e.g. kern).
- AccidentalState.sounding_alter: printed sign -> sounding alteration (the model output).

The rule: a printed sign sets the alteration of its step and octave on its staff until the
barline. A note without sign has the carried alteration of its step and octave on its staff,
else the one of the key signature. All voices of a staff share the carried signs. A note which
continues a tie from the previous bar has the alteration of the tied note and needs no sign;
the alteration of the tied note isn't carried further.
"""

from dataclasses import dataclass
from typing import Hashable

from homr.transformer.vocabulary import (
    EncodedSymbol,
    empty,
    nonote,
    split_slur_and_beam,
)

NO_SIGN = empty
NATURAL = "N"

SIGN_TO_ALTER = {"N": 0, "#": 1, "##": 2, "b": -1, "bb": -2}
ALTER_TO_SIGN = {alter: sign for sign, alter in SIGN_TO_ALTER.items()}

# The order in which sharps are added to a key signature, flats come in the reverse order
_SHARP_ORDER = "FCGDAEB"

# MusicXML <accidental> values, written and read
SIGN_TO_MUSIC_XML = {
    "N": "natural",
    "#": "sharp",
    "##": "double-sharp",
    "b": "flat",
    "bb": "flat-flat",
}
MUSIC_XML_TO_SIGN = {
    "natural": "N",
    "sharp": "#",
    "double-sharp": "##",
    "sharp-sharp": "##",
    "flat": "b",
    "flat-flat": "bb",
    "double-flat": "bb",
    # Closest sign without the cancelling natural
    "natural-sharp": "#",
    "natural-flat": "b",
}

# MEI @accid values (written accidental), the sign Verovio draws
MEI_TO_SIGN = {
    "s": "#",
    "ss": "##",
    "x": "##",
    "f": "b",
    "ff": "bb",
    "n": "N",
    "nf": "b",
    "ns": "#",
}


class UnsupportedAccidentalError(ValueError):
    """A printed sign the vocabulary has no class for, e.g. a quarter tone."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Unsupported accidental {name}")
        self.name = name


def sign_from_music_xml(name: str, strict: bool) -> str:
    """
    The lift class of a MusicXML <accidental> value. Other values, e.g. quarter tones, raise
    UnsupportedAccidentalError if strict (training skips these samples), else the sign
    closest to them is used.
    """
    if name in MUSIC_XML_TO_SIGN:
        return MUSIC_XML_TO_SIGN[name]
    if strict:
        raise UnsupportedAccidentalError(name)
    if "sharp" in name:
        return "#"
    if "flat" in name:
        return "b"
    return NO_SIGN


def sign_from_mei(accid: str | None) -> str | None:
    """The sign of a MEI @accid value, None for no sign. Raises for unknown values."""
    if accid is None or accid in ("", "_", nonote):
        return None
    if accid not in MEI_TO_SIGN:
        raise UnsupportedAccidentalError(accid)
    return MEI_TO_SIGN[accid]


def key_alteration(fifths: int, step: str) -> int:
    """The alteration the key signature with this many sharps (flats if negative) gives a step."""
    if fifths > 0 and step in _SHARP_ORDER[:fifths]:
        return 1
    if fifths < 0 and step in _SHARP_ORDER[::-1][:-fifths]:
        return -1
    return 0


class AccidentalState:
    """
    Key signature and accidentals carried in the bar. A staff can be anything hashable, the
    carried signs are kept per staff, step and octave.
    """

    def __init__(self, fifths: int = 0) -> None:
        self.fifths = fifths
        self._carried: dict[tuple[Hashable, str, int], int] = {}

    def set_key(self, fifths: int) -> None:
        self.fifths = fifths

    def new_bar(self) -> None:
        self._carried.clear()

    def implied(self, staff: Hashable, step: str, octave: int) -> int:
        """The alteration of a note without printed sign."""
        carried = self._carried.get((staff, step, octave))
        if carried is not None:
            return carried
        return key_alteration(self.fifths, step)

    def printed_sign(  # noqa: PLR0913
        self,
        staff: Hashable,
        step: str,
        octave: int,
        alter: int,
        natural: bool = False,
        force: bool = False,
        hide: bool = False,
        tie_alter: int | None = None,
    ) -> str:
        """
        The sign printed before a note which sounds altered by `alter`.

        natural: the source marks an explicit natural (kern n), printed even if not needed.
        force: the sign is printed even if not needed (kern X).
        hide: no sign is printed (kern y), and it isn't carried.
        tie_alter: the alteration of the note this one continues over a barline, if any.
        """
        if hide:
            return NO_SIGN
        if tie_alter == alter and not natural and not force:
            return NO_SIGN
        is_natural_mark = natural and alter == 0
        if not (is_natural_mark or force or alter != self.implied(staff, step, octave)):
            return NO_SIGN
        self._carried[(staff, step, octave)] = alter
        return ALTER_TO_SIGN[alter]

    def sounding_alter(
        self,
        staff: Hashable,
        step: str,
        octave: int,
        sign: str,
        tie_alter: int | None = None,
    ) -> int:
        """The sounding alteration of a note with the printed sign (NO_SIGN for none)."""
        if sign in SIGN_TO_ALTER:
            alter = SIGN_TO_ALTER[sign]
            self._carried[(staff, step, octave)] = alter
            return alter
        if tie_alter is not None:
            return tie_alter
        return self.implied(staff, step, octave)


def split_pitch(pitch: str) -> tuple[str, int]:
    """C#4 isn't a pitch of the vocabulary, the pitch is step and octave only: F4 -> (F, 4)."""
    return pitch[0], int(pitch[1:])


# Lifts of symbols which come from a source with sounding alterations (kern). The sounding
# alteration comes first, then the markers of the source, e.g. "1:" a sharp, "0:n" a
# natural marked with n, "-1:X" a flat marked with X, "0:y" a natural hidden by y. They are
# replaced by printed signs in printed_lifts_from_sounding.


def sounding_lift(
    alter: int, natural: bool = False, force: bool = False, hide: bool = False
) -> str:
    markers = ("n" if natural else "") + ("X" if force else "") + ("y" if hide else "")
    return f"{alter}:{markers}"


def _parse_sounding_lift(lift: str) -> tuple[int, str]:
    alter, _, markers = lift.partition(":")
    return int(alter), markers


@dataclass
class _Voice:
    slot: int = -1
    previous: dict[tuple[str, int], int] | None = None
    current: dict[tuple[str, int], int] | None = None


def _is_note(symbol: EncodedSymbol) -> bool:
    return symbol.rhythm.startswith("note_") and symbol.pitch not in (empty, nonote)


def _is_barline(symbol: EncodedSymbol) -> bool:
    return "barline" in symbol.rhythm or symbol.rhythm.startswith("repeat")


def count_notes(symbols: list[EncodedSymbol]) -> int:
    return sum(1 for symbol in symbols if _is_note(symbol))


def printed_lifts_from_sounding(
    symbols: list[EncodedSymbol],
    printed_signs: list[str | None] | None = None,
) -> list[EncodedSymbol]:
    """
    Replaces the sounding lifts of notes (see sounding_lift) by the printed sign.

    printed_signs: The sign drawn for each note, in the order of the notes in symbols, None or
    "_" for none, e.g. the written @accid of the MEI which Verovio renders for the kern (see
    sign_from_mei). If given, the sign isn't derived. Only a kern n (explicit natural) adds
    a sign which isn't in the list, and X (forced) adds the sounding one, because these are
    drawn even where Verovio leaves them out. Otherwise the signs follow from the rule above.

    Within a staff (the position without the voice) a tie is recognised as a slur stop on the
    same pitch right after a slur start, e.g. a tie across a barline needs no sign.
    """
    notes = count_notes(symbols)
    if printed_signs is not None and len(printed_signs) != notes:
        raise ValueError(f"{len(printed_signs)} printed signs for {notes} notes")
    state = AccidentalState()
    voices: dict[str, _Voice] = {}
    result: list[EncodedSymbol] = []
    slot = 0
    previous_is_chord = False
    note_index = 0
    for symbol in symbols:
        previous_was_chord = previous_is_chord
        previous_is_chord = symbol.rhythm == "chord"
        if symbol.rhythm.startswith("keySignature_"):
            state.set_key(int(symbol.rhythm.split("_")[1]))
        elif _is_barline(symbol):
            state.new_bar()
        if not _is_note(symbol):
            result.append(symbol)
            continue
        if not previous_was_chord:
            slot += 1
        alter, markers = _parse_sounding_lift(symbol.lift)
        step, octave = split_pitch(symbol.pitch)
        staff = symbol.position.rstrip("2")
        voice = voices.setdefault(symbol.position, _Voice())
        if voice.slot != slot:
            voice.slot = slot
            voice.previous, voice.current = voice.current, {}
        slur_start = "slurStart" in split_slur_and_beam(symbol.slur)[0]
        slur_stop = "slurStop" in split_slur_and_beam(symbol.slur)[0]
        tie_alter = (voice.previous or {}).get((step, octave)) if slur_stop else None
        if slur_start and voice.current is not None:
            voice.current[(step, octave)] = alter
        if printed_signs is not None:
            sign = _given_sign(printed_signs[note_index], alter, markers)
        else:
            sign = state.printed_sign(
                staff,
                step,
                octave,
                alter,
                natural="n" in markers,
                force="X" in markers,
                hide="y" in markers,
                tie_alter=tie_alter,
            )
        note_index += 1
        result.append(symbol.change_lift(sign))
    return result


def _given_sign(given: str | None, alter: int, markers: str) -> str:
    if given not in (None, NO_SIGN):
        return given  # type: ignore[return-value]
    if "n" in markers:
        return NATURAL
    if "X" in markers:
        return ALTER_TO_SIGN[alter]
    return NO_SIGN
