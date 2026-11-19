# ruff: noqa: E501, UP031
"""
Strict octave-bracket cutting of a staff image (opt-in: HOMR_STRICT_BRACKET_CUT=1 is version 1, =2 is version 2).

Version 2 (branch strict-bracket-cut-2) verifies the same things with sizes taken from the page (pixel gaps of the dots, staff-line thickness,
blank rows around the dots, a pitch-regularity limit) so that the small dense dots of the Schott print are accepted and text lines are not; see
run/octave_checks/strict_cut2.md. "15ma" and 8vb are not recognised (no support in the development material).

The staff image for the transformer reaches a fixed 4 staff spaces above and below the staff
lines. The line of an 8va bracket is printed higher than that over high passages, so the
bracket is cut off and the model never sees it. The fork's older cutting (octave_bracket_rows,
HOMR_FIXED_MARGIN unset) reaches for it, but also widens the crop for ties, slurs, beams and
text lines, which changes the scale of the input on pages without any bracket.

This version changes the region of a staff only for a bracket which is actually printed:
  * a horizontal DOTTED or DASHED line (several separate ink segments of a bracket's size, with
    gaps between them; slurs, ties, beams, pedal lines and rules are continuous and are rejected),
  * with a NUMERAL ("8", "15", "22") at its left end: a compact component or group of components
    which is as high as a figure of the font and overlaps the row of the line,
  * longer than _MIN_LENGTH_IN_UNITS,
  * owned by this staff (the same ownership rule as before: closer to it than to the other staff).
Without such a line the region is exactly the fixed one: bit-identical crops.
A bracket which continues from the previous system starts at the left edge of the staff without a
numeral and is not reached for (documented limit, 3 of 28 scans' failing segments).
"""

import os

import cv2
import numpy as np

from homr.type_definitions import NDArray

_SEARCH_ABOVE_IN_UNITS = 10.0
_MIN_LENGTH_IN_UNITS = 2.0
_MAX_THICKNESS_IN_UNITS = 0.45
_MIN_SEGMENTS = 5
_MAX_SEGMENT_IN_UNITS = 1.6
_MIN_GAP_IN_UNITS = 0.12
_MAX_GAP_IN_UNITS = 1.8
_MIN_INK_SHARE = 0.03
_MAX_INK_SHARE = 0.75
# the numeral: height and width of a figure, in staff spaces
_NUMERAL_MIN_HEIGHT = 0.7
_NUMERAL_MAX_HEIGHT = 2.4
_NUMERAL_MAX_WIDTH = 3.2
_NUMERAL_LEFT_REACH = 3.0
_NUMERAL_RIGHT_REACH = 0.8
_PADDING_IN_UNITS = 2.0
_LINE_CHECK_LENGTH = 4.0
_NOISE_GAP_IN_UNITS = 0.14
_MAX_PITCH_VARIATION = 0.6
_ISOLATION_NEAR = 0.15
_ISOLATION_FAR = 1.0
_ISOLATION_SKIP_LEFT = 0.0
_ISOLATION_SKIP_RIGHT = 1.0
_MAX_ISOLATION_ABOVE = 0.12
_MAX_ISOLATION_BELOW = 0.30
_MAX_MARK_HEIGHT_IN_UNITS = 0.3
_NUMERAL_HOLES = 1
# 8vb brackets and the shrinking against the next staff's bracket are off in this first strict version: pedal signs and text below a staff gave the false matches
_LOOK_BELOW = False
_MUSIC_SKIP_IN_UNITS = 0.8
_MIN_MUSIC_COLUMNS = 0.08
_MARK_QUANTILE = 80
_OWN_CLEARANCE_IN_UNITS = 4.0
_MAX_OWN_DISTANCE_IN_UNITS = 9.0
_MIN_HOLE_AREA = 3


def _ink(gray: NDArray) -> NDArray:
    _, ink = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return ink


def _gray(image: NDArray) -> NDArray:
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image  # noqa: PLR2004


