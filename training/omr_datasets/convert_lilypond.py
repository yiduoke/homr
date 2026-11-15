"""Staff images engraved by LilyPond from the MusicXML which MuseScore exported.

Why: a model trained only on MuseScore renders reads an octave bracket labelled with
a bold "8" but misses the same bracket labelled with an italic "8va", which is what
LilyPond 2.18-era scores (most of Mutopia) print. The labels are the same tokens the
MuseScore pipeline writes (music_xml_file_to_tokens + MeasureCutter); only the picture
changes, so no answer key has to be invented.

How a page becomes staff crops:
  1. musicxml2ly converts the MusicXML, LilyPond chooses its own line and page breaks.
  2. LilyPond engraves the page once, with the SVG backend, where the grobs we care about
     carry a class via `output-attributes`. That one SVG gives the geometry and, through
     rsvg-convert, the picture. Engraving a second time for the picture does not work:
     LilyPond's backends measure text differently, and with lyrics the second run broke
     the lines elsewhere in a third of the scores, so pictures and tokens disagreed.
  3. Staff lines and bar lines from the SVG give each staff its box and its number of
     measures; MeasureCutter hands out that many measures per staff, top to bottom.
  4. A sample is kept only if the picture agrees with its tokens: same number of note
     heads and of octave brackets. musicxml2ly is lossy, this is what keeps its
     mistakes out of the labels.

Runs from the repo root of a checkout of feature/octave_shifts:
    PYTHONPATH=. python training/omr_datasets/convert_lilypond.py [--all | --share 0.1] FILES...
"""

import hashlib
import json
import multiprocessing
import os
import random
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

import cv2

from homr.circle_of_fifths import strip_naturals
from homr.simple_logging import eprint
from homr.transformer.vocabulary import EncodedSymbol
from training.omr_datasets.convert_lieder import (
    MeasureCutter,
    contains_only_supported_clefs,
    get_svg_voice_count,
    is_grandstaff,
    write_text_to_file,
)
from training.omr_datasets.music_xml_parser import music_xml_file_to_tokens
from training.omr_datasets.time_signatures import UnsupportedTimeSignatureError
from training.transformer.image_utils import crop_info_path
from training.transformer.training_vocabulary import token_lines_to_str

script_location = os.path.dirname(os.path.realpath(__file__))
git_root = Path(script_location).parent.parent.absolute()
lily_root = os.path.join(git_root, "datasets", "lilypond")
flat_lily = os.path.join(lily_root, "flat")
lily_train_index = os.path.join(lily_root, "index.txt")

RASTER_WIDTH = 1400
# Set to render the same scores a second time with other styles and sizes; it is part
# of the file names, so the passes don't overwrite each other.
VARIANT = os.environ.get("LILY_VARIANT", "")
STORED_MARGIN_IN_STAFF_SPACES = 6
# Grobs farther from the staff lines than this belong to another staff
MAX_DISTANCE_IN_STAFF_SPACES = 9
_SVG = "{http://www.w3.org/2000/svg}"
_TRANSLATE = re.compile(r"translate\(\s*(-?[\d.]+)[,\s]+(-?[\d.]+)\s*\)")

# A pianist reads any octave bracket by two things: an "8" and a dashed line, above the
# staff for 8va and below it for 8vb. Everything else differs between editions. A model
# shown one label style learns that style instead (round one found a bold "8" and missed
# an italic "8va" on the same page), so everything else is varied per file here: the
# wording, its font, the dashes, the hook. The wording is drawn independently of the
# direction for part of the files, as editions also print a plain "8" or "8va" below the
# staff, which leaves the position as the only way to tell the two apart.
_LABELS_ABOVE: list[tuple[float, str]] = [
    (0.42, '"8va"'),
    (0.22, '"8"'),
    (0.20, '(markup #:concat ("8" #:super "va"))'),
    (0.08, '"8ve"'),
    (0.08, '(markup #:concat ("8" #:super "a"))'),
]
_LABELS_BELOW: list[tuple[float, str]] = [
    (0.24, '"8va bassa"'),
    (0.24, '"8vb"'),
    (0.20, '"8"'),
    (0.14, '"8va"'),
    (0.10, '"8ba"'),
    (0.08, '(markup #:concat ("8" #:super "va") " bassa")'),
]


