"""Beethoven Op.31/2 (Schirmer F17): every PDF page is a two-page spread and one half is upside down. Split each spread in the middle and
keep the orientation in which homr finds more staffs and noteheads. Writes work/pages/beethoven-op31-2-schirmer-split/p-NN.png (book order) + map.json."""
import os, sys, json, cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from homr.main import ProcessingConfig, detect_single_staffs
BASE = "/Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso/work"
SRC = f"{BASE}/pages/beethoven-op31-2-schirmer"; DST = f"{BASE}/pages/beethoven-op31-2-schirmer-split"; os.makedirs(DST, exist_ok=True)
config = ProcessingConfig(enable_debug=False, enable_cache=False, write_staff_positions=False, read_staff_positions=False, selected_staff=-1,
                          transformer_use_gpu=False, segnet_use_gpu=True, coreml_encoder=False, title_detection=False)
def score(img, tmp):
    """clef/key mass at the left minus at the right end of the staffs (upright music: clefs on the left): >0 means upright"""
    cv2.imwrite(tmp, img)
    try:
        s = detect_single_staffs(tmp, config)
        ck = s.predictions.clefs_keys.astype(float); H, Wd = ck.shape
        x0 = min(st.min_x for st in s.staffs); x1 = max(st.max_x for st in s.staffs); w = x1 - x0
        left = ck[:, int(x0):int(x0 + 0.12 * w)].sum(); right = ck[:, int(x1 - 0.12 * w):int(x1)].sum()
        return float(left - right), len(s.staffs)
    except Exception: return 0.0, 0
mp = []; k = 0
for n in range(int(sys.argv[1]), int(sys.argv[2]) + 1):
    im = cv2.imread(f"{SRC}/p-{n:02d}.png", 0); h, w = im.shape
    for half, (x0, x1) in enumerate(((0, w // 2), (w // 2, w))):
        part = im[:, x0:x1]; rot = cv2.rotate(part, cv2.ROTATE_180)
        a = score(part, f"{BASE}/_t.png"); b = (-a[0], a[1])
        use_rot = a[0] < 0; k += 1
        cv2.imwrite(f"{DST}/p-{k:02d}.png", rot if use_rot else part)
        mp.append(dict(page=k, pdf_page=n, half=half, rotated=use_rot, upright_score=a, rotated_score=b)); print(mp[-1], flush=True)
json.dump(mp, open(f"{DST}/map.json", "w"))
