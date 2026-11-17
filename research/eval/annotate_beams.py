"""Draw a red brace over every beamed group of one staff band in a page crop and label it.

    python annotate_beams.py PAGE.png x0 y0 x1 y1 band_y0 band_y1 out.png "title" "label1,label2,..."

Beams are found as thick horizontal dark segments inside the band (staff lines are thin and are
removed by an opening with a 5-pixel-high kernel); segments that overlap in x form one group.
Labels are assigned to the groups from left to right.
"""
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

page, x0, y0, x1, y1, b0, b1, out, title, labels = sys.argv[1:11]
manual = sys.argv[11] if len(sys.argv) > 11 else ""
footer = sys.argv[12] if len(sys.argv) > 12 else ""
x0, y0, x1, y1, b0, b1 = map(int, (x0, y0, x1, y1, b0, b1))
labels = [s.strip() for s in labels.split(",")] if labels else []
img = cv2.imread(page, cv2.IMREAD_GRAYSCALE)[y0:y1, x0:x1]
band = img[b0 - y0 : b1 - y0]
dark = (band < 128).astype(np.uint8)
thick = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((4, 25), np.uint8))
n, lab, stats, _ = cv2.connectedComponentsWithStats(thick)
segs = sorted(
    (int(s[0]), int(s[0] + s[2])) for s in stats[1:] if s[2] >= 20 and s[3] <= 40 and s[2] < 0.6 * band.shape[1]
)
groups = []
for a, b in segs:
    if groups and a <= groups[-1][1] + 6:
        groups[-1][1] = max(groups[-1][1], b)
    else:
        groups.append([a, b])
if manual:
    groups = [[int(v) for v in g.split("-")] for g in manual.split(";")]
print("groups", len(groups), groups)
font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
head = 90
foot = 34 * (len(footer.split("|")) if footer else 0)
canvas = Image.new("RGB", (img.shape[1], img.shape[0] + head + foot), "white")
canvas.paste(Image.fromarray(img).convert("RGB"), (0, head))
d = ImageDraw.Draw(canvas)
red = (210, 20, 20)
for i, line in enumerate(title.split("|")):
    d.text((8, 6 + 26 * i), line.strip(), fill=red, font=font)
by = head + (b0 - y0) - 14
for i, (a, b) in enumerate(groups):
    d.line([(a, by + 10), (a, by), (b, by), (b, by + 10)], fill=red, width=3)
    mid = (a + b) // 2
    d.line([(mid, by), (mid, by - 6)], fill=red, width=3)
    if i < len(labels):
        w = d.textlength(labels[i], font=small)
        d.text((mid - w / 2, by - 30), labels[i], fill=red, font=small)
for i, line in enumerate(footer.split("|") if footer else []):
    d.text((8, head + img.shape[0] + 6 + 30 * i), line.strip(), fill=red, font=font)
canvas.save(out)