def _ottava_style(rng: random.Random) -> str:
    above = _pick_weighted(rng, _LABELS_ABOVE)
    below = _pick_weighted(rng, _LABELS_BELOW)
    lines = [
        f'ottavationMarkups = #`((1 . ,{above}) (-1 . ,{below}) (2 . "15ma") (-2 . "15mb"))',
        f"\\override OttavaBracket.font-series = #'{rng.choice(['medium', 'medium', 'bold'])}",
        f"\\override OttavaBracket.font-shape = #'{rng.choice(['italic', 'italic', 'upright'])}",
        f"\\override OttavaBracket.font-size = #{rng.choice([-2, -1, 0, 0, 1])}",
        # From dots to long dashes
        f"\\override OttavaBracket.dash-fraction = #{rng.choice([0.08, 0.15, 0.3, 0.3, 0.5])}",
        f"\\override OttavaBracket.dash-period = #{rng.choice([0.6, 0.8, 1.0, 1.0, 1.4])}",
    ]
    if rng.random() < 0.25:  # noqa: PLR2004
        lines.append("\\override OttavaBracket.edge-height = #'(0 . 0)")  # no hook at the end
    # LilyPond keeps a bracket well clear of the notes, older engravings set it right on
    # top of them. Drawn last, so the choices above stay what they were per file.
    if rng.random() < float(os.environ.get("LILY_TIGHT_OTTAVA", "0")):
        lines.extend(
            [
                "\\override OttavaBracket.padding = #0.1",
                "\\override OttavaBracket.staff-padding = #0.2",
                "\\override OttavaBracket.outside-staff-padding = #0.05",
            ]
        )
    return "\n      ".join(lines)


_STAFF_SIZES = [15, 16, 17, 18, 19, 20]

_TAGS = {
    "StaffSymbol": "hStaff",
    "BarLine": "hBar",
    "Stem": "hStem",
    "DynamicText": "hDyn",
    "NoteHead": "hNote",
    "Rest": "hRest",
    "MultiMeasureRest": "hRest",
}


def _random_for(name: str) -> random.Random:
    return random.Random(int(hashlib.sha256(name.encode()).hexdigest(), 16))  # noqa: S311


def _pick_weighted(rng: random.Random, options: list[tuple[float, str]]) -> str:
    threshold = rng.random() * sum(weight for weight, _ in options)
    for weight, value in options:
        threshold -= weight
        if threshold <= 0:
            return value
    return options[-1][1]


_OTHER_DYNAMICS_ALONE = re.compile(
    r"<dynamics\b[^>]*>\s*<other-dynamics\b[^>]*>(.*?)</other-dynamics>\s*</dynamics>", re.S
)
_OTHER_DYNAMICS = re.compile(r"<other-dynamics\b[^>]*>.*?</other-dynamics>", re.S)
_LYRICS = re.compile(r"<lyric(?:\s[^>]*)?>.*?</lyric>", re.S)
# Lyrics aren't in the tokens. Half of the songs are engraved without them, which gives
# their piano parts the look of plain piano music.
_P_DROP_LYRICS = 0.5


def _without_other_dynamics(musicxml_file: str, work_file: str, name: str) -> str:
    """
    musicxml2ly turns <other-dynamics>dolce</other-dynamics> into a LilyPond variable
    named after the text ("dolce.", "più", "ad libitum"), which rarely is a valid name
    and fails more than half of the Lieder. Written as plain words the text is engraved
    the same way and the conversion goes through.
    """
    with open(musicxml_file, encoding="utf-8", errors="ignore") as f:
        xml = f.read()
    drop_lyrics = "<lyric" in xml and _random_for("lyrics" + name).random() < _P_DROP_LYRICS
    if "<other-dynamics" not in xml and not drop_lyrics:
        return musicxml_file
    xml = _OTHER_DYNAMICS_ALONE.sub(r'<words font-style="italic">\1</words>', xml)
    xml = _OTHER_DYNAMICS.sub("", xml)
    if drop_lyrics:
        xml = _LYRICS.sub("", xml)
    with open(work_file, "w", encoding="utf-8") as f:
        f.write(xml)
    return work_file