def _profile(ink: NDArray, y: int, x_left: int, x_right: int, unit: float) -> NDArray:
    """Ink along the row of the line (three pixel rows, small gaps of scan noise closed)."""
    thin = (ink[max(0, y - 1) : y + 2, x_left:x_right] > 0).max(axis=0).astype(np.uint8)
    width = max(2, int(_NOISE_GAP_IN_UNITS * unit))
    return cv2.morphologyEx(
        thin.reshape(1, -1), cv2.MORPH_CLOSE, np.ones((1, width), np.uint8)
    ).reshape(-1)


def _segments(profile: NDArray) -> tuple[NDArray, NDArray]:
    padded = np.concatenate([[0], (profile > 0).astype(np.int8), [0]])
    diff = np.diff(padded)
    return np.where(diff == 1)[0], np.where(diff == -1)[0]


def dotted_stats(profile: NDArray, unit: float) -> str:
    starts, ends = _segments(profile)
    if len(starts) < 3:  # noqa: PLR2004
        return "n=%d" % len(starts)
    seg = (ends - starts) / unit
    gaps = (starts[1:] - ends[:-1]) / unit
    pitch = np.diff(starts)
    return "n=%d seg=%.2f gap=%.2f cv=%.2f cover=%.2f" % (
        len(starts),
        np.median(seg),
        np.median(gaps),
        np.std(pitch) / np.mean(pitch),
        np.count_nonzero(profile) / len(profile),
    )


def _dotted(profile: NDArray, unit: float) -> bool:
    """Several short separate segments with gaps of a bracket's size, evenly spaced; a continuous line or a ledger line with a notehead is not."""
    starts, ends = _segments(profile)
    if len(starts) < _MIN_SEGMENTS + 1:
        return False
    seg = (ends - starts) / unit
    gaps = (starts[1:] - ends[:-1]) / unit
    pitch = np.diff(starts)
    if float(np.median(seg)) > _MAX_SEGMENT_IN_UNITS or float(np.median(gaps)) < _MIN_GAP_IN_UNITS:
        return False
    if float(np.median(gaps)) > _MAX_GAP_IN_UNITS:
        return False
    if float(np.std(pitch)) / float(np.mean(pitch)) > _MAX_PITCH_VARIATION:
        return False
    cover = float(np.count_nonzero(profile)) / len(profile)
    return 0.15 <= cover <= 0.85  # noqa: PLR2004


def _isolated(ink: NDArray, x_left: int, x_right: int, line_y: int, unit: float) -> bool:
    """
    The marks of the line are thin: through the row of the line every dot or dash is only as high as a dot (a letter, a pedal sign or a notehead
    on that row would be taller). Looked at the dots in the middle of the line; the numeral at the left end and the hook at the right end are left out.
    """
    profile = _profile(ink, line_y, x_left, x_right, unit)
    starts, ends = _segments(profile)
    if len(starts) < _MIN_SEGMENTS + 1:
        return False
    heights = []
    limit = int(_MAX_MARK_HEIGHT_IN_UNITS * unit) + 3
    for st, en in zip(starts[1:-1], ends[1:-1], strict=True):
        col = x_left + (st + en) // 2
        up = 0
        while up < limit and line_y - up - 1 >= 0 and ink[line_y - up - 1, col] > 0:
            up += 1
        down = 0
        while down < limit and line_y + down + 1 < ink.shape[0] and ink[line_y + down + 1, col] > 0:
            down += 1
        heights.append(up + down + 1)
    if not heights:
        return False
    return float(np.percentile(heights, _MARK_QUANTILE)) <= _MAX_MARK_HEIGHT_IN_UNITS * unit


