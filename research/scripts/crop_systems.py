"""Cut each page into staff-system images for Zeus, framed the way OLiMPiC frames its own.

The first attempt cropped tightly at 150 DPI, giving ~1200x250 images. OLiMPiC's
samples are ~3402x921, aspect 3.9, and visibly bleed into the neighbouring systems
rather than being cut to the staff. Zeus rescales everything to height 192, so a
crop that starts three times smaller has three times less detail to lose -- at 150
DPI a 32nd-note beam is a couple of pixels.

Pages are therefore rendered at 400 DPI and padded vertically to OLiMPiC's aspect
ratio. Staff boxes come from homr, whose coordinates are normalised and so carry
over between resolutions.
"""

from pathlib import Path

from PIL import Image

OUT = Path("/Users/yiduoke/Documents/olimpic-icdar24/run/beethoven")
OUT.mkdir(parents=True, exist_ok=True)

TARGET_ASPECT = 3.91  # median of the OLiMPiC scanned samples
PLACEHOLDER_LMX = "clef:G2 measure"
PLACEHOLDER_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<score-partwise version="4.0"><part-list><score-part id="P1">'
    "<part-name>P</part-name></score-part></part-list>"
    '<part id="P1"><measure number="1"></measure></part></score-partwise>'
)

pages = sorted(
    Path("run/pages400").glob("page-[0-9].png"),
    key=lambda p: int(p.stem.split("-")[1]),
)

names = []
for page in pages:
    img = Image.open(page)
    width, height = img.size
    # Staff positions were written at 150 DPI but are stored normalised.
    boxes = []
    for line in Path(f"run/pages150/{page.stem}.txt").read_text().splitlines():
        if not line.strip():
            continue
        _cls, cx, cy, w, h = (float(v) for v in line.split())
        boxes.append((cx * width, cy * height, w * width, h * height))
    boxes.sort(key=lambda b: b[1])

    for i, (cx, cy, w, h) in enumerate(boxes):
        pad_x = w * 0.03
        left = max(int(cx - w / 2 - pad_x), 0)
        right = min(int(cx + w / 2 + pad_x), width)
        # Grow vertically until the crop matches OLiMPiC's shape. Overlapping the
        # neighbouring system is expected -- their samples do the same.
        want_h = (right - left) / TARGET_ASPECT
        top = max(int(cy - want_h / 2), 0)
        bottom = min(int(cy + want_h / 2), height)

        name = f"{page.stem}-sys{i}"
        img.crop((left, top, right, bottom)).save(OUT / f"{name}.png")
        (OUT / f"{name}.lmx").write_text(PLACEHOLDER_LMX)
        (OUT / f"{name}.musicxml").write_text(PLACEHOLDER_XML)
        names.append(name)

(OUT / "samples.test.txt").write_text("\n".join(names) + "\n")
sizes = [Image.open(OUT / f"{n}.png").size for n in names]
print(f"wrote {len(names)} crops")
print(f"median size {sorted(s[0] for s in sizes)[len(sizes)//2]}x{sorted(s[1] for s in sizes)[len(sizes)//2]}")