def write_ly(musicxml_file: str, ly_file: str, name: str) -> None:
    """musicxml2ly, then our layout block: grob classes for the SVG and a style per file."""
    musicxml_file = _without_other_dynamics(musicxml_file, ly_file + ".musicxml", name)
    subprocess.run(  # noqa: S603
        [  # noqa: S607
            "musicxml2ly",
            "--npl",
            "--nsd",
            "--nrp",
            "--loglevel=ERROR",
            "-o",
            ly_file,
            musicxml_file,
        ],
        check=True,
        capture_output=True,
        timeout=300,
    )
    rng = _random_for(name + VARIANT)
    tags = "\n".join(
        f'      \\override {grob}.output-attributes = #\'((class . "{css}"))'
        for grob, css in _TAGS.items()
    )
    # An 8va bracket sits above its staff and an 8vb below, the class says which, as a
    # bracket between two staffs is otherwise as close to the wrong one.
    tags += """
      \\override OttavaBracket.output-attributes =
        #(lambda (grob)
           (list (cons 'class
                       (if (eqv? (ly:grob-property grob 'direction) DOWN)
                           "hOttavaDown" "hOttavaUp"))))"""
    layout = f"""\\layout {{
    \\context {{ \\Score
{tags}
    }}
    \\context {{ \\Staff
      {_ottava_style(rng)}
    }}
  }}"""
    with open(ly_file) as f:
        ly = f.read()
    if ly.count("\\layout {}") != 1:
        raise ValueError("unexpected musicxml2ly output, no single empty \\layout block")
    ly = ly.replace("\\layout {}", layout)
    ly = (
        f"#(set-global-staff-size {rng.choice(_STAFF_SIZES)})\n"
        + '\\paper { tagline = ##f print-page-number = ##f #(set-paper-size "a4") }\n'
        + ly
    )
    with open(ly_file, "w") as f:
        f.write(ly)


def _run_lilypond(args: list[str], ly_file: str, out_base: str) -> None:
    subprocess.run(  # noqa: S603
        ["lilypond", "--loglevel=ERROR", *args, "-o", out_base, ly_file],  # noqa: S607
        check=True,
        capture_output=True,
        timeout=900,
    )


def _rasterize(svg_file: str, png_file: str) -> None:
    subprocess.run(  # noqa: S603
        [  # noqa: S607
            "rsvg-convert",
            "-w",
            str(RASTER_WIDTH),
            "-b",
            "white",
            "-o",
            png_file,
            svg_file,
        ],
        check=True,
        capture_output=True,
        timeout=300,
    )


def _lines_are_where_expected(
    image: "cv2.typing.MatLike", staffs: list["LilyStaff"], scale: float
) -> bool:
    """A last check that the picture is the page the geometry describes."""
    for staff in staffs:
        x0 = int(staff.x * scale) + 5
        x1 = int((staff.x + staff.width) * scale) - 5
        for line in range(5):
            y = round((staff.line_top + line * (staff.line_bottom - staff.line_top) / 4) * scale)
            band = image[max(0, y - 2) : y + 3, x0:x1]
            if band.size == 0 or float((band.min(axis=0) < 128).mean()) < 0.6:  # noqa: PLR2004
                return False
    return True


def _pages(out_base: str, extension: str) -> list[str]:
    """LilyPond names a single page base.ext and several base-1.ext or base-page1.ext."""
    single = f"{out_base}.{extension}"
    if os.path.exists(single):
        return [single]
    folder, stem = os.path.split(out_base)
    numbered = []
    for entry in os.listdir(folder):
        match = re.fullmatch(re.escape(stem) + r"-(?:page)?(\d+)\." + extension, entry)
        if match:
            numbered.append((int(match.group(1)), os.path.join(folder, entry)))
    return [path for _number, path in sorted(numbered)]


Box = tuple[float, float, float, float]  # x_min, y_min, x_max, y_max


def _boxes(group: ET.Element) -> list[Box]:
    """Rough boxes of everything LilyPond drew for one grob, in SVG user units."""
    result: list[Box] = []
    for inner in group.iter(f"{_SVG}g"):
        match = _TRANSLATE.search(inner.get("transform", ""))
        if not match:
            continue
        tx, ty = float(match.group(1)), float(match.group(2))
        for child in inner:
            tag = child.tag.removeprefix(_SVG)
            if tag == "line":
                xs = [tx + float(child.get("x1", "0")), tx + float(child.get("x2", "0"))]
                ys = [ty + float(child.get("y1", "0")), ty + float(child.get("y2", "0"))]
                result.append((min(xs), min(ys), max(xs), max(ys)))
            elif tag == "rect":
                x, y = tx + float(child.get("x", "0")), ty + float(child.get("y", "0"))
                result.append(
                    (x, y, x + float(child.get("width", "0")), y + float(child.get("height", "0")))
                )
            elif tag == "text":
                size = float(child.get("font-size", "2"))
                letters = sum(len(span.text or "") for span in child.iter(f"{_SVG}tspan"))
                result.append((tx, ty - size, tx + 0.55 * size * max(1, letters), ty))
            else:  # a glyph path, drawn around its reference point
                result.append((tx, ty, tx, ty))
    return result


