import json
import os
import unittest

import cv2
import numpy as np

from homr.bounding_boxes import RotatedBoundingBox
from homr.model import Staff, StaffPoint
from homr.staff_detection import (
    RawStaff,
    StaffAnchor,
    StaffLineSegment,
    connect_staff_lines,
    estimate_unit_size_from_clefs,
    filter_neighbor_page,
    filter_unusual_anchors,
    find_horizontal_lines,
    merge_staffs_in_same_row,
)


def makeBoundingBox(x: float, y: float) -> RotatedBoundingBox:
    w, h = 40.0, 2.0
    angle = 0.0
    return RotatedBoundingBox(((x, y), (w, h), angle), np.array([]))


def make_staff(min_x: float, max_x: float, top: float) -> Staff:
    y = [top + 10 * i for i in range(5)]
    return Staff([StaffPoint(min_x, y, 0), StaffPoint(max_x, y, 0)])


def make_raw_staff(min_x: float, max_x: float, top: float) -> RawStaff:
    """A staff with a unit size of 10 and one fragment per line."""
    lines = []
    for i in range(5):
        box = ((float(min_x + max_x) / 2, top + 10 * i), (float(max_x - min_x), 2.0), 0.0)
        contour = cv2.boxPoints(box).astype(np.int32).reshape(-1, 1, 2)
        lines.append(StaffLineSegment(i, [RotatedBoundingBox(box, contour)]))
    clef = RotatedBoundingBox(((min_x + 10, top + 20), (20, 40), 0), np.array([]))
    return RawStaff(0, lines, [StaffAnchor(lines, clef)])


def make_anchor(x: float, line_ys: list[float]) -> StaffAnchor:
    """An anchor at a bar line at x, with straight staff lines at line_ys."""
    lines = [
        StaffLineSegment(i, [RotatedBoundingBox(((x, y), (200.0, 2.0), 0.0), np.array([]))])
        for i, y in enumerate(line_ys)
    ]
    height = line_ys[-1] - line_ys[0]
    bar_line = RotatedBoundingBox(((x, line_ys[0] + height / 2), (3.0, height), 0.0), np.array([]))
    return StaffAnchor(lines, bar_line)


def make_anchors(top: float, unit_size: float, xs: list[float]) -> list[StaffAnchor]:
    return [make_anchor(x, [top + unit_size * i for i in range(5)]) for x in xs]


# The anchors which enter the spacing filter on page 7 of Liszt's Grosses Konzertsolo
# (IMSLP56095, Schott), a real scan with three ossias in small print above its systems.
# The x of each anchor's symbol and the y of its five lines there, on the 1920 px wide
# detector input. Written by run/round5_prep/ossia_fix/make_fixture.py of the research repo.
konzertsolo_anchors = os.path.join(
    os.path.dirname(__file__), "data", "staff_anchors_konzertsolo_p7.json"
)
# The y ranges of the three ossia staffs on that page
konzertsolo_ossias = [(220, 275), (728, 783), (1217, 1270)]