def _has_numeral(ink: NDArray, x_start: int, line_y: int, unit: float) -> bool:
    """A figure-sized component (or two side by side) at the left end of the line, overlapping its row."""
    height, width = ink.shape
    x0 = max(0, int(x_start - _NUMERAL_LEFT_REACH * unit))
    x1 = min(width, int(x_start + _NUMERAL_RIGHT_REACH * unit))
    y0 = max(0, int(line_y - 1.8 * unit))
    y1 = min(height, int(line_y + 1.4 * unit))
    if x1 - x0 < 3 or y1 - y0 < 3:  # noqa: PLR2004
        return False
    window = ink[y0:y1, x0:x1]
    count, _labels, stats, _ = cv2.connectedComponentsWithStats(window, connectivity=8)
    figures = []
    for i in range(1, count):
        x, y, w, h, area = stats[i]
        if h < _NUMERAL_MIN_HEIGHT * unit or h > _NUMERAL_MAX_HEIGHT * unit:
            continue
        if w < 0.25 * unit or w > 1.6 * unit:
            continue
        if area / float(w * h) < 0.2 or area / float(w * h) > 0.85:  # noqa: PLR2004
            continue
        # it overlaps the row of the line
        top, bottom = y0 + y, y0 + y + h
        if top <= line_y + 0.5 * unit and bottom >= line_y - 1.2 * unit:
            figures.append((x0 + x, x0 + x + w))
    if not figures:
        return False
    figures.sort()
    # the figure group is not wider than "15ma" or "8va"
    return figures[-1][1] - figures[0][0] <= _NUMERAL_MAX_WIDTH * unit


def _holes(mask: NDArray) -> int:
    """Number of enclosed holes of a component: an "8" has two, letters and pedal signs at most one."""
    contours, hierarchy = cv2.findContours(
        np.pad(mask.astype(np.uint8), 1) * 255, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
    )
    if hierarchy is None:
        return 0
    return sum(
        1
        for k in range(len(contours))
        if hierarchy[0][k][3] >= 0 and cv2.contourArea(contours[k]) >= _MIN_HOLE_AREA
    )


def _music_between(
    ink: NDArray, x_left: int, x_right: int, line_y: int, anchor_y: float, unit: float
) -> bool:
    """An octave bracket stands over music: between the line and the staff there are noteheads, stems or ledger lines along it (a title or a tempo word has blank space below it)."""
    if anchor_y > line_y:
        a, b = int(line_y + _MUSIC_SKIP_IN_UNITS * unit), int(anchor_y - 0.3 * unit)
    else:
        a, b = int(anchor_y + 0.3 * unit), int(line_y - _MUSIC_SKIP_IN_UNITS * unit)
    if b - a < 2:  # noqa: PLR2004
        return False
    band = ink[max(0, a) : max(0, b), x_left:x_right]
    if band.size == 0:
        return False
    return float(np.mean(np.any(band > 0, axis=0))) >= _MIN_MUSIC_COLUMNS


# ---------------------------------------------------------------------------------------------------------------------------------------
# Version 2 (HOMR_STRICT_BRACKET_CUT=2): the same verification, with sizes taken from the page itself (staff line thickness, pixel gaps) instead of
# absolute fractions of a staff space that only hold for one print: dense small dots (gap of 2-3 pixels) were closed into a continuous line by the
# noise closing of 0.14 space, and the thinness limit of 0.3 space rejected the heavier dots of the Schott print.
# ---------------------------------------------------------------------------------------------------------------------------------------


def staff_line_thickness(
    ink: NDArray, top_y: float, unit: float, x_left: int, x_right: int
) -> float:
    """Median thickness in pixels of the five staff lines of the staff whose top line is at top_y (rows where most of the width is ink)."""
    a, b = max(0, int(top_y - 0.5 * unit)), min(ink.shape[0], int(top_y + 4.5 * unit) + 1)
    if b - a < 3 or x_right - x_left < 8:  # noqa: PLR2004
        return max(1.0, 0.08 * unit)
    share = (ink[a:b, x_left:x_right] > 0).mean(axis=1)
    rows = share > 0.5  # noqa: PLR2004
    runs = []
    n = 0
    for v in rows:
        if v:
            n += 1
        elif n:
            runs.append(n)
            n = 0
    if n:
        runs.append(n)
    runs = [r for r in runs if r <= 0.35 * unit]
    return float(np.median(runs)) if runs else max(1.0, 0.08 * unit)


