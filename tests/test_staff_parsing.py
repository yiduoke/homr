import unittest

from homr.model import MultiStaff, Staff, StaffPoint
from homr.staff_parsing import (
    _assign_parts,
    _clean_up_voice,
    _drop_ossias,
    _drop_variants,
    _is_variant_of,
    _measure_rests_like,
)
from homr.system_repair import (
    _common_layout,
    _ensure_same_number_of_staffs,
    _unify_grand_staffs,
    drop_ossia_staffs,
)
from homr.transformer.vocabulary import EncodedSymbol
from training.transformer.training_vocabulary import read_token_lines


def make_staff(number: float, is_grandstaff: bool = False) -> Staff:
    """A staff 40 high, at 100 * number. Staffs at n and n + 0.5 are close, like a grand staff."""
    y_points = [10 * i + 100 * number for i in range(5)]
    staff = Staff([StaffPoint(0.0, y_points, 0)])
    staff.is_grandstaff = is_grandstaff
    return staff


def make_row(number: float, is_grandstaff: bool = False) -> MultiStaff:
    return MultiStaff([make_staff(number, is_grandstaff)], [])


def wide_staff(
    number: float, is_grandstaff: bool = True, min_x: float = 0.0, max_x: float = 1000.0
) -> Staff:
    """A staff from min_x to max_x at the height of make_staff."""
    y_points = [10 * i + 100 * number for i in range(5)]
    staff = Staff([StaffPoint(min_x, y_points, 0), StaffPoint(max_x, y_points, 0)])
    staff.is_grandstaff = is_grandstaff
    return staff


def wide_row(number: float, min_x: float = 0.0, max_x: float = 1000.0) -> MultiStaff:
    return MultiStaff([wide_staff(number, True, min_x, max_x)], [])


def read_with_bar_lines(xs: list[float] | None) -> list[EncodedSymbol]:
    """A staff read of a note and a bar line at every given x, the last one ends the staff."""
    symbols = []
    for x in xs or []:
        note = EncodedSymbol("note_4")
        note.image_coordinates = (x - 30, 100.0)
        bar_line = EncodedSymbol("barline")
        bar_line.image_coordinates = (x, 100.0)
        symbols.extend([note, bar_line])
    return symbols


def make_grandstaff_row(number: int) -> MultiStaff:
    """A grand staff of the staffs number and number + 1."""
    return MultiStaff([make_staff(number).merge(make_staff(number + 1))], [])


def _layouts(result: list[MultiStaff]) -> list[list[bool]]:
    return [[s.is_grandstaff for s in row.staffs] for row in result]


