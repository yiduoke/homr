"""Cuts the MuseScore staff images of scores with octave shifts again.

The staff images were cut around stems and dynamics, so an octave bracket was inside
the image or not depending on how far it floats above the notes. musescore_svg now
extends a staff to its brackets; this writes those images, with their unchanged tokens,
to their own folder and index. The rendered SVGs are reused, nothing is engraved again.

    PYTHONPATH=. python training/omr_datasets/recrop_musescore_octave.py
"""

import multiprocessing
import os
from pathlib import Path

from homr.simple_logging import eprint
from training.omr_datasets.convert_lieder import convert_xml_and_svg_file, dataset_root, lieder
from training.omr_datasets.convert_musetrainer import musetrainer_root
from training.omr_datasets.convert_pdmx import pdmx_root

octave_root = os.path.join(dataset_root, "musescore_octave")
octave_flat = os.path.join(octave_root, "flat")
octave_index = os.path.join(octave_root, "index.txt")


def _convert(file: Path) -> list[str]:
    return convert_xml_and_svg_file(file, False, octave_flat, fail_if_image_is_missing=False)


def main() -> None:
    files: list[Path] = []
    for root in (lieder, pdmx_root, musetrainer_root):
        for file in sorted(Path(root, "rendered_scores").glob("*.musicxml")):
            with open(file, errors="ignore") as f:
                if "<octave-shift" in f.read():
                    files.append(file)
    eprint("Cutting the staffs of", len(files), "scores with octave shifts again")
    os.makedirs(octave_flat, exist_ok=True)
    staffs = 0
    with open(octave_index, "w") as index, multiprocessing.Pool(4) as pool:
        for done, lines in enumerate(pool.imap_unordered(_convert, files), start=1):
            index.writelines(lines)
            staffs += len(lines)
            if done % 50 == 0 or done == len(files):
                eprint(f"{done}/{len(files)} scores, {staffs} staffs")


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")
    main()