# version 2 constants (set on the development material, tuning part T only; see run/octave_checks/strict_cut2.md)
_V2_CLOSE_PIXELS = (
    1  # closes a one-pixel gap of scan noise, not the 2 to 3 pixel gaps between small dense dots
)
_V2_MIN_SEGMENTS = 5
_V2_MIN_GAP_PIXELS = 2.0
_V2_MAX_PITCH_VARIATION = 0.3
_V2_MAX_EXT_CV = 9.0
_V2_NUMERAL_HOLES = 1
_V2_ALLOW_PAIR = False  # no real "15" in the development material: the pair rule matched only text ("poco", "molto") there, so it is off
_V2_NUMERAL_MAX_WIDTH = 1.9  # in staff spaces; the figure may touch the first dot of its line
_V2_MIN_CLEAR_DOTS = 0.4  # share of the dots with blank rows just above and below
_V2_NEIGHBOUR_NEAR = 0.15
_V2_NEIGHBOUR_FAR = 0.35
_V2_START_OFFSETS = (
    0.15,
    0.9,
    1.7,
)  # the line starts right of the numeral, or right of "va" / "ma"
_V2_MARK_FACTOR = 3.0  # dots are at most this many staff-line thicknesses high ...
_V2_MARK_MIN_UNITS = 0.3  # ... but at least as before
_V2_MARK_CAP_UNITS = 0.4  # ... and never as tall as a letter
_V2_PAIR_MAX_GAP = 0.35
_V2_PAIR_MAX_DTOP = 0.3
_V2_PAIR_MIN_HEIGHT = 0.7
_V2_PAIR_MAX_HEIGHT = 1.8


def _profile_v2(ink: NDArray, y: int, x_left: int, x_right: int) -> NDArray:
    thin = (ink[max(0, y - 1) : y + 2, x_left:x_right] > 0).max(axis=0).astype(np.uint8)
    if _V2_CLOSE_PIXELS <= 1:
        return thin
    return cv2.morphologyEx(
        thin.reshape(1, -1), cv2.MORPH_CLOSE, np.ones((1, _V2_CLOSE_PIXELS), np.uint8)
    ).reshape(-1)


def _dotted_v2(profile: NDArray, unit: float) -> bool:
    """Evenly spaced separate marks: gaps counted in pixels, not as a fraction of a staff space (a dense dotted line has gaps of 2 to 3 pixels)."""
    starts, ends = _segments(profile)
    if len(starts) < _V2_MIN_SEGMENTS:
        return False
    seg = ends - starts
    gaps = starts[1:] - ends[:-1]
    pitch = np.diff(starts)
    if (
        float(np.median(gaps)) < _V2_MIN_GAP_PIXELS
        or float(np.median(gaps)) > _MAX_GAP_IN_UNITS * unit
    ):
        return False
    if float(np.median(seg)) > _MAX_SEGMENT_IN_UNITS * unit:
        return False
    if float(np.std(pitch)) / float(np.mean(pitch)) > _V2_MAX_PITCH_VARIATION:
        return False
    cover = float(np.count_nonzero(profile)) / len(profile)
    return 0.15 <= cover <= 0.85  # noqa: PLR2004


def _dot_heights_v2(ink: NDArray, x_left: int, x_right: int, line_y: int, unit: float) -> list[int]:
    """Vertical extent in pixels of the marks in the middle of the line (the first and the last, numeral side and hook, are left out)."""
    profile = _profile_v2(ink, line_y, x_left, x_right)
    starts, ends = _segments(profile)
    limit = int(_V2_MARK_CAP_UNITS * unit) + 3
    heights = []
    for st, en in zip(starts[1:-1], ends[1:-1], strict=True):
        col = x_left + (st + en) // 2
        up = 0
        while up < limit and line_y - up - 1 >= 0 and ink[line_y - up - 1, col] > 0:
            up += 1
        down = 0
        while down < limit and line_y + down + 1 < ink.shape[0] and ink[line_y + down + 1, col] > 0:
            down += 1
        heights.append(up + down + 1)
    return heights