class TestStaffParsing(unittest.TestCase):
    def test_ensure_same_number_of_staffs_already_uniform(self) -> None:
        staffs = [make_row(i, is_grandstaff=True) for i in range(4)]

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual([[True]] * 4, _layouts(result))

    def test_ensure_same_number_of_staffs_merges_repeating_pattern(self) -> None:
        # A voice and a piano grand staff in every system
        staffs = []
        for i in range(0, 12, 3):
            staffs.append(make_row(i))
            staffs.append(make_row(i + 1, is_grandstaff=True))

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual([[False, True]] * 4, _layouts(result))

    def test_ensure_same_number_of_staffs_merges_repeating_pattern_grand_staff_first(self) -> None:
        # The piano grand staff above the solo staff in every system
        staffs = []
        for i in range(0, 12, 3):
            staffs.append(make_row(i, is_grandstaff=True))
            staffs.append(make_row(i + 1))

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual([[True, False]] * 4, _layouts(result))

    def test_ensure_same_number_of_staffs_absorbs_inconsistently_pre_merged_row(self) -> None:
        # Only the first system was connected by a bar line
        pre_merged = MultiStaff([make_staff(0), make_staff(1, is_grandstaff=True)], [])
        staffs = [pre_merged]
        for i in range(2, 8, 2):
            staffs.append(make_row(i))
            staffs.append(make_row(i + 1, is_grandstaff=True))

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual([[False, True]] * 4, _layouts(result))

    def test_ensure_same_number_of_staffs_keeps_leading_system_with_other_layout(self) -> None:
        staffs = [make_row(0, is_grandstaff=True)]
        staffs += [MultiStaff([make_staff(i), make_staff(i + 1, True)], []) for i in (1, 3, 5)]

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual([[True]] + [[False, True]] * 3, _layouts(result))

    def test_ensure_same_number_of_staffs_drops_single_staff_below_last_system(self) -> None:
        staffs = [make_row(i, is_grandstaff=True) for i in range(4)] + [make_row(4)]

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual([[True]] * 4, _layouts(result))

    def test_ensure_same_number_of_staffs_splits_pairs_on_page_of_single_staffs(self) -> None:
        staffs = [make_row(0), make_row(1), MultiStaff([make_staff(2), make_staff(3)], [])]
        staffs += [make_row(4), MultiStaff([make_staff(5), make_staff(6)], []), make_row(7)]

        result = _ensure_same_number_of_staffs(staffs)

        # Connected pairs on a page of single staffs are most likely false connections
        self.assertEqual([[False]] * 8, _layouts(result))

    def test_ensure_same_number_of_staffs_keeps_certain_systems(self) -> None:
        staffs = [make_row(0), make_row(1), make_row(2)]
        staffs += [MultiStaff([make_staff(3), make_staff(4)], [], certain=True)]
        staffs += [MultiStaff([make_staff(5), make_staff(6)], [], certain=True)]

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual([[False]] * 3 + [[False, False]] * 2, _layouts(result))

    def test_ensure_same_number_of_staffs_keeps_layout_change(self) -> None:
        # A system where the voice pauses, between systems with voice and piano
        staffs = [
            MultiStaff([make_staff(3 * i), make_staff(3 * i + 1, True)], []) for i in range(4)
        ]
        staffs.insert(2, make_row(12, is_grandstaff=True))

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual([[False, True]] * 2 + [[True]] + [[False, True]] * 2, _layouts(result))

    def test_ensure_same_number_of_staffs_merges_neighbors_into_common_layout(self) -> None:
        staffs = [
            MultiStaff([make_staff(3 * i), make_staff(3 * i + 1, True)], []) for i in range(3)
        ]
        staffs += [make_row(9), make_row(10, is_grandstaff=True)]

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual([[False, True]] * 4, _layouts(result))

    def test_ensure_same_number_of_staffs_merges_single_staffs_with_missed_brace(self) -> None:
        staffs = [make_row(i, is_grandstaff=True) for i in (0, 1, 4, 5)]
        staffs[2:2] = [make_row(2), make_row(2.5)]

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual([[True]] * 5, _layouts(result))

    def test_ensure_same_number_of_staffs_keeps_evenly_spaced_single_staffs(self) -> None:
        # Verses for the voice alone after systems of a piano
        staffs = [make_row(i, is_grandstaff=True) for i in range(3)]
        staffs += [make_row(i) for i in range(3, 9)]

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual([[True]] * 3 + [[False]] * 6, _layouts(result))

    def test_ensure_same_number_of_staffs_keeps_single_staffs_above_grand_staffs(self) -> None:
        # A violin part whose last systems add a second voice
        staffs = [make_row(i) for i in range(5)]
        staffs += [make_grandstaff_row(i) for i in (5, 7, 9)]

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual([[False]] * 5 + [[True]] * 3, _layouts(result))

    def test_ensure_same_number_of_staffs_completes_system_with_single_staff(self) -> None:
        # The first grand staff of the second system lost its brace
        system = [make_grandstaff_row(0).staffs[0], make_staff(2), make_staff(3)]
        staffs = [MultiStaff([*system, make_grandstaff_row(4).staffs[0]], [])]
        staffs += [make_row(6)]
        staffs += [MultiStaff([make_staff(7), make_staff(8), make_staff(9)], [])]
        staffs[-1].staffs.append(make_grandstaff_row(10).staffs[0])

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual([[True, False, False, True]] * 2, _layouts(result))

    def test_ensure_same_number_of_staffs_splits_wrongly_connected_systems(self) -> None:
        # A crease connected the staffs of several systems
        connected = [make_staff(i, is_grandstaff=i % 2 == 1) for i in range(7)]
        staffs = [MultiStaff(connected, []), make_row(7, is_grandstaff=True)]

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual([[False, True]] * 4, _layouts(result))

    def test_ensure_same_number_of_staffs_merges_only_staffs_which_overlap(self) -> None:
        staffs = [make_row(i, is_grandstaff=True) for i in range(4)]
        right = Staff([StaffPoint(500.0, [10 * i + 1100.0 for i in range(5)], 0)])
        staffs[2:2] = [make_row(10), MultiStaff([right], [])]

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual([[True]] * 2 + [[False]] * 2 + [[True]] * 2, _layouts(result))

    def test_ensure_same_number_of_staffs_keeps_systems_without_common_layout(self) -> None:
        staffs = [
            MultiStaff([make_staff(0), make_staff(1, is_grandstaff=True)], []),
            MultiStaff([make_staff(2, is_grandstaff=True), make_staff(3)], []),
        ]

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual(staffs, result)

    def test_ensure_same_number_of_staffs_finds_grand_staff_found_as_single_staffs(self) -> None:
        # A grand staff was found as two connected single staffs
        staffs = [make_row(0), make_row(1, is_grandstaff=True), make_row(2)]
        staffs += [MultiStaff([make_staff(3), make_staff(3.5)], [])]
        staffs += [make_row(5), make_row(6, is_grandstaff=True)]

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual([[False, True]] * 3, _layouts(result))

    def test_ensure_same_number_of_staffs_merges_system_with_missed_brace(self) -> None:
        staffs = [make_row(i, is_grandstaff=True) for i in range(4)]
        staffs.append(MultiStaff([make_staff(4), make_staff(5)], []))

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual([[True]] * 5, _layouts(result))

    def test_ensure_same_number_of_staffs_splits_wrongly_found_grand_staff(self) -> None:
        staffs = [MultiStaff([make_staff(2 * i), make_staff(2 * i + 1)], []) for i in range(3)]
        staffs.append(MultiStaff([make_staff(6).merge(make_staff(7))], []))

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual([[False, False]] * 4, _layouts(result))

    def test_common_layout_prefers_mix_of_single_and_grand_staffs(self) -> None:
        grand = [False, True, False, True, False, False, False, True]
        staffs = [make_row(i, is_grandstaff) for i, is_grandstaff in enumerate(grand)]

        self.assertEqual((False, True), _common_layout(staffs))

    def test_ensure_same_number_of_staffs_merges_single_staffs_as_close_as_grand_staffs(
        self,
    ) -> None:
        # Two grand staffs whose braces were missed
        staffs = [make_row(0), make_row(0.5), make_row(2), make_row(2.5)]
        staffs += [make_grandstaff_row(4), make_grandstaff_row(6)]

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual([[True]] * 4, _layouts(result))

    def test_ensure_same_number_of_staffs_joins_voice_and_piano_of_single_system(self) -> None:
        staffs = [make_row(0), make_row(1, is_grandstaff=True)]

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual([[False, True]], _layouts(result))

    def test_ensure_same_number_of_staffs_keeps_two_grand_staffs_per_system(self) -> None:
        # Piano four hands, the last system has one piano only
        staffs = [MultiStaff([make_staff(i, True), make_staff(i + 1, True)], []) for i in (0, 2)]
        staffs.append(make_row(4, is_grandstaff=True))

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual([[True, True]] * 2 + [[True]], _layouts(result))

    def test_ensure_same_number_of_staffs_merges_only_staffs_as_close_as_grand_staffs(
        self,
    ) -> None:
        staffs = [make_grandstaff_row(0), make_grandstaff_row(2)]
        staffs += [make_row(4), make_row(6)]  # Twice the gap of a grand staff
        staffs += [make_grandstaff_row(8), make_grandstaff_row(10)]

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual([[True]] * 2 + [[False]] * 2 + [[True]] * 2, _layouts(result))

    def test_unify_grand_staffs_keeps_page_if_staffs_dont_overlap(self) -> None:
        right = Staff([StaffPoint(500.0, [10 * i + 600.0 for i in range(5)], 0)])
        staffs = [MultiStaff([make_staff(0), make_staff(1, True)], []) for _ in range(2)]
        staffs.append(MultiStaff([make_staff(4), make_staff(5), right], []))

        self.assertEqual(staffs, _unify_grand_staffs(staffs))

    def test_ensure_same_number_of_staffs_keeps_systems_of_several_grand_staffs(self) -> None:
        staffs = [
            MultiStaff([make_staff(0, True), make_staff(1, True)], []),
            MultiStaff([make_staff(i, True) for i in (2, 3, 4)], []),
        ]

        result = _ensure_same_number_of_staffs(staffs)

        self.assertEqual(_layouts(staffs), _layouts(result))

    def test_unify_grand_staffs_keeps_page_without_most_common_layout(self) -> None:
        staffs = [
            MultiStaff([make_staff(0).merge(make_staff(1))], []),
            MultiStaff([make_staff(2), make_staff(3)], []),
        ]
        self.assertEqual(staffs, _unify_grand_staffs(staffs))

    def test_unify_grand_staffs_keeps_page_if_grand_staff_cant_be_split(self) -> None:
        # Detected as grand staff, but without the lines of two staffs
        staffs = [MultiStaff([make_staff(2 * i), make_staff(2 * i + 1)], []) for i in range(3)]
        staffs.append(MultiStaff([make_staff(6, is_grandstaff=True)], []))
        self.assertEqual(staffs, _unify_grand_staffs(staffs))

    def test_assign_parts_with_hidden_voice(self) -> None:
        # Voice and piano, in the second system the voice is hidden
        voice_and_piano = MultiStaff([make_staff(0), make_staff(1, is_grandstaff=True)], [])
        piano = make_row(3, is_grandstaff=True)

        self.assertEqual([(0, 1), (1,)], _assign_parts([voice_and_piano, piano]))

    def test_assign_parts_ambiguous(self) -> None:
        # Two voices, a system with one of them doesn't tell which one
        two_voices = MultiStaff([make_staff(0), make_staff(1)], [])

        self.assertIsNone(_assign_parts([two_voices, make_row(3)]))

    def test_measure_rests_like(self) -> None:
        symbols = [
            EncodedSymbol("clef_G2"),
            EncodedSymbol("note_8", "C4"),
            EncodedSymbol("note_8", "D4"),
            EncodedSymbol("barline"),
            EncodedSymbol("note_4", "E4"),
            EncodedSymbol("repeatEnd"),
        ]

        result = _measure_rests_like(symbols, is_grandstaff=True)

        self.assertEqual(
            ["measureRest", "chord", "measureRest", "barline"]
            + ["measureRest", "chord", "measureRest", "repeatEnd"],
            [s.rhythm for s in result],
        )
        self.assertEqual("lower", result[2].position)

    def test_clean_up_voice_restores_unmarked_triplets(self) -> None:
        # Three eighths in the right hand against each quarter in the left hand
        measure = """note_8 C5 _ _ _ upper&note_4 C3 _ _ _ lower
note_8 D5 _ _ _ upper
note_8 E5 _ _ _ upper
barline . . . . ."""
        header = """clef_G2 _ _ _ _ upper&clef_F4 _ _ _ _ lower
keySignature_0 . . . . .
timeSignature_4/4 . . . . ."""
        symbols = read_token_lines([*header.splitlines(), *measure.splitlines() * 3])

        result = _clean_up_voice(symbols)

        right_hand = [s.rhythm for s in result if s.position == "upper" and "note" in s.rhythm]
        self.assertEqual(["note_12"] * 9, right_hand)


