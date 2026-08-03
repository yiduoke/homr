import re
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import NamedTuple

from rapidocr import RapidOCR

from homr.debug import Debug
from homr.model import Staff

# Globals
_reader: RapidOCR | None = None
_reader_lock = threading.Lock()
_executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=1)

# Words which mark the text above a staff as a tempo indication rather than a title.
# Only used to tell the two apart, no beats per minute are derived from them: the
# conventional BPM for a given term differs between sources, so guessing one here
# would put a number into the MusicXML which isn't in the score.
TEMPO_TERMS = frozenset(
    {
        # Italian
        "grave", "largo", "larghissimo", "larghetto", "largamente", "lento",
        "adagio", "adagietto", "andante", "andantino", "moderato", "allegretto",
        "allegro", "allegrissimo", "vivace", "vivacissimo", "presto",
        "prestissimo", "maestoso", "animato", "sostenuto", "tempo",
        # German
        "langsam", "schnell", "lebhaft", "bewegt", "breit", "massig",
        # French
        "lent", "vif", "large", "modere", "anime",
        # English
        "slow", "fast", "moderate",
    }
)


class TitleAndTempo(NamedTuple):
    """Text found above the first staff, split into a title and a tempo marking."""

    title: str
    tempo: str


def cleanup_text(text: str) -> str:
    """
    Remove all special characters from the text. Merge multiple whitespaces into a single space.
    """
    return re.sub(r"[^a-zA-Z0-9]+", " ", text).strip()


def _initialize_reader() -> None:
    """
    Thread-safe initialization of the OCR reader.
    """
    global _reader  # noqa: PLW0603
    if _reader is None:
        with _reader_lock:
            if _reader is None:  # double-checked locking
                _reader = RapidOCR()


def is_tempo_marking(text: str) -> bool:
    """
    Filter out tempo markings, e.g. 60 BPM
    """
    min_letters = 4
    if len(text) < min_letters:
        return True
    return sum(1 for c in text if "a" <= c.lower() <= "z") < min_letters


def is_tempo_text(text: str) -> bool:
    """
    True if the text reads as a tempo indication, e.g. "Allegro di molto e con brio".

    A piece actually named after a tempo ("Adagio") is misread as a tempo marking
    here. That is preferred over the previous behaviour, where every tempo was
    misread as the title.
    """
    words = cleanup_text(text).lower().split()
    return any(word in TEMPO_TERMS for word in words)


def _detect_title_task(debug: Debug, top_staff: Staff) -> TitleAndTempo:
    _initialize_reader()

    if _reader is None:
        raise ValueError("reader is not initialized")
    image = debug.original_image
    height: int = int(15 * top_staff.average_unit_size)
    y: int = max(int(top_staff.min_y) - height, 0)
    x: int = max(int(top_staff.min_x) - 50, 0)
    width: int = int(top_staff.max_x - top_staff.min_x) + 100
    width = min(width, image.shape[1] - x)
    height = min(height, int(top_staff.min_y) - y)
    above_staff = image[y : y + height, x : x + width]

    ocr_input: str = debug.write_model_input_image("_tesseract_input.png", above_staff)
    ocr_results = _reader(ocr_input)

    if ocr_results.txts is None:
        return TitleAndTempo("", "")

    results = [
        (box, txt, score)
        for box, txt, score in zip(
            ocr_results.boxes, ocr_results.txts, ocr_results.scores, strict=True
        )
    ]

    filtered_results = [r for r in results if not is_tempo_marking(r[1])]

    tempo_results = [r for r in filtered_results if is_tempo_text(r[1])]
    filtered_results = [r for r in filtered_results if not is_tempo_text(r[1])]

    tempo = cleanup_text(tempo_results[0][1]) if tempo_results else ""

    if not filtered_results:
        return TitleAndTempo("", tempo)

    def bbox_height(bbox: list[list[float]]) -> float:
        ys = [p[1] for p in bbox]
        return max(ys) - min(ys)

    # Take max average character height = bbox_height / number of chars
    def font_size_score(result: tuple[list[list[float]], str, float]) -> float:
        bbox, text, _ = result
        if not text:
            return 0
        return bbox_height(bbox) / len(text)

    largest_text = max(filtered_results, key=font_size_score)[1]
    return TitleAndTempo(cleanup_text(largest_text), tempo)


def download_ocr_weights() -> None:
    """
    Pre-download and initialize OCR reader weights before detection runs.
    """
    _initialize_reader()


def detect_title(debug: Debug, top_staff: Staff) -> Future[TitleAndTempo]:
    """
    Runs the title detection in a separate thread and returns a Future.
    """
    return _executor.submit(_detect_title_task, debug, top_staff)
