"""Transcribe every staff system with rokot-omr-2b and bank the raw ABC.

rokot reads one system at a time, so this crops systems using the staff boxes
homr already wrote, then runs each through llama.cpp. Roughly 50 s per system, so
pieces are processed smallest-first and every result is written as it arrives --
the run can be stopped and resumed without losing work.

Conversion of the ABC into MusicXML happens separately: the inference is the
expensive half and worth banking on its own.
"""

import re
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image

ROOT = Path("/Users/yiduoke/Documents/homr")
WORK = ROOT / "run/work"
MODEL = ROOT / "run/models/rokot/rokot-omr-2b-Q8_0.gguf"
MMPROJ = ROOT / "run/models/rokot/mmproj-rokot-omr-2b-f16.gguf"
PROMPT = "Transcribe this staff to rokot-ABC."
TARGET_WIDTH = 1400  # the model card's recommended system width


def systems_for(page_png: Path) -> list[tuple[int, int, int, int]]:
    txt = page_png.with_suffix(".txt")
    if not txt.exists():
        return []
    img = Image.open(page_png)
    width, height = img.size
    boxes = []
    for line in txt.read_text().splitlines():
        if not line.strip():
            continue
        _cls, cx, cy, w, h = (float(v) for v in line.split())
        cx, cy, w, h = cx * width, cy * height, w * width, h * height
        pad = h * 0.55
        boxes.append(
            (
                max(int(cx - w / 2 - w * 0.02), 0),
                max(int(cy - h / 2 - pad), 0),
                min(int(cx + w / 2 + w * 0.02), width),
                min(int(cy + h / 2 + pad), height),
            )
        )
    boxes.sort(key=lambda b: b[1])
    return boxes


def transcribe(image: Path) -> str:
    proc = subprocess.run(
        [
            "llama-mtmd-cli",
            "-m", str(MODEL),
            "--mmproj", str(MMPROJ),
            "--image", str(image),
            "-p", PROMPT,
            "-n", "1600",
            "--temp", "0",
            "-ngl", "99",
            "--no-warmup",
        ],
        capture_output=True,
        text=True,
        timeout=900,
    )
    text = proc.stdout
    start = text.find("%%rokot-abc")
    if start == -1:
        start = text.find("X:1")
    return text[start:].strip() if start != -1 else ""


def main() -> None:
    pieces = sorted(
        (p for p in WORK.iterdir() if (p / "pages").is_dir()),
        key=lambda p: sum(
            len(t.read_text().splitlines()) for t in (p / "pages").glob("page-*.txt")
        ),
    )
    for piece in pieces:
        out_dir = piece / "rokot"
        out_dir.mkdir(exist_ok=True)
        pages = sorted(
            (p for p in (piece / "pages").glob("page-*.png") if "_teaser" not in p.name),
            key=lambda p: int(re.search(r"page-(\d+)", p.name).group(1)),
        )
        index = 0
        for page in pages:
            img = Image.open(page).convert("RGB")
            for box in systems_for(page):
                index += 1
                dst = out_dir / f"sys-{index:04d}.abc"
                if dst.exists():
                    continue
                crop = img.crop(box)
                if crop.width < 50 or crop.height < 20:
                    dst.write_text("")
                    continue
                scale = TARGET_WIDTH / crop.width
                crop = crop.resize((TARGET_WIDTH, max(int(crop.height * scale), 1)), Image.LANCZOS)
                tmp = out_dir / "_current.png"
                crop.save(tmp)
                started = time.time()
                try:
                    abc = transcribe(tmp)
                except subprocess.TimeoutExpired:
                    abc = ""
                dst.write_text(abc)
                print(
                    f"{piece.name} sys {index:4d}  {time.time() - started:5.1f}s  "
                    f"{len(abc):5d} chars",
                    flush=True,
                )
        print(f"=== {piece.name} done: {index} systems ===", flush=True)


main()
