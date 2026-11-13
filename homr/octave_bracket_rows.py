"""
Finds the dashed or dotted lines of octave brackets in the space between two systems.

The staff image for the transformer is cut with a fixed margin around the staff lines.
An octave bracket floats above the highest note under it, so over high passages it ends
up outside that margin, or closer to the system above than to its own, where it is read
as an octave-lower bracket of the wrong staff. Knowing the rows of these lines lets the
region of a staff reach up to its bracket and stop short of the next one's.
"""

import cv2
import numpy as np

from homr.type_definitions import NDArray

# A dashed line bridged with a kernel of this many staff spaces becomes one long run
_BRIDGE_IN_UNITS = 1.3
_MIN_LENGTH_IN_UNITS = 4.0
_MAX_THICKNESS_IN_UNITS = 0.6
# Share of ink along the line: a solid line (pedal or volta bracket) is close to 1
_MIN_INK_SHARE = 0.12
_MAX_INK_SHARE = 0.8
# A blank band taller than this separates the content of two systems
_MAX_BLANK_IN_UNITS = 1.2


def find_dashed_line_rows(  # noqa: PLR0917
    image: NDArray, x_min: float, x_max: float, y_min: float, y_max: float, unit_size: float
) -> list[float]:
    """The y positions, in image coordinates, of long dashed or dotted horizontal lines."""
    height, width = image.shape[:2]
    x0, x1 = max(0, int(x_min)), min(width, int(x_max))
    y0, y1 = max(0, int(y_min)), min(height, int(y_max))
    if y1 - y0 < 3 or x1 - x0 < _MIN_LENGTH_IN_UNITS * unit_size:  # noqa: PLR2004
        return []
    gap = image[y0:y1, x0:x1]
    if gap.ndim == 3:  # noqa: PLR2004
        gap = cv2.cvtColor(gap, cv2.COLOR_BGR2GRAY)
    _, ink = cv2.threshold(gap, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    bridge = cv2.getStructuringElement(
        cv2.MORPH_RECT, (max(3, int(_BRIDGE_IN_UNITS * unit_size)), 3)
    )
    bridged = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, bridge)
    long_run = cv2.getStructuringElement(
        cv2.MORPH_RECT, (max(5, int(_MIN_LENGTH_IN_UNITS * unit_size)), 1)
    )
    lines = cv2.morphologyEx(bridged, cv2.MORPH_OPEN, long_run)

    rows: list[float] = []
    count, _labels, stats, _centroids = cv2.connectedComponentsWithStats(lines, connectivity=8)
    for i in range(1, count):
        x, y, w, h, _area = stats[i]
        if h > _MAX_THICKNESS_IN_UNITS * unit_size or w < _MIN_LENGTH_IN_UNITS * unit_size:
            continue
        ink_share = float(np.count_nonzero(ink[y : y + h, x : x + w])) / float(w * h)
        if _MIN_INK_SHARE <= ink_share <= _MAX_INK_SHARE:
            rows.append(y0 + y + h / 2)
    return sorted(rows)


def find_top_of_content(  # noqa: PLR0917
    image: NDArray, x_min: float, x_max: float, y_start: float, y_limit: float, unit_size: float
) -> float:
    """
    Walks up from y_start and returns the top of the ink which is attached to what lies
    below: the walk ends at the first blank band of more than a staff space, or at y_limit.
    High notes with their beams, tuplet brackets and short octave brackets are stacked
    without such a band, while the system above is set apart by one.
    """
    height, width = image.shape[:2]
    x0, x1 = max(0, int(x_min)), min(width, int(x_max))
    y0, y1 = max(0, int(y_limit)), min(height, int(y_start))
    if y1 - y0 < 2 or x1 <= x0:  # noqa: PLR2004
        return y_start
    band = image[y0:y1, x0:x1]
    if band.ndim == 3:  # noqa: PLR2004
        band = cv2.cvtColor(band, cv2.COLOR_BGR2GRAY)
    _, ink = cv2.threshold(band, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    has_ink = np.count_nonzero(ink, axis=1) >= max(2, int(0.002 * (x1 - x0)))
    max_blank = max(2, int(_MAX_BLANK_IN_UNITS * unit_size))
    top = y1
    blank = 0
    for row in range(y1 - y0 - 1, -1, -1):
        if has_ink[row]:
            top = y0 + row
            blank = 0
        else:
            blank += 1
            if blank > max_blank:
                break
    return float(top)
