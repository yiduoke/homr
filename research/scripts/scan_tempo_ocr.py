"""OCR a whole page and report every text run that reads as a tempo marking."""
import sys
from rapidocr import RapidOCR
from homr.title_detection import cleanup_text, is_tempo_text

reader = RapidOCR()
for path in sys.argv[1:]:
    res = reader(path)
    if res.txts is None:
        print(path, "-> no text"); continue
    hits = []
    for box, txt, score in zip(res.boxes, res.txts, res.scores):
        if is_tempo_text(txt):
            xs = [p[0] for p in box]; ys = [p[1] for p in box]
            hits.append((min(ys), min(xs), cleanup_text(txt), round(float(score), 2)))
    print(f"\n{path.split('/')[-1]}: {len(hits)} tempo-like text runs")
    for y, x, txt, sc in sorted(hits):
        print(f"   y={y:7.0f} x={x:6.0f}  conf={sc}  {txt!r}")