@dataclass
class LilyStaff:
    """One staff of one system, in SVG user units."""

    x: float
    width: float
    line_top: float
    line_bottom: float
    top: float = 0.0
    bottom: float = 0.0
    bar_xs: list[float] = field(default_factory=list)
    notes: int = 0
    rests: int = 0
    ottavas: int = 0

    def __post_init__(self) -> None:
        self.top, self.bottom = self.line_top, self.line_bottom
        self.staff_space = (self.line_bottom - self.line_top) / 4
        self.bar_xs = [self.x, self.x + self.width]

    @property
    def number_of_measures(self) -> int:
        return len(self.bar_xs) - 1

    def distance(self, y_min: float, y_max: float) -> float:
        if y_max < self.line_top:
            return self.line_top - y_max
        if y_min > self.line_bottom:
            return y_min - self.line_bottom
        return 0.0

    def add_bar_line(self, x: float, heavy: bool) -> None:
        # A repeat sign after the clef and key at the start of a line isn't a measure
        if heavy and x < self.x + 0.15 * self.width:
            return
        if all(abs(x - other) > 2.5 * self.staff_space for other in self.bar_xs):
            self.bar_xs.append(x)

    def extend(self, box: Box) -> None:
        self.top = min(self.top, box[1])
        self.bottom = max(self.bottom, box[3])

    def merge(self, other: "LilyStaff") -> "LilyStaff":
        if self.number_of_measures != other.number_of_measures:
            raise ValueError("Can't merge staffs with a different number of measures")
        left = min(self.x, other.x)
        right = max(self.x + self.width, other.x + other.width)
        merged = LilyStaff(
            left,
            right - left,
            min(self.line_top, other.line_top),
            max(self.line_bottom, other.line_bottom),
        )
        merged.staff_space = self.staff_space
        merged.top, merged.bottom = min(self.top, other.top), max(self.bottom, other.bottom)
        merged.bar_xs = sorted(self.bar_xs)
        merged.notes = self.notes + other.notes
        merged.rests = self.rests + other.rests
        merged.ottavas = self.ottavas + other.ottavas
        return merged


def parse_page(svg_file: str) -> tuple[float, list[LilyStaff]]:
    """The width of the page in user units and its staffs from top to bottom."""
    root = ET.parse(svg_file).getroot()  # noqa: S314
    page_width = float(root.get("viewBox", "0 0 1 1").split()[2])
    groups: dict[str, list[list[Box]]] = {
        css: [] for css in {*_TAGS.values(), "hOttavaUp", "hOttavaDown"}
    }
    for group in root.iter(f"{_SVG}g"):
        css = group.get("class", "")
        if css in groups:
            boxes = _boxes(group)
            if boxes:
                groups[css].append(boxes)

    staffs: list[LilyStaff] = []
    for lines in groups["hStaff"]:
        ys = sorted({round(box[1], 3) for box in lines})
        if len(ys) != 5:  # noqa: PLR2004
            continue
        x_min, x_max = min(box[0] for box in lines), max(box[2] for box in lines)
        staffs.append(LilyStaff(x_min, x_max - x_min, ys[0], ys[-1]))
    staffs.sort(key=lambda staff: staff.line_top)
    if not staffs:
        return page_width, []

    def nearest(box: Box) -> LilyStaff | None:
        best = min(staffs, key=lambda staff: staff.distance(box[1], box[3]))
        limit = MAX_DISTANCE_IN_STAFF_SPACES * best.staff_space
        return best if best.distance(box[1], box[3]) <= limit else None

    for bar in groups["hBar"]:
        rects = [box for box in bar if box[3] - box[1] > 0]
        if not rects:
            continue
        x = min(box[0] for box in rects)
        heavy = any(box[2] - box[0] >= 0.3 for box in rects)  # noqa: PLR2004
        y_min, y_max = min(box[1] for box in rects), max(box[3] for box in rects)
        for staff in staffs:
            if y_min <= staff.line_bottom and y_max >= staff.line_top:
                staff.add_bar_line(x, heavy)

    def owner_of_bracket(box: Box, above_staff: bool) -> LilyStaff | None:
        middle = (box[1] + box[3]) / 2
        if above_staff:
            candidates = [staff for staff in staffs if staff.line_top > middle]
            return candidates[0] if candidates else None
        candidates = [staff for staff in staffs if staff.line_bottom < middle]
        return candidates[-1] if candidates else None

    for css, counter in (
        ("hNote", "notes"),
        ("hRest", "rests"),
        ("hOttavaUp", "ottavas"),
        ("hOttavaDown", "ottavas"),
    ):
        for boxes in groups[css]:
            whole = (
                min(b[0] for b in boxes),
                min(b[1] for b in boxes),
                max(b[2] for b in boxes),
                max(b[3] for b in boxes),
            )
            if css.startswith("hOttava"):
                staff = owner_of_bracket(whole, above_staff=css == "hOttavaUp")
            else:
                staff = nearest(whole)
            if staff is None:
                continue
            setattr(staff, counter, getattr(staff, counter) + 1)
            pad = staff.staff_space * (1.0 if css.startswith("hOttava") else 0.6)
            staff.extend((whole[0], whole[1] - pad, whole[2], whole[3] + pad))
    for css in ("hStem", "hDyn"):
        for boxes in groups[css]:
            for box in boxes:
                staff = nearest(box)
                if staff is not None:
                    pad = staff.staff_space * (1.2 if css == "hDyn" else 0.0)
                    staff.extend((box[0], box[1] - pad, box[2], box[3] + pad))
    for staff in staffs:
        staff.bar_xs.sort()
    return page_width, staffs