def _clear_neighbourhood_v2(
    ink: NDArray, x_left: int, x_right: int, line_y: int, unit: float, dot_height: float
) -> bool:
    """
    A dotted line stands alone on its row: for most of its dots there is no ink just above and just below (beyond the dot itself, up to 0.35
    space away); letters of a text line fill those rows. A slur, a stem or an accent that touches a few dots does not matter.
    """
    near = int(dot_height / 2) + 2
    far = max(near + 2, int(_V2_NEIGHBOUR_FAR * unit))
    starts, ends = _segments(_profile_v2(ink, line_y, x_left, x_right))
    if len(starts) == 0:
        return False
    clear = 0
    for st, en in zip(starts, ends, strict=True):
        cols = slice(x_left + st, x_left + en)
        above = ink[max(0, line_y - far) : max(0, line_y - near), cols]
        below = ink[line_y + near + 1 : line_y + far + 1, cols]
        if not (above.any() or below.any()):
            clear += 1
    return clear / len(starts) >= _V2_MIN_CLEAR_DOTS


def _thin_marks_v2(heights: list[int], unit: float, thickness: float) -> bool:
    """The dots in the middle of the line are as high as a few staff-line thicknesses (letters, pedal signs and noteheads on that row are taller)."""
    if len(heights) < _V2_MIN_SEGMENTS - 2:
        return False
    limit_units = min(
        max(_V2_MARK_MIN_UNITS, _V2_MARK_FACTOR * thickness / unit), _V2_MARK_CAP_UNITS
    )
    if float(np.std(heights)) / float(np.mean(heights)) > _V2_MAX_EXT_CV:
        return False
    return float(np.percentile(heights, _MARK_QUANTILE)) <= limit_units * unit