def _sized_staff(number: float, unit: float, is_grandstaff: bool = False) -> Staff:
    y_points = [unit * i + 100 * number for i in range(5)]
    staff = Staff([StaffPoint(0.0, y_points, 0)])
    staff.is_grandstaff = is_grandstaff
    return staff


class TestOssias(unittest.TestCase):
    def test_drops_small_staff_above_a_system(self) -> None:
        # Three systems of a grand staff, the third with an ossia above it (7 instead of 10)
        rows = [MultiStaff([_sized_staff(i, 10, True)], []) for i in range(3)]
        rows[2] = MultiStaff([_sized_staff(1.5, 7), _sized_staff(2, 10, True)], [], certain=True)
        rows += [MultiStaff([_sized_staff(i, 10, True)], []) for i in range(3, 6)]

        result = drop_ossia_staffs(rows)

        self.assertEqual([[True]] * 6, _layouts(result))
        self.assertFalse(result[2].certain)

    def test_drops_small_staff_which_is_a_system_of_its_own(self) -> None:
        rows = [MultiStaff([_sized_staff(i, 10, True)], []) for i in range(4)]
        rows.insert(2, MultiStaff([_sized_staff(1.5, 6)], []))

        result = drop_ossia_staffs(rows)

        self.assertEqual(4, len(result))

    def test_keeps_staffs_of_about_the_same_size(self) -> None:
        rows = [MultiStaff([_sized_staff(i, 10 + i % 2, True)], []) for i in range(5)]

        self.assertEqual(rows, drop_ossia_staffs(rows))

    def test_keeps_small_staffs_if_they_are_not_a_minority(self) -> None:
        rows = [MultiStaff([_sized_staff(i, 6 if i % 2 else 10)], []) for i in range(6)]

        self.assertEqual(rows, drop_ossia_staffs(rows))

    def test_keeps_a_page_of_two_staffs(self) -> None:
        rows = [MultiStaff([_sized_staff(0, 10)], []), MultiStaff([_sized_staff(1, 5)], [])]

        self.assertEqual(rows, drop_ossia_staffs(rows))

    def test_drops_staff_found_in_another_print_size(self) -> None:
        # The short bass ossia of a real scan (Liszt, Réminiscences de Don Juan, IMSLP415304
        # p20) is printed at 78 percent of the normal size: the staff detection found it as a
        # staff of another size, but it isn't below ossia_unit_share
        rows = [MultiStaff([_sized_staff(i, 15.5, True)], []) for i in range(5)]
        ossia = _sized_staff(2.5, 12.1)
        ossia.other_print_size = True
        rows.insert(3, MultiStaff([ossia], []))

        result = drop_ossia_staffs(rows)

        self.assertEqual(5, len(result))
        self.assertNotIn(ossia, [staff for row in result for staff in row.staffs])

    def test_keeps_staff_of_78_percent_size_without_other_print_size(self) -> None:
        rows = [MultiStaff([_sized_staff(i, 15.5, True)], []) for i in range(5)]
        rows.insert(3, MultiStaff([_sized_staff(2.5, 12.1)], []))

        self.assertEqual(rows, drop_ossia_staffs(rows))

    def test_drops_staffs_found_in_another_print_size_over_every_system(self) -> None:
        rows = []
        for i in range(4):
            ossia = _sized_staff(i - 0.4, 10)
            ossia.other_print_size = True
            rows.append(MultiStaff([ossia, _sized_staff(i, 15, True)], []))

        result = drop_ossia_staffs(rows)

        self.assertEqual([[True]] * 4, _layouts(result))

    def test_drops_staff_found_in_another_print_size_on_page_of_one_system(self) -> None:
        ossia = _sized_staff(-0.4, 10)
        ossia.other_print_size = True
        rows = [MultiStaff([ossia, _sized_staff(0, 15, True)], [])]

        self.assertEqual([[True]], _layouts(drop_ossia_staffs(rows)))


