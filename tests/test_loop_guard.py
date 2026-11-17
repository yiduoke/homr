import unittest

from homr.transformer.decoder_inference import (
    LOOP_KEEP,
    LOOP_MAX_PERIOD,
    LOOP_RUN,
    _loop_cut,
)
from homr.transformer.vocabulary import EncodedSymbol


def _symbol(pitch: str, rhythm: str = "note_16") -> EncodedSymbol:
    return EncodedSymbol(rhythm, pitch, "_", "_", "_", "upper")


def _feed(symbols: list[EncodedSymbol]) -> int | None:
    """Add the symbols one by one like the decoder and return the cut, if any."""
    seen: list[EncodedSymbol] = []
    runs = [0] * (LOOP_MAX_PERIOD + 1)
    for symbol in symbols:
        seen.append(symbol)
        cut = _loop_cut(seen, runs)
        if cut is not None:
            return cut
    return None


class LoopGuardTest(unittest.TestCase):
    def test_a_long_alternation_is_cut_back_to_its_start(self) -> None:
        start = [_symbol("C4"), _symbol("D4"), _symbol("E4")]
        loop = [_symbol("B5"), _symbol("C6")] * 200
        cut = _feed(start + loop)
        self.assertIsNotNone(cut)
        self.assertEqual(cut, len(start) + LOOP_KEEP)

    def test_a_long_repeat_of_one_note_is_cut(self) -> None:
        self.assertIsNotNone(_feed([_symbol("C6")] * (LOOP_RUN + 5)))

    def test_real_tremolos_and_repeated_notes_are_not_cut(self) -> None:
        # The longest repeat in the test references is 24 notes
        self.assertIsNone(_feed([_symbol("B5"), _symbol("C6")] * 12))
        self.assertIsNone(_feed([_symbol("C6")] * 24))

    def test_a_cycle_longer_than_the_period_limit_is_not_cut(self) -> None:
        cycle = [_symbol(p) for p in ("C4", "D4", "E4", "F4", "G4")]
        self.assertIsNone(_feed(cycle * 100))


if __name__ == "__main__":
    unittest.main()