def find_bracket_lines_v2(  # noqa: PLR0917
    image: NDArray,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    unit: float,
    debug: list | None = None,
    anchor_y: float | None = None,
) -> list[tuple[float, float]]:
    """(y, x of the numeral) of every printed octave bracket in the band: version 2 of find_bracket_lines (pixel gaps, thickness-relative dots, "15", later starts)."""
    height, width = image.shape[:2]
    x0, x1 = max(0, int(x_min)), min(width, int(x_max))
    y0, y1 = max(0, int(y_min)), min(height, int(y_max))
    if y1 - y0 < 3 or x1 - x0 < _MIN_LENGTH_IN_UNITS * unit:  # noqa: PLR2004
        return []
    pad = int(2 * unit)
    ya, yb = max(0, y0 - pad), min(height, y1 + pad)
    ink = _ink(_gray(image[ya:yb, :]))
    thickness = 0.1 * unit
    if anchor_y is not None:
        thickness = staff_line_thickness(
            _ink(
                _gray(image[int(max(0, anchor_y - unit)) : int(min(height, anchor_y + 5 * unit))])
            ),
            unit,
            unit,
            x0,
            x1,
        )
    count, labels, stats, _ = cv2.connectedComponentsWithStats(ink[:, x0:x1], connectivity=8)
    # only components whose middle is in the band
    keep = [i for i in range(1, count) if y0 <= ya + stats[i][1] + stats[i][3] / 2 <= y1]
    found: list[tuple[float, float]] = []
    numerals = []
    for i in keep:
        x, y, w, h, area = (int(v) for v in stats[i])
        if (
            _NUMERAL_MIN_HEIGHT * unit <= h <= _NUMERAL_MAX_HEIGHT * unit
            and 0.3 * unit <= w <= _V2_NUMERAL_MAX_WIDTH * unit
        ):  # noqa: PLR2004
            fill = area / float(w * h)
            if (
                0.25 <= fill <= 0.85
                and _holes(labels[y : y + h, x : x + w] == i) >= _V2_NUMERAL_HOLES
            ):  # noqa: PLR2004
                numerals.append((x0 + x, x0 + x + w, ya + y + h / 2, h, "8"))
    boxes = sorted(
        (int(stats[i][0]), int(stats[i][1]), int(stats[i][2]), int(stats[i][3]))
        for i in keep
        if _V2_PAIR_MIN_HEIGHT * unit <= stats[i][3] <= _V2_PAIR_MAX_HEIGHT * unit
        and 0.12 * unit <= stats[i][2] <= 0.9 * unit
    )  # noqa: PLR2004
    for a, b in zip(boxes[:-1], boxes[1:], strict=True) if _V2_ALLOW_PAIR else []:
        gap = b[0] - (a[0] + a[2])
        if (
            -0.1 * unit <= gap <= _V2_PAIR_MAX_GAP * unit
            and abs(a[1] - b[1]) <= _V2_PAIR_MAX_DTOP * unit
            and abs(a[3] - b[3]) <= _V2_PAIR_MAX_DTOP * unit
        ):
            numerals.append((x0 + a[0], x0 + b[0] + b[2], ya + a[1] + a[3] / 2, a[3], "pair"))
    for nx, nright, ncy, nh, kind in numerals:
        best = None
        for offset in _V2_START_OFFSETS:
            xs = nright + int(offset * unit)
            xe = min(width, xs + int(_LINE_CHECK_LENGTH * unit))
            if xe - xs < 2 * unit:  # noqa: PLR2004
                continue
            rows = []
            for dy in range(-int(0.9 * unit), int(0.5 * unit) + 1):
                row_y = int(ncy + dy)
                if row_y - ya < 2 or row_y - ya >= ink.shape[0] - 2:  # noqa: PLR2004
                    continue
                if _dotted_v2(_profile_v2(ink, row_y - ya, xs, xe), unit):
                    rows.append(row_y)
                elif rows:
                    break
            if rows:
                best = (rows[len(rows) // 2], xs, xe)  # the middle of the rows that show the dots
                break
        if best is None:
            if debug is not None:
                debug.append((ncy, "numeral_no_line"))
            continue
        row_y, xs, xe = best
        heights = _dot_heights_v2(ink, xs, xe, row_y - ya, unit)
        if not _thin_marks_v2(heights, unit, thickness):
            if debug is not None:
                debug.append((row_y, "not_isolated"))
            continue
        if not _clear_neighbourhood_v2(ink, xs, xe, row_y - ya, unit, float(np.median(heights))):
            if debug is not None:
                debug.append((row_y, "text_around"))
            continue
        if anchor_y is not None and not _music_between(
            ink, xs, xe, row_y - ya, anchor_y - ya, unit
        ):
            if debug is not None:
                debug.append((row_y, "no_music_below"))
            continue
        if debug is not None:
            debug.append((row_y, "found %.2f %.2f %s" % (nh / unit, (nright - nx) / unit, kind)))
        found.append((float(row_y), float(nx)))
    return sorted(set(found))


def _version() -> int:
    return 2 if os.environ.get("HOMR_STRICT_BRACKET_CUT") == "2" else 1


def find_bracket_lines(  # noqa: PLR0917
    image: NDArray,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    unit: float,
    debug: list | None = None,
    anchor_y: float | None = None,
) -> list[tuple[float, float]]:
    """
    (y, x of the numeral) of every printed octave bracket in the band: a figure ("8", "15") with a dotted or dashed line starting right of it
    at the height of the figure, nothing else on that row of the line (no noteheads, ledger lines, slurs, text).
    """
    height, width = image.shape[:2]
    x0, x1 = max(0, int(x_min)), min(width, int(x_max))
    y0, y1 = max(0, int(y_min)), min(height, int(y_max))
    if y1 - y0 < 3 or x1 - x0 < _MIN_LENGTH_IN_UNITS * unit:  # noqa: PLR2004
        return []
    pad = int(2 * unit)
    ya, yb = max(0, y0 - pad), min(height, y1 + pad)
    ink = _ink(_gray(image[ya:yb, :]))
    count, _labels, stats, _ = cv2.connectedComponentsWithStats(ink[:, x0:x1], connectivity=8)
    found: list[tuple[float, float]] = []
    for i in range(1, count):
        x, y, w, h, area = stats[i]
        cy = ya + y + h / 2
        if not (y0 <= cy <= y1):
            continue
        if not (
            _NUMERAL_MIN_HEIGHT * unit <= h <= _NUMERAL_MAX_HEIGHT * unit
            and 0.3 * unit <= w <= 1.4 * unit
        ):  # noqa: PLR2004
            continue
        fill = area / float(w * h)
        if not 0.25 <= fill <= 0.85:  # noqa: PLR2004
            continue
        if _holes(_labels[y : y + h, x : x + w] == i) < _NUMERAL_HOLES:
            continue
        # the line: a dotted row right of the figure (right edge of a second figure, "15" / "22", is skipped)
        x_right = x0 + x + w
        best = None
        for dy in range(-int(0.9 * unit), int(0.5 * unit) + 1):
            row_y = int(ya + y + h / 2 + dy)
            xs = x_right + int(0.15 * unit)
            xe = min(width, xs + int(_LINE_CHECK_LENGTH * unit))
            if xe - xs < 2 * unit or row_y - ya < 2 or row_y - ya >= ink.shape[0] - 2:  # noqa: PLR2004
                continue
            profile = _profile(ink, row_y - ya, xs, xe, unit)
            if _dotted(profile, unit):
                best = (row_y, xs, xe)
                break
        if best is None:
            if debug is not None:
                debug.append((cy, "numeral_no_line"))
            continue
        row_y, xs, xe = best
        if not _isolated(ink, xs, xe, row_y - ya, unit):
            if debug is not None:
                debug.append((row_y, "not_isolated"))
            continue
        if anchor_y is not None and not _music_between(
            ink, xs, xe, row_y - ya, anchor_y - ya, unit
        ):
            if debug is not None:
                debug.append((row_y, "no_music_below"))
            continue
        found.append((float(row_y), float(x0 + x)))
    return sorted(found)


def owner_is_below(
    line_y: float, bottom_of_upper: float, top_of_lower: float, unit: float = 0.0
) -> bool:
    """
    A line between two staffs belongs to the lower one unless it hangs right below the upper one (pedal signs, dynamics and text sit within
    _OWN_CLEARANCE_IN_UNITS of the upper staff; an 8va floats above the high notes of its own staff).
    """
    if unit > 0:
        return (line_y - bottom_of_upper) >= _OWN_CLEARANCE_IN_UNITS * unit and (
            top_of_lower - line_y
        ) <= _MAX_OWN_DISTANCE_IN_UNITS * unit
    return (top_of_lower - line_y) <= (line_y - bottom_of_upper)


def strict_region_y(  # noqa: PLR0917
    staff_min_y: float,
    staff_max_y: float,
    unit: float,
    image: NDArray,
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    neighbors: tuple[float, float],
) -> tuple[float, float]:
    """The fixed y range, widened to hold a verified bracket of this staff (and nothing else)."""
    y_min, y_max = y_range
    staff_above, staff_below = neighbors
    pad = _PADDING_IN_UNITS * unit
    find = find_bracket_lines_v2 if _version() == 2 else find_bracket_lines  # noqa: PLR2004
    # above: only a line that the fixed region would cut
    top = max(staff_above + 0.5 * unit, staff_min_y - _SEARCH_ABOVE_IN_UNITS * unit, 0)
    if top < y_min + pad:
        for line_y, _x in find(
            image, *x_range, top, staff_min_y - 0.5 * unit, unit, anchor_y=staff_min_y
        ):
            if owner_is_below(line_y, staff_above, staff_min_y, unit) and line_y - pad < y_min:
                y_min = max(line_y - pad, staff_above, 0)
    # below: 8vb of this staff, a bracket of the staff below must stay outside
    bottom = min(
        staff_below - 0.5 * unit, staff_max_y + _SEARCH_ABOVE_IN_UNITS * unit, image.shape[0]
    )
    if _LOOK_BELOW and bottom > y_max - pad:
        for line_y, _x in find(
            image, *x_range, staff_max_y + 0.5 * unit, bottom, unit, anchor_y=staff_max_y
        ):
            if staff_below < image.shape[0] and owner_is_below(
                line_y, staff_max_y, staff_below, unit
            ):
                y_max = min(y_max, line_y - 0.5 * unit)
            elif line_y + pad > y_max:
                y_max = min(line_y + pad, staff_below)
    return y_min, y_max