class TestStaffDetection(unittest.TestCase):
    def test_merge_staffs_in_same_row(self) -> None:
        left = make_raw_staff(100, 500, 100)
        after_clef_change = make_raw_staff(600, 1500, 100)
        next_row = make_raw_staff(100, 500, 300)
        shifted_by_a_line = make_raw_staff(600, 1500, 310)
        neighbor_page = make_raw_staff(1800, 2500, 100)

        # The clef covers the gap of the first row, the second row has an empty gap
        ink = np.zeros((400, 2600), dtype=np.uint8)
        ink[100:141, 490:610] = 1

        result = merge_staffs_in_same_row(
            [left, after_clef_change, next_row, shifted_by_a_line, neighbor_page], ink
        )

        self.assertEqual(4, len(result))
        merged = next(staff for staff in result if staff.min_y < 200 and staff.max_x < 1600)
        self.assertAlmostEqual(100, merged.min_x, delta=2)
        self.assertAlmostEqual(1500, merged.max_x, delta=2)

    def test_merge_staffs_in_same_row_not_across_gutter(self) -> None:
        left_page = make_raw_staff(100, 500, 100)
        right_page = make_raw_staff(600, 1500, 100)
        ink = np.zeros((200, 1600), dtype=np.uint8)
        ink[100:141, 100:501] = 1
        ink[100:141, 600:1501] = 1

        result = merge_staffs_in_same_row([left_page, right_page], ink)

        self.assertEqual(2, len(result))

    def test_filter_neighbor_page(self) -> None:
        page = [make_staff(500, 1500, top) for top in (100, 300, 500)]
        indented = make_staff(700, 1500, 700)
        neighbor_page = make_staff(100, 350, 300)

        result = filter_neighbor_page([*page, indented, neighbor_page])

        self.assertEqual([*page, indented], result)

    def test_filter_neighbor_page_keeps_left_of_two_pages(self) -> None:
        left_page = [make_staff(100, 900, top) for top in (100, 300, 500)]
        right_page = [make_staff(1000, 1800, top) for top in (150, 350, 550)]

        result = filter_neighbor_page(left_page + right_page)

        self.assertEqual(left_page, result)

    def test_connect_staff_lines(self) -> None:
        lines = [makeBoundingBox(100, 100), makeBoundingBox(50, 100), makeBoundingBox(150, 100)]
        result = connect_staff_lines(lines, 5)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].staff_fragments, [lines[1], lines[0], lines[2]])

    def test_find_horizontal_lines_without_lines(self) -> None:
        empty = np.zeros((200, 20), dtype=np.uint8)
        self.assertEqual([], find_horizontal_lines(empty, 10))

    def test_estimate_unit_size_from_clefs(self) -> None:
        lines = [
            RotatedBoundingBox(((300, 100 + 10 * i), (400, 2), 0), np.array([])) for i in range(5)
        ]
        clef = RotatedBoundingBox(((150, 120), (20, 40), 0), np.array([]))

        self.assertAlmostEqual(10, estimate_unit_size_from_clefs(lines, [clef]) or 0, delta=0.5)
        self.assertIsNone(estimate_unit_size_from_clefs(lines, []))

    def test_filter_unusual_anchors_removes_anchors_which_contradict_their_staff(self) -> None:
        xs = [200.0 + 150 * i for i in range(10)]
        page = [a for top in (100, 300, 500, 700) for a in make_anchors(top, 15, xs)]
        # Five lines connected over a ledger line, on the staff at y=300
        wrong = make_anchor(1000, [300, 319, 338, 357, 376])

        result = filter_unusual_anchors([*page, wrong])

        self.assertEqual(page, result)

    def test_filter_unusual_anchors_keeps_staffs_in_small_print(self) -> None:
        xs = [200.0 + 75 * i for i in range(20)]
        page = [a for top in (300, 500, 900, 1100) for a in make_anchors(top, 15, xs)]
        ossia = make_anchors(200, 9, [400, 700, 1000])
        lone_ossia_anchor = make_anchors(800, 9, [1500])
        wrong_on_page_staff = make_anchor(1000, [500, 519, 538, 557, 576])

        result = filter_unusual_anchors([*page, *ossia, *lone_ossia_anchor, wrong_on_page_staff])

        self.assertEqual([*page, *ossia, *lone_ossia_anchor], result)
        self.assertEqual(
            [False] * len(page) + [True] * 4, [anchor.other_print_size for anchor in result]
        )

    def test_filter_unusual_anchors_on_real_scan_with_ossias(self) -> None:
        with open(konzertsolo_anchors) as f:
            anchors = [make_anchor(x, ys) for x, ys in json.load(f)["anchors"]]

        def on_ossia(anchor: StaffAnchor) -> bool:
            center = (anchor.min_y + anchor.max_y) / 2
            return any(top < center < bottom for top, bottom in konzertsolo_ossias)

        result = filter_unusual_anchors(anchors)

        self.assertEqual(350, len(anchors))
        self.assertEqual(30, sum(on_ossia(anchor) for anchor in anchors))
        # The page-wide spacing alone rejects all 30 anchors of the ossias
        self.assertEqual(30, sum(on_ossia(anchor) for anchor in result))
        self.assertEqual(anchors, result)
