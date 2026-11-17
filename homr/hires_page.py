"""
A higher resolution render of a page as the source of the staff crops (resolution experiment).

HOMR_HIRES_DIR names a folder with a render of the page at a higher resolution under the
same file name as the input image, e.g. page-018.png at 225 dpi next to the 150 dpi page.
Staff detection, layout and the crop rectangle of every staff are still found on the normal
page image; only the pixels which are cut out for the transformer come from the render, so
every crop covers the same part of the page as without it. Without the variable nothing
changes.
"""

import os
from dataclasses import dataclass

import cv2

from homr import color_adjust
from homr.point_mapping import PointMapping
from homr.type_definitions import NDArray


@dataclass
class HiresPage:
    """
    The part of the render which covers the page image that the staffs were found on:
    image is grayscale like that page image, scale_x and scale_y are its pixels per
    pixel of the page image.
    """

    image: NDArray
    scale_x: float
    scale_y: float


def load_hires_page(
    image_path: str, page_shape: tuple[int, ...], page_to_input_image: PointMapping
) -> HiresPage | None:
    """
    page_shape is the shape of the page image the staffs were found on and
    page_to_input_image maps its coordinates to the input image (undoing autocrop and
    resizing), which is how the part of the render is found: the corners of the page image
    are mapped to the input image and from there to the render, whose size relative to the
    input image gives the factor per axis.
    """
    folder = os.environ.get("HOMR_HIRES_DIR")
    if not folder:
        return None
    path = os.path.join(folder, os.path.basename(image_path))
    hires = cv2.imread(path)
    if hires is None:
        raise ValueError(
            f"HOMR_HIRES_DIR is set but {path} can't be read, "
            "render every page of the input at a higher resolution"
        )
    original = cv2.imread(image_path)
    if original is None:
        raise ValueError("Failed to read " + image_path)
    factor_x = hires.shape[1] / original.shape[1]
    factor_y = hires.shape[0] / original.shape[0]
    left, top = page_to_input_image((0.0, 0.0))
    right, bottom = page_to_input_image((float(page_shape[1]), float(page_shape[0])))
    x0, x1 = round(left * factor_x), round(right * factor_x)
    y0, y1 = round(top * factor_y), round(bottom * factor_y)
    part = hires[max(y0, 0) : y1, max(x0, 0) : x1]
    if part.size == 0:
        raise ValueError(f"{path} doesn't cover the page {image_path}")
    gray = color_adjust.apply_clahe(part)
    return HiresPage(gray, gray.shape[1] / page_shape[1], gray.shape[0] / page_shape[0])
