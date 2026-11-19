"""
Strict octave-bracket cutting of a staff image (opt-in, HOMR_STRICT_BRACKET_CUT=1).

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
    return cv2.morphologyEx(thin.reshape(1, -1), cv2.MORPH_CLOSE, np.ones((1, width), np.uint8)).reshape(-1)


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
    return "n=%d seg=%.2f gap=%.2f cv=%.2f cover=%.2f" % (len(starts), np.median(seg), np.median(gaps), np.std(pitch) / np.mean(pitch), np.count_nonzero(profile) / len(profile))


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
    contours, hierarchy = cv2.findContours(np.pad(mask.astype(np.uint8), 1) * 255, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is None:
        return 0
    return sum(1 for k in range(len(contours)) if hierarchy[0][k][3] >= 0 and cv2.contourArea(contours[k]) >= _MIN_HOLE_AREA)


def _music_between(ink: NDArray, x_left: int, x_right: int, line_y: int, anchor_y: float, unit: float) -> bool:
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
        if not (_NUMERAL_MIN_HEIGHT * unit <= h <= _NUMERAL_MAX_HEIGHT * unit and 0.3 * unit <= w <= 1.4 * unit):  # noqa: PLR2004
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
        if anchor_y is not None and not _music_between(ink, xs, xe, row_y - ya, anchor_y - ya, unit):
            if debug is not None:
                debug.append((row_y, "no_music_below"))
            continue
        found.append((float(row_y), float(x0 + x)))
    return sorted(found)


def owner_is_below(line_y: float, bottom_of_upper: float, top_of_lower: float, unit: float = 0.0) -> bool:
    """
    A line between two staffs belongs to the lower one unless it hangs right below the upper one (pedal signs, dynamics and text sit within
    _OWN_CLEARANCE_IN_UNITS of the upper staff; an 8va floats above the high notes of its own staff).
    """
    if unit > 0:
        return (line_y - bottom_of_upper) >= _OWN_CLEARANCE_IN_UNITS * unit and (top_of_lower - line_y) <= _MAX_OWN_DISTANCE_IN_UNITS * unit
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
    # above: only a line that the fixed region would cut
    top = max(staff_above + 0.5 * unit, staff_min_y - _SEARCH_ABOVE_IN_UNITS * unit, 0)
    if top < y_min + pad:
        for line_y, _x in find_bracket_lines(image, *x_range, top, staff_min_y - 0.5 * unit, unit, anchor_y=staff_min_y):
            if owner_is_below(line_y, staff_above, staff_min_y, unit) and line_y - pad < y_min:
                y_min = max(line_y - pad, staff_above, 0)
    # below: 8vb of this staff, a bracket of the staff below must stay outside
    bottom = min(staff_below - 0.5 * unit, staff_max_y + _SEARCH_ABOVE_IN_UNITS * unit, image.shape[0])
    if _LOOK_BELOW and bottom > y_max - pad:
        for line_y, _x in find_bracket_lines(image, *x_range, staff_max_y + 0.5 * unit, bottom, unit, anchor_y=staff_max_y):
            if staff_below < image.shape[0] and owner_is_below(line_y, staff_max_y, staff_below, unit):
                y_max = min(y_max, line_y - 0.5 * unit)
            elif line_y + pad > y_max:
                y_max = min(line_y + pad, staff_below)
    return y_min, y_max