def _token_counts(symbols: list[EncodedSymbol]) -> tuple[int, int, int]:
    notes = sum(1 for s in symbols if s.rhythm.startswith("note"))
    rests = sum(1 for s in symbols if s.rhythm.startswith("rest"))
    ottavas = sum(
        1 for s in symbols if s.rhythm.startswith("octaveShift") and s.rhythm != "octaveShiftStop"
    )
    return notes, rests, ottavas


def _group_systems(staffs: list[LilyStaff], voices: list) -> list[LilyStaff] | None:
    """Merges the two staffs of every grand staff, None if the page doesn't fit the parts."""
    per_system = sum(get_svg_voice_count(voice) for voice in voices)
    if len(staffs) % per_system != 0:
        return None
    result: list[LilyStaff] = []
    for start in range(0, len(staffs), per_system):
        system = staffs[start : start + per_system]
        i = 0
        for voice in voices:
            if is_grandstaff(voice):
                result.append(system[i].merge(system[i + 1]))
                i += 2
            else:
                result.append(system[i])
                i += 1
    return result


def convert_file(file: Path) -> tuple[list[str], dict[str, int]]:  # noqa: PLR0915
    """Index lines of one MusicXML file and what happened to its staffs."""
    stats = {"kept": 0, "note_mismatch": 0, "ottava_mismatch": 0, "clef": 0, "kept_with_ottava": 0}
    name = file.stem
    try:
        voices = music_xml_file_to_tokens(str(file))
        if not voices:
            return [], {"failed_empty": 1}
        cutters = [MeasureCutter(voice) for voice in voices]
        with tempfile.TemporaryDirectory() as work:
            ly_file = os.path.join(work, "score.ly")
            write_ly(str(file), ly_file, name)
            _run_lilypond(["-dbackend=svg", "-dno-point-and-click"], ly_file, f"{work}/geo")
            svgs = _pages(f"{work}/geo", "svg")
            if not svgs:
                return [], {"failed_pages": 1}
            pngs = [svg[: -len("svg")] + "png" for svg in svgs]
            for svg, png in zip(svgs, pngs, strict=True):
                _rasterize(svg, png)

            pages: list[tuple[float, list[LilyStaff], str]] = []
            for svg, png in zip(svgs, pngs, strict=True):
                width, staffs = parse_page(svg)
                if not staffs:
                    continue
                picture = cv2.imread(png, cv2.IMREAD_GRAYSCALE)
                if not _lines_are_where_expected(picture, staffs, picture.shape[1] / width):
                    return [], {"failed_picture": 1}
                grouped = _group_systems(staffs, voices)
                if grouped is None:
                    return [], {"failed_staff_count": 1}
                pages.append((width, grouped, png))
            total = sum(staff.number_of_measures for _w, staffs, _p in pages for staff in staffs)
            if total != sum(len(voice) for voice in voices):
                return [], {"failed_measure_count": 1}

            lines: list[str] = []
            os.makedirs(flat_lily, exist_ok=True)
            for page_no, (width, staffs, png) in enumerate(pages, start=1):
                image = cv2.imread(png, cv2.IMREAD_GRAYSCALE)
                scale = image.shape[1] / width
                for staff_no, staff in enumerate(staffs, start=1):
                    cutter = cutters[(staff_no - 1) % len(cutters)]
                    symbols = cutter.extract_measures(staff.number_of_measures)
                    notes, _rests, ottavas = _token_counts(symbols)
                    if notes != staff.notes:
                        stats["note_mismatch"] += 1
                        continue
                    if ottavas != staff.ottavas:
                        stats["ottava_mismatch"] += 1
                        continue
                    if not contains_only_supported_clefs(symbols):
                        stats["clef"] += 1
                        continue
                    base = os.path.join(flat_lily, f"{name}{VARIANT}-{page_no}-{staff_no}")
                    margin = STORED_MARGIN_IN_STAFF_SPACES * staff.staff_space
                    x_min = max(0, int((staff.x - 2.5 * staff.staff_space) * scale))
                    x_max = int((staff.x + staff.width + 0.5 * staff.staff_space) * scale)
                    y_min = max(0, int((staff.top - margin) * scale))
                    y_max = int((staff.bottom + margin) * scale)
                    cv2.imwrite(base + ".png", image[y_min:y_max, x_min:x_max])
                    crop_info = {
                        "stems": [staff.top * scale - y_min, staff.bottom * scale - y_min],
                        "lines": [
                            staff.line_top * scale - y_min,
                            staff.line_bottom * scale - y_min,
                        ],
                        "staff_space": staff.staff_space * scale,
                    }
                    write_text_to_file(json.dumps(crop_info), crop_info_path(base + ".png"))
                    write_text_to_file(
                        token_lines_to_str(strip_naturals(symbols)), base + ".tokens"
                    )
                    lines.append(
                        str(Path(base + ".png").relative_to(git_root))
                        + ","
                        + str(Path(base + ".tokens").relative_to(git_root))
                        + "\n"
                    )
                    stats["kept"] += 1
                    stats["kept_with_ottava"] += ottavas > 0
            return lines, stats
    except subprocess.TimeoutExpired:
        return [], {"failed_timeout": 1}
    except subprocess.CalledProcessError as e:
        tool = "musicxml2ly" if "musicxml2ly" in str(e.cmd[0]) else "lilypond"
        return [], {f"failed_{tool}": 1}
    except UnsupportedTimeSignatureError as e:
        eprint("Skipping", file, e)
        return [], {"failed_unsupported_time_signature": 1}
    except Exception as e:
        eprint("Error while processing", file, repr(e)[:200])
        return [], {"failed_other": 1}


