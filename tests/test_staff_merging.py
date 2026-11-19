import unittest

from homr.transformer.vocabulary import EncodedSymbol, empty
from training.omr_datasets.staff_merging import (
    EncodedSymbolWithPos,
    create_chord_over_two_staffs,
    merge_upper_and_lower_staff,
)


class TestStaffMerging(unittest.TestCase):
    def test_chord_merging(self) -> None:

        result = create_chord_over_two_staffs(
            [
                EncodedSymbol("keySignature_0", empty, empty, empty, "upper"),
                EncodedSymbol("timeSignature_4/4"),
                EncodedSymbol("clef_G2", empty, empty, empty, "upper"),
                EncodedSymbol("note_16", "F4", empty, empty, "upper"),
                EncodedSymbol("clef_F4", empty, empty, empty, "lower"),
                EncodedSymbol("rest_4", empty, empty, empty, "upper"),
                EncodedSymbol("repeatStart"),
            ]
        )

        self.assertEqual(
            [r.rhythm for r in result],
            [
                "repeatStart",
                "clef_G2",
                "chord",
                "clef_F4",
                "keySignature_0",
                "timeSignature_4/4",
                "note_16",
                "chord",
                "rest_4",
            ],
        )


    def _merge(self, rhythms: list[str]) -> list[str]:
        symbols = [EncodedSymbolWithPos(i, EncodedSymbol(r)) for i, r in enumerate(rhythms)]
        return [s.rhythm for s in merge_upper_and_lower_staff([symbols])]

    def test_volta_mark_does_not_hide_the_repeat_end(self) -> None:
        # The bar already ends with the repeat; no second barline (an empty measure) may follow.
        self.assertEqual(
            self._merge(["note_4", "repeatEnd", "voltaStop"]),
            ["note_4", "repeatEnd", "voltaStop"],
        )

    def test_volta_mark_does_not_hide_a_double_bar(self) -> None:
        self.assertEqual(
            self._merge(["note_4", "bolddoublebarline", "voltaDiscontinue"]),
            ["note_4", "bolddoublebarline", "voltaDiscontinue"],
        )

    def test_volta_mark_after_notes_still_gets_its_barline(self) -> None:
        self.assertEqual(
            self._merge(["voltaStart", "note_4", "voltaStop"]),
            ["voltaStart", "note_4", "voltaStop", "barline"],
        )