class TestVariants(unittest.TestCase):
    def test_variant_has_the_bar_lines_of_its_main_staff(self) -> None:
        # Vallee d'Obermann p. 42, bars 184-185 and their variant: two bars, same bar lines
        main = read_with_bar_lines([672, 1180])
        variant = read_with_bar_lines([665, 1184])

        self.assertTrue(_is_variant_of(main, variant))

    def test_staff_with_other_bar_lines_is_no_variant(self) -> None:
        # A handwritten page where the staff relation model took two systems for one:
        # four bars each, the bar lines are somewhere else
        main = read_with_bar_lines([178, 319, 493, 736, 936])
        other = read_with_bar_lines([278, 508, 710, 971])

        self.assertFalse(_is_variant_of(main, other))

    def test_staff_with_the_same_number_of_bars_elsewhere_is_no_variant(self) -> None:
        main = read_with_bar_lines([300, 600, 900])
        other = read_with_bar_lines([380, 560, 900])

        self.assertFalse(_is_variant_of(main, other))

    def test_one_bar_staffs_are_no_variants(self) -> None:
        # No inner bar line to compare: the staff stays
        self.assertFalse(_is_variant_of(read_with_bar_lines([900]), read_with_bar_lines([900])))

    def test_staff_without_positions_is_no_variant(self) -> None:
        main = read_with_bar_lines([672, 1180])
        for symbol in main:
            symbol.image_coordinates = None

        self.assertFalse(_is_variant_of(main, read_with_bar_lines([665, 1184])))

    def test_drop_variants_keeps_both_of_two_real_systems_grouped_as_one(self) -> None:
        # Polish scores sample 93: five systems of a grand staff, the first two read as one system
        # of two grand staffs. They are different systems and both stay.
        results = {
            (0, 0): read_with_bar_lines([178, 319, 493, 736, 936]),
            (1, 0): read_with_bar_lines([278, 508, 710, 971]),
            (2, 0): read_with_bar_lines([337, 538, 694, 789]),
        }
        before = dict(results)

        _drop_variants(results, [0, 0, 1], [True, True, True])

        self.assertEqual(before, results)

    def test_drop_variants_drops_the_variant_only(self) -> None:
        # Page 42: variants below the first two systems, a system of its own at the end
        results = {
            (0, 0): read_with_bar_lines([672, 1180]),
            (1, 0): read_with_bar_lines([665, 1184]),
            (2, 0): read_with_bar_lines([651, 1183]),
            (3, 0): read_with_bar_lines([639, 1168]),
            (4, 0): read_with_bar_lines([599, 1187]),
        }

        _drop_variants(results, [0, 0, 1, 1, 2], [True] * 5)

        self.assertEqual([(0, 0), (2, 0), (4, 0)], sorted(results))

    def test_drop_variants_keeps_the_voices_of_other_staffs(self) -> None:
        # A voice and a piano staff with the same bars are no variants
        results = {(0, 0): read_with_bar_lines([300, 900]), (1, 0): read_with_bar_lines([300, 900])}

        _drop_variants(results, [0, 0], [False, True])

        self.assertEqual([(0, 0), (1, 0)], sorted(results))


class TestDropOssias(unittest.TestCase):
    def test_drops_ossia_which_starts_far_right(self) -> None:
        rows = [wide_row(0), wide_row(3, min_x=900), wide_row(6), wide_row(9)]

        kept = _drop_ossias(rows)

        self.assertEqual([0, 2, 3], [i for i, _ in kept])

    def test_keeps_a_system_which_ends_early(self) -> None:
        # A short last system starts at the left margin
        rows = [wide_row(0), wide_row(3), wide_row(6), wide_row(9, max_x=900)]

        self.assertEqual([0, 1, 2, 3], [i for i, _ in _drop_ossias(rows)])

    def test_keeps_a_page_with_a_staff_which_is_no_grand_staff(self) -> None:
        rows = [
            MultiStaff([wide_staff(0, is_grandstaff=False)], []),
            wide_row(3, min_x=900),
            wide_row(6),
        ]

        self.assertEqual([0, 1, 2], [i for i, _ in _drop_ossias(rows)])
