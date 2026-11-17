# ruff: noqa: S101

import os
from pathlib import Path

import cv2
import numpy as np
import pytest

from homr.hires_page import load_hires_page
from homr.point_mapping import chain, undo_crop, undo_resize


def test_without_the_variable_nothing_is_loaded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HOMR_HIRES_DIR", raising=False)
    assert load_hires_page("page.png", (10, 10), lambda p: p) is None


def test_the_render_is_cut_to_the_page_image(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    low, high = tmp_path / "low", tmp_path / "high"
    low.mkdir()
    high.mkdir()
    cv2.imwrite(str(low / "page.png"), np.full((100, 200, 3), 255, np.uint8))
    render = np.full((300, 600, 3), 255, np.uint8)
    render[150:300, 300:600] = 0
    cv2.imwrite(str(high / "page.png"), render)
    monkeypatch.setenv("HOMR_HIRES_DIR", str(high))
    # The page image is the bottom right quarter of the input (crop at (100, 50)), enlarged 2x
    page_shape = (100, 200)
    to_input = chain(undo_resize((50, 100), page_shape), undo_crop(100, 50))
    page = load_hires_page(os.path.join(low, "page.png"), page_shape, to_input)
    assert page is not None
    assert page.image.shape == (150, 300)
    assert page.scale_x == pytest.approx(1.5)
    assert page.scale_y == pytest.approx(1.5)
    assert page.image.max() < 50  # only the dark quarter of the render was cut out


def test_a_missing_render_is_an_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOMR_HIRES_DIR", str(tmp_path))
    with pytest.raises(ValueError):
        load_hires_page("page.png", (10, 10), lambda p: p)