def select_files(files: list[Path], share_without_octave_marks: float) -> list[Path]:
    """Every file with an octave shift, and a fixed share of the others."""
    selected = []
    for file in files:
        with open(file, errors="ignore") as f:
            has_shift = "<octave-shift" in f.read()
        if has_shift or _random_for("pick" + file.stem).random() < share_without_octave_marks:
            selected.append(file)
    return selected


def main() -> None:
    args = sys.argv[1:]
    share = 0.0
    if "--all" in args:
        share = 1.0
        args.remove("--all")
    if "--share" in args:
        i = args.index("--share")
        share = float(args[i + 1])
        del args[i : i + 2]
    files: list[Path] = []
    for arg in args:
        path = Path(arg)
        files.extend(sorted(path.rglob("*.musicxml")) if path.is_dir() else [path])
    files = select_files(files, share)
    eprint("Rendering", len(files), "files with LilyPond")
    totals: dict[str, int] = {}
    os.makedirs(lily_root, exist_ok=True)
    workers = int(os.environ.get("LILY_WORKERS", "8"))
    with open(lily_train_index, "a") as index, multiprocessing.Pool(workers) as pool:
        for done, (lines, stats) in enumerate(pool.imap_unordered(convert_file, files), start=1):
            index.writelines(lines)
            index.flush()
            for key, value in stats.items():
                totals[key] = totals.get(key, 0) + value
            if done % 20 == 0 or done == len(files):
                eprint(f"{done}/{len(files)}", json.dumps(totals, sort_keys=True))
    print(json.dumps(totals, sort_keys=True))  # noqa: T201


if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")
    main()
